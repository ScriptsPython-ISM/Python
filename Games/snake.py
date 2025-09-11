import pygame
import random
import sys

pygame.init()

# ---------------------- CONFIG ----------------------
DIS_WIDTH, DIS_HEIGHT = 600, 400
SNAKE_BLOCK = 20
INITIAL_SPEED = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (213, 50, 80)
GREEN = (0, 200, 0)
BLUE = (50, 153, 213)
GREY = (150, 150, 150)
YELLOW = (255, 255, 0)

# Display
DIS = pygame.display.set_mode((DIS_WIDTH, DIS_HEIGHT))
pygame.display.set_caption("Snake Game Enhanced")
clock = pygame.time.Clock()

# Fonts
font_style = pygame.font.SysFont("bahnschrift", 25)
score_font = pygame.font.SysFont("comicsansms", 30)

# Load images
apple_image = pygame.image.load("apple.png")
background_image = pygame.image.load("background.png")
apple_image = pygame.transform.scale(apple_image, (SNAKE_BLOCK, SNAKE_BLOCK))
background_image = pygame.transform.scale(background_image, (DIS_WIDTH, DIS_HEIGHT))

# Game settings
volume = 100  # 0 to 100
key_layout = 'WASD'

# ---------------------- UTILITY FUNCTIONS ----------------------
def draw_text(msg, font, color, surface, x, y):
    textobj = font.render(msg, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)

def Your_score(score):
    value = score_font.render("Score: " + str(score), True, BLACK)
    DIS.blit(value, [10, 10])

def our_snake(snake_list):
    for segment in snake_list:
        pygame.draw.rect(DIS, GREEN, [segment[0], segment[1], SNAKE_BLOCK, SNAKE_BLOCK])

def draw_button(surface, color, x, y, w, h, text, text_color):
    pygame.draw.rect(surface, color, [x, y, w, h])
    draw_text(text, font_style, text_color, surface, x + w/2, y + h/2)
    return pygame.Rect(x, y, w, h)

def draw_volume_slider(surface, volume):
    # Slider background
    pygame.draw.rect(surface, GREY, [DIS_WIDTH-160, 20, 140, 10])
    # Slider knob
    knob_x = DIS_WIDTH-160 + int(140 * (volume/100))
    pygame.draw.rect(surface, YELLOW, [knob_x-5, 15, 10, 20])
    draw_text(f"Vol: {volume}%", font_style, BLACK, surface, DIS_WIDTH-80, 45)

# ---------------------- MENU ----------------------
def menu():
    global volume, key_layout
    menu_running = True
    dragging_volume = False

    while menu_running:
        DIS.fill(BLUE)
        draw_text("Snake Game", font_style, WHITE, DIS, DIS_WIDTH / 2, 60)
        play_button = draw_button(DIS, GREEN, 200, 150, 200, 50, "Play", BLACK)
        settings_button = draw_button(DIS, GREY, 200, 220, 200, 50, "Settings", BLACK)
        draw_volume_slider(DIS, volume)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if play_button.collidepoint(mx, my):
                    menu_running = False
                if settings_button.collidepoint(mx, my):
                    settings_menu()
                # Check if clicking slider knob
                if DIS_WIDTH-160 <= mx <= DIS_WIDTH-20 and 15 <= my <= 35:
                    dragging_volume = True

            if event.type == pygame.MOUSEBUTTONUP:
                dragging_volume = False

            if event.type == pygame.MOUSEMOTION and dragging_volume:
                mx, my = pygame.mouse.get_pos()
                volume = max(0, min(100, int((mx - (DIS_WIDTH-160))/140*100)))

# ---------------------- SETTINGS ----------------------
def settings_menu():
    global key_layout
    settings_running = True
    while settings_running:
        DIS.fill(BLUE)
        draw_text("Settings", font_style, WHITE, DIS, DIS_WIDTH / 2, 60)
        wasd_button = draw_button(DIS, GREEN if key_layout=='WASD' else GREY, 150, 150, 300, 50, "WASD (QWERTY)", BLACK)
        zqsd_button = draw_button(DIS, GREEN if key_layout=='ZQSD' else GREY, 150, 220, 300, 50, "ZQSD (AZERTY)", BLACK)
        back_button = draw_button(DIS, GREY, 200, 300, 200, 50, "Back", BLACK)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if wasd_button.collidepoint(mx, my):
                    key_layout = 'WASD'
                if zqsd_button.collidepoint(mx, my):
                    key_layout = 'ZQSD'
                if back_button.collidepoint(mx, my):
                    settings_running = False

# ---------------------- GAME LOOP ----------------------
def gameLoop():
    global key_layout
    x1, y1 = DIS_WIDTH / 2, DIS_HEIGHT / 2
    x1_change, y1_change = SNAKE_BLOCK, 0
    snake_List = []
    Length_of_snake = 4

    foodx = round(random.randrange(0, DIS_WIDTH - SNAKE_BLOCK) / 20.0) * 20.0
    foody = round(random.randrange(0, DIS_HEIGHT - SNAKE_BLOCK) / 20.0) * 20.0
    snake_speed = INITIAL_SPEED
    game_over = False
    game_close = False

    while not game_over:
        while game_close:
            DIS.fill(BLUE)
            draw_text("You Lost!", font_style, RED, DIS, DIS_WIDTH / 2, 150)
            draw_text("Press C to Play Again or Q to Quit", font_style, WHITE, DIS, DIS_WIDTH / 2, 200)
            Your_score(Length_of_snake - 4)
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        return False
                    if event.key == pygame.K_c:
                        return True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if key_layout == 'WASD':
                    left_keys, right_keys = [pygame.K_LEFT, pygame.K_a], [pygame.K_RIGHT, pygame.K_d]
                    up_keys, down_keys = [pygame.K_UP, pygame.K_w], [pygame.K_DOWN, pygame.K_s]
                else:
                    left_keys, right_keys = [pygame.K_LEFT, pygame.K_q], [pygame.K_RIGHT, pygame.K_d]
                    up_keys, down_keys = [pygame.K_UP, pygame.K_z], [pygame.K_DOWN, pygame.K_s]

                if event.key in left_keys and x1_change == 0:
                    x1_change, y1_change = -SNAKE_BLOCK, 0
                elif event.key in right_keys and x1_change == 0:
                    x1_change, y1_change = SNAKE_BLOCK, 0
                elif event.key in up_keys and y1_change == 0:
                    x1_change, y1_change = 0, -SNAKE_BLOCK
                elif event.key in down_keys and y1_change == 0:
                    x1_change, y1_change = 0, SNAKE_BLOCK

        if x1 >= DIS_WIDTH or x1 < 0 or y1 >= DIS_HEIGHT or y1 < 0:
            game_close = True

        x1 += x1_change
        y1 += y1_change
        DIS.blit(background_image, (0, 0))
        DIS.blit(apple_image, (foodx, foody))

        snake_Head = [x1, y1]
        snake_List.append(snake_Head)
        if len(snake_List) > Length_of_snake:
            del snake_List[0]

        for x in snake_List[:-1]:
            if x == snake_Head:
                game_close = True

        our_snake(snake_List)
        Your_score(Length_of_snake - 4)
        pygame.display.update()

        if x1 == foodx and y1 == foody:
            foodx = round(random.randrange(0, DIS_WIDTH - SNAKE_BLOCK) / 20.0) * 20.0
            foody = round(random.randrange(0, DIS_HEIGHT - SNAKE_BLOCK) / 20.0) * 20.0
            Length_of_snake += 1
            if (Length_of_snake - 4) % 3 == 0:
                snake_speed += 1

        clock.tick(snake_speed)

    return False

# ---------------------- MAIN LOOP ----------------------
while True:
    menu()
    if not gameLoop():
        break

pygame.quit()
sys.exit()
