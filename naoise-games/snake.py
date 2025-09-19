import pygame
import numpy as np

pygame.init()
screen = pygame.display.set_mode((600, 600))

class SnakeBody():
    def __init__(self, pos=(0, 0)):
        self.rect = pygame.Rect(pos[0], pos[1], 10, 10)

class SnakeHead():
    def __init__(self, pos=(300, 300)):
        self.pos = pos
        self.rect = pygame.Rect(pos[0], pos[1], 10, 10)

class Snake():
    def __init__(self, length:int):
        self.head = SnakeHead()
        self.body = [SnakeBody((self.head.pos[0], self.head.pos[1] + 10*(i+1))) for i in range(length)]

    def advance(self, direction:tuple):
        x, y = self.head.pos
        dx, dy = direction
        new_pos = (x + dx*10, y + dy*10)

        self.body = [SnakeBody(self.head.pos)] + self.body[:-1]

        self.head.pos = new_pos
        self.head.rect.topleft = new_pos

    def draw(self):
        screen.fill((0, 255, 100), self.head.rect)
        for part in self.body:
            screen.fill((0, 255, 0), part.rect)

class Fruit():
    def __init__(self, colour=(255, 0, 0)):
        self.pos = np.array([0, 0])
        self.rect = pygame.Rect(self.pos[0], self.pos[1], 10, 10)
        self.colour = colour
    def draw(self):
        screen.fill(self.colour, self.rect)
    def place(self):
        self.pos = np.array((np.random.randint(0, 600), np.random.randint(0, 600)))
        self.rect.topleft = (self.pos[0]//10*10, self.pos[1]//10*10)

class PowerUpFruit(Fruit(colour=(0, 0, 255))):
    def draw(self):
        screen.fill(self.colour, self.rect)
    
    def on_eat(self):
        return None

class DoubleFruit(PowerUpFruit):
    def on_eat(self):
        return 2
snake = Snake(4)
fruit = Fruit()
fruit.place()
running = True
clock = pygame.time.Clock()
direction = (0, -1)
time_between_inputs = 0

while running:
    time_between_inputs = max(0, time_between_inputs-1)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d and direction!=(-1,0):
                if time_between_inputs == 0:
                    direction = (1, 0)
                    time_between_inputs = 1
            elif event.key == pygame.K_q and direction!=(1,0):
                if time_between_inputs == 0:
                    direction = (-1, 0)
                    time_between_inputs = 1
            elif event.key == pygame.K_z and direction!=(0,1):
                if time_between_inputs == 0:
                    direction = (0, -1)
                    time_between_inputs = 1
            elif event.key == pygame.K_s and direction!=(0,-1):
                if time_between_inputs == 0:
                    direction = (0, 1)
                    time_between_inputs = 1
    
    screen.fill((0, 0, 0))
    snake.advance(direction)
    if (np.array(snake.head.pos) >= 600).any() or (np.array(snake.head.pos) < 0).any() or any(part.rect.colliderect(snake.head.rect) for part in snake.body):
        running = False
    snake.draw()
    fruit.draw()
    if fruit.rect.colliderect(snake.head.rect):
        if isinstance(fruit, PowerUpFruit):
            for _ in range(fruit.on_eat()):
                snake.body.append(SnakeBody(snake.body[-1].rect.topleft))
        else:
            snake.body.append(SnakeBody(snake.body[-1].rect.topleft))
        fruit.place()
    pygame.display.flip()
    clock.tick(7+len(snake.body))