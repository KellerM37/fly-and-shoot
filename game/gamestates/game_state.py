import pygame
import pygame_gui


from .base_state import BaseGamestate
from game.data import settings
from saves import *
from pygame_gui.elements import *

from game.entities.player import Player
from game.data.enemy_factory import EnemyFactory
from game.data.powerup_factory import PowerupFactory
from game.entities.powerups import BombExplosion
from game.data.aggression_manager import AggressionManager
from game.data.collision_manager import CollisionManager

class GameState(BaseGamestate):
    def __init__(self, ui_manager, state_manager):
        super().__init__("game_state", state_manager)
        
        self.ui_manager = ui_manager
        self.state_manager = state_manager

    
    def start(self):
        player_start = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT * 0.9)
        self.screen_bounds = pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        self.player = Player(player_start[0], player_start[1], self.ui_manager, self)
        self.screen = None

        # Game timers
        self.elapsed_time = 0
        self.game_length = 0
        self.spawn_timer = 0

        # Groups for various sprites to be updated and drawn
        self.updatable = pygame.sprite.Group()
        self.drawable = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()

        self.player.add(self.updatable, self.drawable)
        self.kill_count = 0
        self.explosion = None

        # Factory initializations
        self.powerup_factory = PowerupFactory(self.screen_bounds, self, self.player, self.powerups)
        self.enemy_factory = EnemyFactory(self.screen_bounds, self)
        self.aggression_manager = AggressionManager(self.elapsed_time, self.ui_manager, self.state_manager, self.enemy_factory, self.powerup_factory)
        self.collision_manager = CollisionManager(self, self.player, self.enemies, self.powerups, self.screen)

        self.build_ui()
        self.is_paused = False

    def end(self):
        self.ui_manager.clear_and_reset()
        self.updatable.empty()
        self.drawable.empty()
        self.powerups.empty()
        self.enemies.empty()
        self.enemy_bullets.empty()
        self.player_bullets.empty()
        self.player.kill()

    def update(self, dt):
        self.spawn_timer -= dt
        self.elapsed_time += dt
        
        self.updatable.update(dt, self.screen_bounds)
        self.ui_manager.update(dt)
        self.add_new_bullets()
        self.player.bullets.update(dt, self.screen_bounds)
        self.enemy_bullets.update(dt, self.screen_bounds)
        self.collision_manager.check_collisions()

        self.enemy_factory.update(dt, self.elapsed_time)
        self.powerup_factory.update(dt)
        self.aggression_manager.update(dt, self.elapsed_time)

        # Debug prints
        #print(self.player.ally)
        #print(f"Ally left: {self.player.ally['left']}, ally right: {self.player.ally['right']}")

    def add_new_bullets(self):
        for x in self.enemies:
            for bullet in x.bullets:
                self.updatable.add(bullet)
                self.drawable.add(bullet)
                self.enemy_bullets.add(bullet)
        for x in self.player.bullets:
            self.updatable.add(x)
            self.drawable.add(x)
            self.player_bullets.add(x)

    def detonate_bomb(self):
        self.explosion = BombExplosion(self.player.position, 10, self.enemies, self.player)
        self.explosion.add(self.updatable)
        self.player.update_bombs(self)
            
    def draw(self, screen):
        self.drawable.draw(screen)
        self.ui_manager.draw_ui(screen)
        if self.explosion:
            self.explosion.draw(screen)
            if self.explosion.is_finished:
                self.explosion = None

    def build_ui(self):
        
        self.background_image = pygame.image.load("ui/game_assets/sci_fi_bg1.jpg").convert_alpha()
        self.background_image = pygame.transform.scale(self.background_image, (settings.SCREEN_WIDTH, self.background_image.get_height()))
        self.background_speed = 0

        # Player HUD
        self.player_hud = UIPanel(pygame.Rect(0, 0, 400, 100),
                                  manager=self.ui_manager,
                                  object_id="#settings_bg",
                                  anchors={"left": "left",
                                           "top": "top"})
        self.player_health_bar = UIScreenSpaceHealthBar(pygame.Rect(0, 15, 370, 20),
                                                        manager=self.ui_manager,
                                                        sprite_to_monitor=self.player,
                                                        parent_element=self.player_hud,
                                                        anchors={"centerx": "centerx", "top": "top", "centerx_target": self.player_hud}
                                                        )
        self.kill_display = UILabel(pygame.Rect(15, 40, -1, -1),
                                    f"Kills: {self.kill_count}",
                                    manager=self.ui_manager,
                                    container=self.player_hud,
                                    anchors={"top": "top", "left": "left"})
        self.lives_display = UILabel(pygame.Rect(15, 63, -1, -1),
                                    f"Lives: ",
                                    manager=self.ui_manager,
                                    container=self.player_hud,
                                    anchors={"top": "top", "left": "left"})
        self.score_display = UILabel(pygame.Rect(200, 40, -1, -1),
                                    f"Score: {self.player.score}",
                                    manager=self.ui_manager,
                                    container=self.player_hud,
                                    anchors={"top": "top", "left": "left"})
        self.bomb_display = UILabel(pygame.Rect(200, 63, -1, -1),
                                    f"Bombs: ",
                                    manager=self.ui_manager,
                                    container=self.player_hud,
                                    anchors={"top": "top", "left": "left"})
        
        self.hud_elements = [self.player_hud, self.player_health_bar, self.kill_display]
        
        # Pause Menu
        self.pause_panel = UIPanel(pygame.Rect(0, 0, 350, 200),
                                   manager=self.ui_manager,
                                   object_id="#settings_bg",
                                   anchors={"centerx": "centerx", "centery": "centery"},
                                   visible=False)
        self.pause_title = UILabel(pygame.Rect(0, 10, -1, -1),
                                      "Paused",
                                      manager=self.ui_manager,
                                      container=self.pause_panel,
                                      object_id="#settings_titles",
                                      anchors={"top": "top", "centerx": "centerx"})
        self.resume_button = UIButton(pygame.Rect(0, -125, 250, 50),
                                        "Resume",
                                        manager=self.ui_manager,
                                        container=self.pause_panel,
                                        object_id="#settings_buttons",
                                        anchors={"bottom": "bottom", "centerx": "centerx"})
        self.quit_button = UIButton(pygame.Rect(0, -75, 250, 50),
                                        "Quit",
                                        manager=self.ui_manager,
                                        container=self.pause_panel,
                                        object_id="#settings_buttons",
                                        anchors={"bottom": "bottom", "centerx": "centerx"})
        self.player.update_hearts(self)
        self.player.update_bombs(self)
        
    def reset(self):
        self.kill_count = 0
    
    def run(self, screen, dt):
        self.screen = screen

        # Event loops
        for event in pygame.event.get():
            keys = pygame.key.get_pressed()
            self.ui_manager.process_events(event)

            # If window closed, quit game
            if event.type == pygame.QUIT:
                self.time_to_quit = True

            # Temporary escape key to return to main menu. Will be replaced with a pause menu
            if keys[pygame.K_ESCAPE]:
                self.is_paused = True if not self.is_paused else False
                if self.is_paused:
                    self.pause_panel.show()
                    for x in self.hud_elements:
                        x.hide()
                else:
                    self.pause_panel.hide()
                    for x in self.hud_elements:
                        x.show()
            if keys[pygame.K_F12]:
                settings.DEBUG_MODE = False
            if keys[pygame.K_F9]:
                return self.powerup_factory.spawn_powerup()

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.resume_button:
                    self.is_paused = False
                    self.pause_panel.hide()
                    for x in self.hud_elements:
                        x.show()
                if event.ui_element == self.quit_button:
                    self.new_state = "game_over"
                    self.transition = True

        if not self.is_paused:
            # Background scrolling
            self.background_speed += 25 * dt
            if self.background_speed >= self.background_image.get_height():
                self.background_speed = 0
            screen.blit(self.background_image, (0, self.background_speed - self.background_image.get_height()))
            screen.blit(self.background_image, (0, self.background_speed))

            self.update(dt)

            if settings.DEBUG_SHOW_PLAYER_HITBOX:
                pygame.draw.rect(screen, ("White"), self.playable_area, width=2) # Debugging
            self.draw(screen)
        
        else:
            overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
            overlay.set_alpha(20)
            overlay.fill((50, 50, 50))
            screen.blit(overlay, (0, 0))
            self.ui_manager.update(dt)
            self.ui_manager.draw_ui(screen)
