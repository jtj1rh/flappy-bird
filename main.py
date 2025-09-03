import sys
import random
import pygame

from pygame.sprite import Sprite, Group

class Settings:
    def __init__(self):
        self.width = 864 # use 1000 to see hidden mechanics
        self.height = 936
        
        self.fps = 60

        # Background variables
        self.ground_scroll = 0
        self.scroll_speed = 4

        # Bird variables
        self.flying = False
        self.game_over = False
 
        # Pipe variables
        self.pipe_gap = 150
        self.pipe_frequency = 1500 # milliseconds

        self.last_pipe = pygame.time.get_ticks() - self.pipe_frequency

        # Score variables
        self.pass_pipe = False # score tracking
        self.score = 0

        self.font = pygame.font.SysFont('Bauhaus 93', 60)


class Bird(Sprite):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings

        self.images = []

        self.index = 0
        self.counter = 0

        for num in range(1, 4):
            img = pygame.image.load(f'img/bird{num}.png')
            self.images.append(img)

        self.image = self.images[self.index]

        self.rect = self.image.get_rect()
        self.rect.center = [100, self.settings.height // 2]

        self.vel = 0

        self.clicked = False

    def update(self):
        if self.settings.flying == True:
            # Add gravity
            self.vel += 0.5

            if self.vel > 8:
                self.vel = 8

            if self.rect.bottom < 768:
                self.rect.y += int(self.vel)

        if not self.settings.game_over:
            # Add jump function
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                self.vel = -10
            elif pygame.mouse.get_pressed()[0] == 0:
                self.clicked = False

            # Handle the animation
            self.counter += 1
            flap_cooldown = 5

            if self.counter > flap_cooldown:
                self.counter = 0
                self.index += 1

                if self.index >= len(self.images):
                    self.index = 0

            self.image = self.images[self.index]

            # Add rotation (tip: no accumulation of rotation)
            self.image = pygame.transform.rotate(self.images[self.index], self.vel * -2)
        
        else:
            self.image = pygame.transform.rotate(self.images[self.index], -90)


class Pipe(Sprite):
    def __init__(self, settings, position, pipe_height):
        super().__init__()
        self.settings = settings
        self.image = pygame.image.load('img/pipe.png')
        self.rect = self.image.get_rect()

        self.pipe_height = pipe_height

        # position 1 is from the top, -1 is from the bottom
        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = [self.settings.width,
                                    (self.settings.height // 2 - self.settings.pipe_gap // 2) + 
                                     self.pipe_height]
        elif position == -1:
            self.rect.topleft = [self.settings.width,
                                 (self.settings.height // 2 + self.settings.pipe_gap // 2) +
                                 self.pipe_height]

    def update(self):
        self.rect.x -= self.settings.scroll_speed

        if self.rect.right < 0:
            self.kill()


class Button():
    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = self.screen.get_rect()

        self.image = pygame.image.load('img/restart.png')
        self.rect = self.image.get_rect()
        self.rect.center = self.screen_rect.center
        
    def draw(self):
        action = False

        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1:
                action = True

        self.screen.blit(self.image, self.rect)

        return action


# Function to draw text(score) to screen
def draw_text(settings, screen, text):
    img = settings.font.render(text, True, (255, 255, 255))
    screen.blit(img, (settings.width // 2, 20))


# Function to reset the game
def reset_game(settings, flappy, pipe_group):
    # Remove pipes created from group
    pipe_group.empty()

    flappy.rect.center = [100, settings.height // 2]
    
    settings.score = 0


def main():
    # Initialize pygame and settings
    pygame.init()

    settings = Settings()

    # Create screen and clock object
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((settings.width, settings.height))
    pygame.display.set_caption('Flappy Bird')

    # Load background images
    bg = pygame.image.load('img/bg.png')
    ground_img = pygame.image.load('img/ground.png')

    # Create an instance of the button
    restart_button = Button(screen)

    # Make a bird and pipe group
    bird_group = Group()
    pipe_group = Group()

    # Create an instance of the bird
    flappy = Bird(settings)

    bird_group.add(flappy)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN\
                and settings.flying == False\
                and settings.game_over == False:
                    settings.flying = True

        bird_group.update()

        if not settings.game_over and settings.flying == True:
            # Generate new pipes
            time_now = pygame.time.get_ticks()
            if time_now - settings.last_pipe > settings.pipe_frequency:
                pipe_height = random.randint(-100, 100)

                top_pipe = Pipe(settings, 1, pipe_height)
                btm_pipe = Pipe(settings, -1, pipe_height)

                pipe_group.add(top_pipe)
                pipe_group.add(btm_pipe)

                settings.last_pipe = time_now

            pipe_group.update()

            # Add ground scroll effect
            settings.ground_scroll -= settings.scroll_speed

            if abs(settings.ground_scroll) > 35:
                settings.ground_scroll = 0

        # Check score
        if len(pipe_group) > 0:
            bird = bird_group.sprites()[0]
            pipe = pipe_group.sprites()[0]

            if bird.rect.left > pipe.rect.left\
                and bird.rect.right < pipe.rect.right\
                and settings.pass_pipe == False:
                settings.pass_pipe = True
            
            if settings.pass_pipe == True:
                if bird.rect.left > pipe.rect.right:
                    settings.score += 1
                    settings.pass_pipe = False

        # Look for collisions between bird, pipe, and ceiling
        if pygame.sprite.groupcollide(bird_group, pipe_group, False, False)\
            or flappy.rect.top < 0:
                settings.game_over = True

        # Check if bird hits the ground
        if flappy.rect.bottom >= 768:
            settings.game_over = True
            settings.flying = False

        # Draw background
        screen.blit(bg, (0, 0))

        pipe_group.draw(screen)

        bird_group.draw(screen)

        # Draw ground
        screen.blit(ground_img, (settings.ground_scroll, 768))

        # Draw score
        draw_text(settings, screen, str(settings.score))

        if settings.game_over == True and settings.flying == False:
            if restart_button.draw():
                settings.game_over = False
                reset_game(settings, flappy, pipe_group)

        pygame.display.update()

        clock.tick(60)

if __name__ == '__main__':
    main()