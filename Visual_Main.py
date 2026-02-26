import sys
import pygame

from enemy import generate_enemy
from player import create_ninja, create_orc, create_queen, create_test_char

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Turn Based RPG")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 28)

# (label, builder function)
CHARACTERS = [
    ("Ninja", create_ninja),
    ("Orc", create_orc),
    ("Queen Carter", create_queen),
    ("Test Character", create_test_char),
]

buttons = []
start_y = 150
for i, (label, builder) in enumerate(CHARACTERS):
    rect = pygame.Rect(300, start_y + (i * 80), 300, 55)
    buttons.append({"rect": rect, "label": label, "builder": builder})

player = None
enemy = None
game_state = "choose_character"
message = "Choose your character to begin."


def draw_text(text, x, y, color=(255, 255, 255), use_small=False):
    renderer = small_font if use_small else font
    img = renderer.render(text, True, color)
    screen.blit(img, (x, y))


def start_battle(builder):
    global player, enemy, game_state, message
    player = builder()
    enemy = generate_enemy(player)
    game_state = "player_turn"
    message = f"You chose {player.name.title()}. Press 1 to Attack, 2 to Defend."


running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "choose_character":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for btn in buttons:
                    if btn["rect"].collidepoint(mx, my):
                        start_battle(btn["builder"])
                        break

        elif game_state == "player_turn":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    player.attack(enemy)
                    if enemy.alive():
                        game_state = "enemy_turn"
                        message = f"{player.name.title()} attacked!"
                    else:
                        game_state = "battle_over"
                        message = "Enemy defeated! Press R to choose again, Esc to quit."

                elif event.key == pygame.K_2:
                    player.defend()
                    game_state = "enemy_turn"
                    message = f"{player.name.title()} is defending."

        elif game_state == "battle_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_state = "choose_character"
                    player = None
                    enemy = None
                    message = "Choose your character to begin."
                elif event.key == pygame.K_ESCAPE:
                    running = False

    if game_state == "enemy_turn" and player and enemy:
        if player.alive() and enemy.alive():
            enemy.attack(player)

        if not player.alive():
            game_state = "battle_over"
            message = "You were defeated. Press R to choose again, Esc to quit."
        elif not enemy.alive():
            game_state = "battle_over"
            message = "Enemy defeated! Press R to choose again, Esc to quit."
        else:
            game_state = "player_turn"
            message = "Your turn. Press 1 to Attack, 2 to Defend."

    screen.fill((30, 30, 30))

    if game_state == "choose_character":
        draw_text("Choose Your Character", 305, 70)
        for btn in buttons:
            pygame.draw.rect(screen, (70, 70, 200), btn["rect"], border_radius=8)
            draw_text(btn["label"], btn["rect"].x + 15, btn["rect"].y + 12)
        draw_text(message, 260, 500, use_small=True)

    else:
        draw_text(f"Player: {player.name.title()}", 40, 30)
        draw_text(f"Player HP: {int(player.health)}", 40, 70)
        draw_text(f"Enemy: {enemy.name}", 560, 30)
        draw_text(f"Enemy HP: {int(enemy.health)}", 560, 70)
        draw_text(message, 60, 500, use_small=True)

        if game_state == "player_turn":
            draw_text("1 = Attack    2 = Defend", 300, 540, use_small=True)

        if game_state == "battle_over":
            draw_text("R = Character Select    Esc = Quit", 250, 540, use_small=True)

    pygame.display.flip()

pygame.quit()
sys.exit()
