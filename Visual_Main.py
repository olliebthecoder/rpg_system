import sys
import pygame

from enemy import generate_enemy
from player import create_ninja, create_orc, create_queen, create_test_char
from main import finish_battle
from Items import ITEM_DATABASE

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Turn Based RPG")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 28)

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
    preview = builder()
    buttons.append(
        {"rect": rect, "label": label, "builder": builder, "preview": preview}
    )

player = None
enemy = None
game_state = "choose_character"
message = "Choose your character to begin."
inventory_index = 0
player_turn_started = False

# Lightweight feedback effects
damage_popups = []
player_flash_timer = 0
enemy_flash_timer = 0


def draw_text(text, x, y, color=(255, 255, 255), use_small=False):
    renderer = small_font if use_small else font
    img = renderer.render(text, True, color)
    screen.blit(img, (x, y))


def add_damage_popup(target_side, amount):
    if amount <= 0:
        return
    x = 125 if target_side == "player" else 645
    y = 190
    damage_popups.append(
        {"text": f"-{int(amount)}", "x": x, "y": y, "color": (255, 90, 90), "ttl": 45}
    )


def draw_hp_bar(x, y, width, height, current_hp, max_hp, flash_timer):
    pygame.draw.rect(screen, (55, 55, 55), (x, y, width, height), border_radius=6)
    ratio = 0 if max_hp <= 0 else max(0.0, min(1.0, current_hp / max_hp))
    fill_width = int(width * ratio)
    hp_color = (50, 190, 80) if flash_timer <= 0 else (255, 120, 120)
    pygame.draw.rect(screen, hp_color, (x, y, fill_width, height), border_radius=6)
    pygame.draw.rect(
        screen, (200, 200, 200), (x, y, width, height), width=2, border_radius=6
    )


def start_battle(builder):
    global player, enemy, game_state, message, player_turn_started
    player = builder()
    player.load()
    player.reset_health()
    enemy = generate_enemy(player)
    game_state = "player_turn"
    player_turn_started = True
    message = f"You chose {player.name.title()}. Your turn!"


def draw_hover_panel(character):
    panel = pygame.Rect(40, 150, 230, 250)
    pygame.draw.rect(screen, (50, 50, 50), panel, border_radius=10)
    pygame.draw.rect(screen, (120, 120, 120), panel, width=2, border_radius=10)

    draw_text(
        f"{character.name.title()} Stats", panel.x + 12, panel.y + 12, use_small=True
    )
    draw_text(
        f"HP: {int(character.health)}", panel.x + 12, panel.y + 50, use_small=True
    )
    draw_text(
        f"ATK: {int(character.attack_power)}",
        panel.x + 12,
        panel.y + 80,
        use_small=True,
    )
    draw_text(
        f"SPD: {int(character.speed)}", panel.x + 12, panel.y + 110, use_small=True
    )
    draw_text(
        f"ATK SPD: {int(character.attack_speed)}",
        panel.x + 12,
        panel.y + 140,
        use_small=True,
    )
    draw_text(
        f"DEF: {int(character.defense)}", panel.x + 12, panel.y + 170, use_small=True
    )


def get_inventory_entries(character):
    return list(character.inventory.items())


def wrap_small_text(text, max_width):
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        test = f"{current} {word}"
        if small_font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def format_value(value):
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            parts.append(f"{k}:{format_value(v)}")
        return ", ".join(parts)
    return str(value)


def resolve_item_data(item_name):
    name = (item_name or "").strip()
    candidates = [
        name,
        name.title(),
        name.lower(),
        name.lower().replace(" ", "_"),
        name.replace("_", " ").title(),
        name.replace(" ", "_"),
    ]
    seen = set()
    for key in candidates:
        if key in seen:
            continue
        seen.add(key)
        if key in ITEM_DATABASE:
            return key, ITEM_DATABASE[key]
    return None, None


def draw_item_preview(panel, item_name):
    preview_rect = pygame.Rect(panel.x + 16, panel.y + 255, 604, 122)
    pygame.draw.rect(screen, (56, 56, 56), preview_rect, border_radius=8)
    pygame.draw.rect(screen, (110, 110, 110), preview_rect, width=1, border_radius=8)

    _, item = resolve_item_data(item_name)
    if not item:
        draw_text(
            "No item data available.",
            preview_rect.x + 10,
            preview_rect.y + 10,
            use_small=True,
        )
        return

    draw_text(
        "HOVER PREVIEW",
        preview_rect.x + 10,
        preview_rect.y + 6,
        color=(170, 210, 255),
        use_small=True,
    )
    draw_text(
        f"{item.name} [{item.type}] ({item.rarity})",
        preview_rect.x + 10,
        preview_rect.y + 30,
        use_small=True,
    )

    y = preview_rect.y + 54
    if item.bonuses:
        bonus_parts = []
        for stat, val in item.bonuses.items():
            sign = "+" if isinstance(val, (int, float)) and val >= 0 else ""
            bonus_parts.append(f"{stat}:{sign}{format_value(val)}")
        draw_text(
            f"Bonuses: {', '.join(bonus_parts)}", preview_rect.x + 10, y, use_small=True
        )
        y += 22

    if item.effect:
        draw_text(
            f"Effect: {item.effect} ({format_value(item.value)})",
            preview_rect.x + 10,
            y,
            use_small=True,
        )
        y += 22

    if item.special:
        special_parts = []
        for key, val in item.special.items():
            special_parts.append(f"{key}:{format_value(val)}")
        special_text = "Special: " + ", ".join(special_parts)
        for line in wrap_small_text(special_text, preview_rect.width - 20)[:2]:
            draw_text(line, preview_rect.x + 10, y, use_small=True)
            y += 20

    desc_lines = wrap_small_text(f"Desc: {item.description}", preview_rect.width - 20)[
        :2
    ]
    for line in desc_lines:
        if y > preview_rect.bottom - 20:
            break
        draw_text(line, preview_rect.x + 10, y, use_small=True)
        y += 20


def build_inventory_ui(character, selected_index):
    panel = pygame.Rect(130, 105, 640, 390)
    entries = get_inventory_entries(character)
    list_y = panel.y + 122
    max_rows = 5
    start = max(0, min(selected_index - (max_rows // 2), len(entries) - max_rows))
    visible = entries[start : start + max_rows]

    row_rects = []
    for offset, (item_name, qty) in enumerate(visible):
        i = start + offset
        row_rect = pygame.Rect(panel.x + 16, list_y + (offset * 28), 420, 24)
        row_rects.append((i, row_rect, item_name, qty))

    action_buttons = {
        "use": pygame.Rect(panel.x + 455, panel.y + 126, 165, 34),
        "equip": pygame.Rect(panel.x + 455, panel.y + 168, 165, 34),
        "unequip_weapon": pygame.Rect(panel.x + 455, panel.y + 210, 165, 34),
        "unequip_armor": pygame.Rect(panel.x + 455, panel.y + 252, 165, 34),
        "back": pygame.Rect(panel.x + 455, panel.y + 294, 165, 34),
    }

    return {
        "panel": panel,
        "entries": entries,
        "row_rects": row_rects,
        "buttons": action_buttons,
    }


def draw_inventory_panel(character, selected_index):
    ui = build_inventory_ui(character, selected_index)
    panel = ui["panel"]
    entries = ui["entries"]
    row_rects = ui["row_rects"]
    action_buttons = ui["buttons"]
    mouse_pos = pygame.mouse.get_pos()
    hovered_item_name = None

    pygame.draw.rect(screen, (48, 48, 48), panel, border_radius=10)
    pygame.draw.rect(screen, (120, 120, 120), panel, width=2, border_radius=10)

    draw_text("Inventory / Equip", panel.x + 18, panel.y + 14)
    draw_text(
        f"Weapon: {character.equipped_weapon or 'None'}",
        panel.x + 18,
        panel.y + 58,
        use_small=True,
    )
    draw_text(
        f"Armor: {character.equipped_armor or 'None'}",
        panel.x + 18,
        panel.y + 84,
        use_small=True,
    )

    list_y = panel.y + 122
    if not entries:
        draw_text("Inventory is empty.", panel.x + 18, list_y, use_small=True)
    else:
        for i, row_rect, item_name, qty in row_rects:
            is_hovered = row_rect.collidepoint(mouse_pos)
            if i == selected_index:
                pygame.draw.rect(screen, (80, 80, 130), row_rect, border_radius=6)
            elif is_hovered:
                pygame.draw.rect(screen, (65, 65, 85), row_rect, border_radius=6)
            if is_hovered:
                hovered_item_name = item_name

            item = ITEM_DATABASE.get(item_name)
            _, item = resolve_item_data(item_name)
            item_type = item.type if item else "unknown"
            draw_text(
                f"{item_name} x{qty} [{item_type}]",
                panel.x + 18,
                row_rect.y + 1,
                use_small=True,
            )

        preview_name = hovered_item_name or entries[selected_index][0]
        draw_item_preview(panel, preview_name)

    for key, rect in action_buttons.items():
        hovered = rect.collidepoint(mouse_pos)
        color = (95, 95, 190) if hovered else (70, 70, 160)
        pygame.draw.rect(screen, color, rect, border_radius=6)
        label = {
            "use": "Use (U)",
            "equip": "Equip (E)",
            "unequip_weapon": "Unequip W",
            "unequip_armor": "Unequip A",
            "back": "Back (Q)",
        }[key]
        draw_text(label, rect.x + 12, rect.y + 6, use_small=True)

    draw_text(
        "Hover any item for full preview. Click actions or use U/E/W/A/Q.",
        panel.x + 18,
        panel.y + 380,
        color=(170, 210, 255),
        use_small=True,
    )


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

        elif game_state == "player_turn" and player and enemy:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    player.end_defend()
                    enemy_before = enemy.health
                    player.attack(enemy)
                    damage = enemy_before - enemy.health
                    if damage > 0:
                        enemy_flash_timer = 10
                        add_damage_popup("enemy", damage)
                    game_state = "enemy_turn"
                    player_turn_started = True
                    message = "You attacked."
                elif event.key == pygame.K_2:
                    player.end_defend()
                    player.defend()
                    game_state = "enemy_turn"
                    player_turn_started = True
                    message = "You defended."
                elif event.key == pygame.K_3:
                    game_state = "inventory_menu"
                    inventory_index = 0
                    message = "Inventory menu opened."
                elif event.key == pygame.K_5:
                    player.save()
                    game_state = "battle_over"
                    message = "Game saved. Press R to choose again."

        elif game_state == "inventory_menu" and player and enemy:
            entries = get_inventory_entries(player)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    game_state = "player_turn"
                    message = "Back to battle."
                elif event.key == pygame.K_DOWN and entries:
                    inventory_index = min(inventory_index + 1, len(entries) - 1)
                elif event.key == pygame.K_UP and entries:
                    inventory_index = max(inventory_index - 1, 0)
                elif event.key == pygame.K_u and entries:
                    selected_item = entries[inventory_index][0]
                    _, item = resolve_item_data(selected_item)
                    if item and item.type == "consumable":
                        player.end_defend()
                        player.use_item(selected_item)
                        game_state = "enemy_turn"
                        player_turn_started = True
                        message = f"Used {selected_item}."
                    else:
                        message = "Selected item is not a consumable."
                elif event.key == pygame.K_e and entries:
                    selected_item = entries[inventory_index][0]
                    player.equip_item(selected_item)
                    message = f"Equipped {selected_item}."
                elif event.key == pygame.K_w:
                    player.unequip_item("weapon")
                    message = "Weapon unequipped."
                elif event.key == pygame.K_a:
                    player.unequip_item("armor")
                    message = "Armor unequipped."
            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                ui = build_inventory_ui(player, inventory_index)
                for idx, row_rect, _, _ in ui["row_rects"]:
                    if row_rect.collidepoint(mx, my):
                        inventory_index = idx
                        break
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                ui = build_inventory_ui(player, inventory_index)
                clicked = False

                for idx, row_rect, _, _ in ui["row_rects"]:
                    if row_rect.collidepoint(mx, my):
                        inventory_index = idx
                        clicked = True
                        break

                if not clicked:
                    action_buttons = ui["buttons"]
                    if action_buttons["use"].collidepoint(mx, my):
                        if entries:
                            selected_item = entries[inventory_index][0]
                            _, item = resolve_item_data(selected_item)
                            if item and item.type == "consumable":
                                player.end_defend()
                                player.use_item(selected_item)
                                game_state = "enemy_turn"
                                player_turn_started = True
                                message = f"Used {selected_item}."
                            else:
                                message = "Selected item is not a consumable."
                    elif action_buttons["equip"].collidepoint(mx, my):
                        if entries:
                            selected_item = entries[inventory_index][0]
                            player.equip_item(selected_item)
                            message = f"Equipped {selected_item}."
                    elif action_buttons["unequip_weapon"].collidepoint(mx, my):
                        player.unequip_item("weapon")
                        message = "Weapon unequipped."
                    elif action_buttons["unequip_armor"].collidepoint(mx, my):
                        player.unequip_item("armor")
                        message = "Armor unequipped."
                    elif action_buttons["back"].collidepoint(mx, my):
                        game_state = "player_turn"
                        message = "Back to battle."

        elif game_state == "battle_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_state = "choose_character"
                    player = None
                    enemy = None
                    message = "Choose your character to begin."
                elif event.key == pygame.K_ESCAPE:
                    running = False

    if game_state == "player_turn" and player and enemy and player_turn_started:
        player.process_status_effects()
        player_turn_started = False
        if not player.alive():
            finish_battle(player, enemy)
            game_state = "battle_over"
            message = "You were defeated! Press R to choose again."

    if game_state == "enemy_turn" and player and enemy:
        enemy.process_status_effects()
        if enemy.alive() and player.alive():
            player_before = player.health
            enemy.attack(player)
            damage = player_before - player.health
            if damage > 0:
                player_flash_timer = 10
                add_damage_popup("player", damage)
        if not player.alive() or not enemy.alive():
            finish_battle(player, enemy)
            game_state = "battle_over"
            if player.alive() and not enemy.alive():
                message = "Enemy defeated! Press R to choose again."
            else:
                message = "You were defeated! Press R to choose again."
        else:
            game_state = "player_turn"
            player_turn_started = True
            message = "Your turn."

    screen.fill((30, 30, 30))

    if player_flash_timer > 0:
        player_flash_timer -= 1
    if enemy_flash_timer > 0:
        enemy_flash_timer -= 1

    if game_state == "choose_character":
        draw_text("Choose Your Character", 305, 70)
        hovered_btn = None
        mouse_pos = pygame.mouse.get_pos()
        for btn in buttons:
            is_hovered = btn["rect"].collidepoint(mouse_pos)
            if is_hovered:
                hovered_btn = btn
            button_color = (100, 100, 235) if is_hovered else (70, 70, 200)
            pygame.draw.rect(screen, button_color, btn["rect"], border_radius=8)
            draw_text(btn["label"], btn["rect"].x + 15, btn["rect"].y + 12)

        if hovered_btn:
            draw_hover_panel(hovered_btn["preview"])

        draw_text(message, 260, 500, use_small=True)

    else:
        draw_text(f"Player: {player.name.title()}", 40, 30)
        draw_text(f"Player HP: {int(player.health)}", 40, 70)
        draw_hp_bar(
            40, 95, 260, 18, player.health, player.max_health, player_flash_timer
        )
        draw_text(
            f"Weapon: {player.equipped_weapon or 'None'}", 40, 120, use_small=True
        )
        draw_text(f"Armor: {player.equipped_armor or 'None'}", 40, 145, use_small=True)
        if player.is_defending:
            draw_text("Defending!", 40, 170, color=(140, 210, 255), use_small=True)

        draw_text(f"Enemy: {enemy.name}", 560, 30)
        draw_text(f"Enemy HP: {int(enemy.health)}", 560, 70)
        draw_hp_bar(560, 95, 260, 18, enemy.health, enemy.max_health, enemy_flash_timer)
        if enemy.is_defending:
            draw_text("Defending!", 560, 120, color=(140, 210, 255), use_small=True)

        draw_text(message, 60, 500, use_small=True)

        if game_state == "player_turn":
            draw_text(
                "1 = Attack    2 = Defend    3 = Inventory/Equip    5 = Save and Exit",
                220,
                540,
                use_small=True,
            )

        if game_state == "inventory_menu":
            entries = get_inventory_entries(player)
            if entries:
                inventory_index = max(0, min(inventory_index, len(entries) - 1))
            else:
                inventory_index = 0
            draw_inventory_panel(player, inventory_index)

        if game_state == "battle_over":
            draw_text("R = Character Select    Esc = Quit", 250, 540, use_small=True)

    for popup in damage_popups[:]:
        draw_text(popup["text"], popup["x"], popup["y"], color=popup["color"])
        popup["y"] -= 1
        popup["ttl"] -= 1
        if popup["ttl"] <= 0:
            damage_popups.remove(popup)

    pygame.display.flip()

pygame.quit()
sys.exit()
