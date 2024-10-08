import pygame

from game.data import settings

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, bullet_area, rotation=0, damage=10):
        super().__init__()
        self.surface = pygame.Surface((10, 10))
        self.rotation = rotation
        self.surface.fill((255, 255, 255))
        self.position = pygame.Vector2(x, y)
        self.speed = 300
        self.velocity = pygame.Vector2(0, -300).rotate(rotation)
        self.bullet_area = bullet_area
        self.radius = 5
        self.damage = damage

        self.image, self.rect = self.get_sprite(pygame.image.load("ui/game_assets/missile00.png").convert_alpha())

    def update(self, dt, screen_bounds):
        self.rect.y += self.velocity.y * dt
        if (self.rect.right < 0 or self.rect.left > screen_bounds.width or
            self.rect.bottom < 0 or self.rect.top > screen_bounds.height):
            self.kill()

    def draw(self, screen):
        screen.blit(self.surface, self.rect)

    def get_sprite(self, bullet_image):
        rotated_image = pygame.transform.rotate(bullet_image, self.rotation)
        bullet_rect = rotated_image.get_rect(center=self.position)
        return rotated_image, bullet_rect 
    

class BossBullet(Bullet):
    def __init__(self, x, y, bullet_area, rotation, damage, speed, direction):
        super().__init__(x, y, bullet_area, rotation, damage)
        self.image, self.rect = self.get_sprite(pygame.image.load("ui/game_assets/missile00.png").convert_alpha())
        self.speed = speed
        self.damage = damage
        self.velocity = pygame.Vector2(direction).normalize() * speed

    def update(self, dt, screen_bounds):
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
        if (self.rect.right < 0 or self.rect.left > screen_bounds.width or
            self.rect.bottom < 0 or self.rect.top > screen_bounds.height):
            self.kill()