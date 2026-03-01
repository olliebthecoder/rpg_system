import io
import os
import sys
from contextlib import redirect_stdout
import pygame

from enemy import generate_enemy, decide_enemy_action
from player import (
    create_Cheat_Char,
    create_ninja,
    create_orc,
    create_queen,
    create_test_char,
)
from Items import ITEM_DATABASE
from loot.drops import roll_drops

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
    ("Cheat Character", create_Cheat_Char),
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
shop_index = 0
inventory_return_state = "player_turn"
player_turn_started = False
player_action_used = False
enemy_turn_started_at = None
enemy_turn_status_processed = False
ENEMY_ATTACK_DELAY_MS = 700

# Lightweight feedback effects
damage_popups = []
battle_log = []
battle_log_scroll = 0
player_flash_timer = 0
enemy_flash_timer = 0
preview_scroll_offset = 0
preview_max_scroll = 0
preview_item_key = None
preview_scroll_rect = pygame.Rect(0, 0, 0, 0)
ninja_sprite_frames = []
ninja_sprite_notice_shown = False
tank_enemy_sprite_frames = []
player_hp_bar_sprite = None
enemy_hp_bar_sprite = None
battle_log_panel_sprite = None


def get_battle_action_buttons():
    return {
        "attack": pygame.Rect(220, 534, 130, 34),
        "defend": pygame.Rect(360, 534, 130, 34),
        "inventory": pygame.Rect(500, 534, 130, 34),
        "save": pygame.Rect(640, 534, 130, 34),
        "end_turn": pygame.Rect(780, 534, 100, 34),
    }


def begin_enemy_turn():
    global game_state, enemy_turn_started_at, enemy_turn_status_processed, message
    game_state = "enemy_turn"
    enemy_turn_started_at = pygame.time.get_ticks()
    enemy_turn_status_processed = False
    message = "Enemy is preparing an action..."


def draw_text(text, x, y, color=(255, 255, 255), use_small=False):
    renderer = small_font if use_small else font
    img = renderer.render(text, True, color)
    screen.blit(img, (x, y))


def add_log(text):
    global battle_log_scroll
    battle_log.append(text)
    if len(battle_log) > 200:
        battle_log.pop(0)
    battle_log_scroll = 0


def get_battle_log_line_color(line):
    lower = line.lower()

    # Effect/status-specific colors.
    effect_colors = [
        ("burn", (255, 150, 90)),
        ("poison", (145, 235, 145)),
        ("freeze", (145, 220, 255)),
        ("bleed", (255, 120, 120)),
        ("lightning", (255, 225, 120)),
        ("weaken", (240, 200, 130)),
        ("armor break", (230, 190, 140)),
        ("afflicted", (255, 220, 140)),
        ("recovered", (165, 235, 175)),
    ]
    for key, color in effect_colors:
        if key in lower:
            return color

    # Enemy actions: red.
    enemy_action_tokens = [
        " hit you",
        " attacked",
        " defended",
        " braces(defend)",
        " hides(defend)",
        " protects themself",
        " charges",
        " strikes",
        " swings",
    ]
    if "crit!" in lower and "you hit" not in lower:
        return (255, 125, 125)
    if any(token in lower for token in enemy_action_tokens):
        return (245, 130, 130)

    # Player actions: green.
    player_action_tokens = [
        "you attacked",
        "you defended",
        "you ended your turn",
        "used ",
        "equipped ",
        "unequipped",
        "bought ",
        "saved game",
    ]
    if "crit! you hit" in lower:
        return (130, 255, 160)
    if any(token in lower for token in player_action_tokens):
        return (140, 235, 145)

    # Everything else: blue/system.
    return (150, 190, 255)


def perform_attack(attacker, defender):
    before_hp = defender.health
    buf = io.StringIO()
    with redirect_stdout(buf):
        attacker.attack(defender)
    output = buf.getvalue()
    damage = max(0, before_hp - defender.health)
    return {
        "damage": damage,
        "crit": "CRITICAL HIT" in output,
        "dodged": "DODGED" in output,
    }


def enemy_action_text(enemy, action):
    archetype = getattr(enemy, "archetype", "")
    if action == "defend":
        if archetype == "Tank":
            return f"{enemy.name} BRACES(defend)."
        if archetype == "Assassin":
            return f"{enemy.name} hides(defend)."
        if archetype == "Bruiser":
            return f"{enemy.name} protects themself."
        return f"{enemy.name} defended."
    if action == "attack":
        if archetype == "Tank":
            return f"{enemy.name} charges!"
        if archetype == "Assassin":
            return f"{enemy.name} strikes!"
        if archetype == "Bruiser":
            return f"{enemy.name} swings!"
    return f"{enemy.name} attacked."


def _effect_signature(character):
    sig = []
    for eff in getattr(character, "status_effects", []):
        sig.append((str(eff.get("type", "?")), int(eff.get("duration", 0))))
    sig.sort()
    return sig


def _effect_display(effect):
    etype = str(effect.get("type", "?"))
    duration = effect.get("duration", 0)
    if duration < 0:
        return f"{etype} (permanent)"
    return f"{etype} ({duration}t)"


def draw_active_effects(label, effects, x, y):
    draw_text(f"{label} Effects:", x, y, color=(255, 225, 150), use_small=True)
    if not effects:
        draw_text("None", x, y + 18, color=(165, 165, 165), use_small=True)
        return

    for i, eff in enumerate(effects[:4]):
        draw_text(
            _effect_display(eff),
            x,
            y + 18 + (i * 16),
            color=(235, 235, 235),
            use_small=True,
        )
    if len(effects) > 4:
        draw_text(
            f"+{len(effects) - 4} more",
            x,
            y + 18 + (4 * 16),
            color=(165, 165, 165),
            use_small=True,
        )


def log_effect_changes(label, before_sig, character):
    after_effects = getattr(character, "status_effects", [])
    after_sig = _effect_signature(character)

    if after_effects:
        effects_text = ", ".join(_effect_display(eff) for eff in after_effects)
        add_log(f"{label} afflicted: {effects_text}")
    elif before_sig:
        add_log(f"{label} has no active effects.")

    # Only mark an effect as recovered when that effect type disappears entirely.
    before_types = {etype for etype, _ in before_sig}
    after_types = {etype for etype, _ in after_sig}
    removed_types = sorted(before_types - after_types)
    if removed_types:
        removed_text = ", ".join(removed_types)
        add_log(f"{label} recovered from: {removed_text}")


def add_damage_popup(target_side, amount):
    if amount <= 0:
        return
    x = 125 if target_side == "player" else 645
    y = 190
    damage_popups.append(
        {"text": f"-{int(amount)}", "x": x, "y": y, "color": (255, 90, 90), "ttl": 45}
    )


def get_battle_log_panel_rect():
    return pygame.Rect(50, 350, 800, 150)


def draw_hp_bar(x, y, width, height, current_hp, max_hp, flash_timer, bar_sprite=None):
    ratio = 0 if max_hp <= 0 else max(0.0, min(1.0, current_hp / max_hp))
    fill_width = int(width * ratio)

    if bar_sprite:
        # Draw dark background lane then clip the bar sprite by current health ratio.
        pygame.draw.rect(screen, (28, 28, 28), (x, y, width, height), border_radius=6)
        scaled = pygame.transform.smoothscale(bar_sprite, (width, height))
        if fill_width > 0:
            area = pygame.Rect(0, 0, fill_width, height)
            screen.blit(scaled, (x, y), area=area)
        if flash_timer > 0:
            flash = pygame.Surface((width, height), pygame.SRCALPHA)
            flash.fill((255, 70, 70, 80))
            screen.blit(flash, (x, y))
        return

    pygame.draw.rect(screen, (55, 55, 55), (x, y, width, height), border_radius=6)
    hp_color = (50, 190, 80) if flash_timer <= 0 else (255, 120, 120)
    pygame.draw.rect(screen, hp_color, (x, y, fill_width, height), border_radius=6)
    pygame.draw.rect(
        screen, (200, 200, 200), (x, y, width, height), width=2, border_radius=6
    )


def load_ui_sprite(candidates):
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            return pygame.image.load(path).convert_alpha()
        except Exception:
            continue
    return None


def get_model_palette(name: str, is_enemy: bool = False):
    n = (name or "").lower()
    skin = (228, 186, 148)
    outfit = (85, 125, 210)
    legs = (48, 56, 72)

    if "ninja" in n:
        outfit, legs = (45, 45, 55), (28, 28, 36)
    elif "orc" in n:
        skin, outfit, legs = (108, 164, 94), (95, 70, 55), (55, 40, 32)
    elif "queen" in n:
        outfit, legs = (170, 75, 135), (96, 55, 96)
    elif "test" in n:
        outfit, legs = (60, 140, 150), (40, 82, 90)
    elif "cheat" in n:
        outfit, legs = (210, 125, 50), (95, 55, 25)
    elif "tank" in n:
        outfit, legs = (95, 105, 118), (55, 65, 78)
    elif "assassin" in n:
        outfit, legs = (65, 50, 85), (42, 34, 58)
    elif "bruiser" in n:
        outfit, legs = (130, 95, 65), (78, 56, 38)
    elif "glass cannon" in n:
        outfit, legs = (170, 70, 70), (88, 45, 45)

    if is_enemy:
        # Shift enemy models slightly warmer/darker to distinguish sides.
        outfit = tuple(max(0, min(255, c - 18)) for c in outfit)
        legs = tuple(max(0, min(255, c - 14)) for c in legs)

    return {"skin": skin, "outfit": outfit, "legs": legs}


def draw_character_model(x: int, y: int, palette: dict):
    # Shadow
    pygame.draw.ellipse(screen, (18, 18, 24), (x - 24, y + 96, 48, 12))
    # Head
    pygame.draw.circle(screen, palette["skin"], (x, y), 16)
    # Torso
    pygame.draw.rect(
        screen, palette["outfit"], (x - 15, y + 18, 30, 42), border_radius=7
    )
    # Arms
    pygame.draw.rect(screen, palette["skin"], (x - 27, y + 22, 10, 28), border_radius=4)
    pygame.draw.rect(screen, palette["skin"], (x + 17, y + 22, 10, 28), border_radius=4)
    # Legs
    pygame.draw.rect(screen, palette["legs"], (x - 12, y + 60, 10, 34), border_radius=4)
    pygame.draw.rect(screen, palette["legs"], (x + 2, y + 60, 10, 34), border_radius=4)


def load_vertical_sprite_sheet(path, frame_count=2, scale=(96, 96)):
    if not os.path.exists(path):
        return []
    try:
        sheet = pygame.image.load(path).convert_alpha()
    except Exception:
        return []
    frame_h = sheet.get_height() // frame_count
    frame_w = sheet.get_width()
    if frame_h <= 0 or frame_w <= 0:
        return []
    frames = []
    for i in range(frame_count):
        rect = pygame.Rect(0, i * frame_h, frame_w, frame_h)
        frame = sheet.subsurface(rect).copy()
        if scale:
            frame = pygame.transform.scale(frame, scale)
        frames.append(frame)
    return frames


def build_inline_ninja_frames(scale=(96, 96)):
    """Fallback 2-frame ninja sprite (matches the shared red/sword style)."""
    frames = []
    for step in range(2):
        surf = pygame.Surface((24, 32), pygame.SRCALPHA)
        red = (220, 35, 35)
        steel = (185, 185, 185)
        shadow = (40, 40, 40)

        # Body/head
        pygame.draw.rect(surf, red, (8, 8, 8, 10), border_radius=2)
        pygame.draw.circle(surf, red, (12, 6), 3)

        # Legs (alternate stance per frame)
        if step == 0:
            pygame.draw.line(surf, red, (10, 18), (5, 27), 3)
            pygame.draw.line(surf, red, (14, 18), (17, 27), 3)
        else:
            pygame.draw.line(surf, red, (10, 18), (7, 27), 3)
            pygame.draw.line(surf, red, (14, 18), (19, 25), 3)

        # Arms + sword
        pygame.draw.line(surf, red, (8, 12), (4, 14), 2)
        pygame.draw.line(surf, red, (16, 12), (20, 10), 2)
        pygame.draw.line(surf, steel, (18, 11), (23, 6), 2)
        pygame.draw.line(surf, shadow, (16, 13), (18, 11), 2)

        if scale:
            surf = pygame.transform.scale(surf, scale)
        frames.append(surf)
    return frames


def load_ninja_sprite_frames():
    candidates = [
        "assets/sprites/ninja_sheet.png",
        "assets/sprites/ninja.png",
        "assets/ninja_sheet.png",
        "assets/ninja.png",
        "ninja_sheet.png",
        "ninja.png",
    ]
    for path in candidates:
        frames = load_vertical_sprite_sheet(path, frame_count=2, scale=(96, 96))
        if frames:
            return frames
    return build_inline_ninja_frames(scale=(96, 96))


def load_tank_enemy_sprite_frames():
    candidates = [
        "assets/sprites/enemy_tank_sheet.png",
        "assets/sprites/tank_enemy_sheet.png",
        "assets/sprites/tank_sheet.png",
        "assets/enemy_tank_sheet.png",
        "enemy_tank_sheet.png",
        "tank_sheet.png",
    ]
    for path in candidates:
        frames = load_vertical_sprite_sheet(path, frame_count=2, scale=(96, 96))
        if frames:
            return frames
    return []


def draw_player_model(character):
    if character and "ninja" in character.name.lower() and ninja_sprite_frames:
        frame_index = (pygame.time.get_ticks() // 220) % len(ninja_sprite_frames)
        frame = ninja_sprite_frames[frame_index]
        rect = frame.get_rect(center=(220, 272))
        screen.blit(frame, rect)
    else:
        draw_character_model(
            220, 225, get_model_palette(character.name, is_enemy=False)
        )


def draw_enemy_model(character):
    archetype = str(getattr(character, "archetype", "")).lower() if character else ""
    if character and archetype == "tank" and tank_enemy_sprite_frames:
        frame_index = (pygame.time.get_ticks() // 220) % len(tank_enemy_sprite_frames)
        frame = tank_enemy_sprite_frames[frame_index]
        rect = frame.get_rect(center=(680, 272))
        screen.blit(frame, rect)
    else:
        draw_character_model(680, 225, get_model_palette(character.name, is_enemy=True))


def start_battle(builder):
    global player, enemy, game_state, message, player_turn_started, player_action_used, ninja_sprite_notice_shown
    player = builder()
    player.load()
    player.reset_health()
    enemy = generate_enemy(player)
    game_state = "player_turn"
    player_turn_started = True
    player_action_used = False
    message = f"You chose {player.name.title()}. Your turn!"
    battle_log.clear()
    add_log(f"Started run with {player.name.title()}.")
    add_log(f"Enemy spawned: {enemy.name}.")
    if (
        "ninja" in player.name.lower()
        and not ninja_sprite_frames
        and not ninja_sprite_notice_shown
    ):
        add_log("Ninja sprite sheet not found. Using placeholder model.")
        ninja_sprite_notice_shown = True


def start_next_battle():
    global enemy, game_state, message, player_turn_started, battle_log_scroll, player_action_used
    player.reset_health()
    enemy = generate_enemy(player)
    game_state = "player_turn"
    player_turn_started = True
    player_action_used = False
    message = "A new enemy appears! Your turn."
    battle_log.clear()
    battle_log_scroll = 0
    add_log("Moved to next battle.")
    add_log(f"Enemy spawned: {enemy.name}.")


def handle_battle_end():
    global game_state, message, shop_index
    if player.alive() and not enemy.alive():
        is_boss = "BOSS" in enemy.name.upper()
        xp_reward = 200 if is_boss else 50
        gold_reward = 100 if is_boss else 20
        player.gain_xp(xp_reward)
        player.gain_gold(gold_reward)

        drops = getattr(enemy, "drops", [])
        dropped_items = roll_drops(drops)
        if dropped_items:
            for item_name in dropped_items:
                player.add_item(item_name, 1)
            message = f"Victory! +{xp_reward} XP, +{gold_reward} gold, {len(dropped_items)} drop(s)."
            add_log(
                f"Victory! +{xp_reward} XP, +{gold_reward}g, {len(dropped_items)} drops."
            )
        else:
            message = f"Victory! +{xp_reward} XP, +{gold_reward} gold."
            add_log(f"Victory! +{xp_reward} XP, +{gold_reward}g.")

        game_state = "shop"
        shop_index = 0
        add_log("Entered shop.")
    else:
        message = "You were defeated! Press R to choose again."
        game_state = "battle_over"
        add_log("Defeat.")


def draw_shop_panel():
    rarity_glow = {
        "Common": (190, 190, 190),
        "Uncommon": (90, 210, 120),
        "Rare": (90, 140, 255),
        "Epic": (210, 110, 255),
        "Legendary": (255, 190, 70),
        "Mythic": (255, 80, 80),
    }
    items = list(ITEM_DATABASE.keys())
    panel = pygame.Rect(120, 110, 660, 370)
    pygame.draw.rect(screen, (40, 40, 52), panel, border_radius=10)
    pygame.draw.rect(screen, (120, 120, 145), panel, width=2, border_radius=10)

    draw_text("Shop", panel.x + 14, panel.y + 12)
    draw_text(
        f"Gold: {player.gold}",
        panel.x + 520,
        panel.y + 14,
        color=(245, 210, 120),
        use_small=True,
    )

    start = max(0, min(shop_index - 4, len(items) - 8))
    visible = items[start : start + 8]
    row_rects = []
    for offset, key in enumerate(visible):
        idx = start + offset
        row = pygame.Rect(panel.x + 14, panel.y + 50 + offset * 32, 355, 26)
        row_rects.append((idx, row))
        item = ITEM_DATABASE[key]
        glow = rarity_glow.get(item.rarity, (180, 180, 180))
        # soft rarity glow border
        pygame.draw.rect(screen, glow, row.inflate(2, 2), width=2, border_radius=6)
        if idx == shop_index:
            pygame.draw.rect(screen, (76, 76, 126), row, border_radius=5)
        else:
            pygame.draw.rect(screen, (48, 52, 66), row, border_radius=5)
        draw_text(f"{item.name} ({item.price}g)", row.x + 8, row.y + 2, use_small=True)

    selected_key = items[shop_index]
    selected = ITEM_DATABASE[selected_key]
    preview = pygame.Rect(panel.x + 382, panel.y + 50, 262, 250)
    pygame.draw.rect(screen, (34, 38, 50), preview, border_radius=8)
    selected_glow = rarity_glow.get(selected.rarity, (180, 180, 180))
    # layered border to make the rarity glow more visible
    pygame.draw.rect(
        screen, selected_glow, preview.inflate(10, 10), width=2, border_radius=12
    )
    pygame.draw.rect(
        screen, selected_glow, preview.inflate(4, 4), width=2, border_radius=10
    )
    pygame.draw.rect(screen, (108, 128, 170), preview, width=2, border_radius=8)
    draw_text(selected.name, preview.x + 10, preview.y + 10, use_small=True)
    draw_text(f"Type: {selected.type}", preview.x + 10, preview.y + 34, use_small=True)
    draw_text(
        f"Rarity: {selected.rarity}", preview.x + 10, preview.y + 54, use_small=True
    )
    draw_text(
        f"Price: {selected.price}g",
        preview.x + 10,
        preview.y + 74,
        color=(240, 200, 110),
        use_small=True,
    )
    y = preview.y + 98
    for line in wrap_small_text(selected.description, 244)[:7]:
        draw_text(line, preview.x + 10, y, color=(220, 220, 220), use_small=True)
        y += 18

    buy_btn = pygame.Rect(panel.x + 382, panel.y + 310, 262, 28)
    next_btn = pygame.Rect(panel.x + 382, panel.y + 342, 262, 28)
    inv_btn = pygame.Rect(panel.x + 14, panel.y + 342, 355, 28)
    pygame.draw.rect(screen, (75, 130, 80), buy_btn, border_radius=6)
    pygame.draw.rect(screen, (105, 90, 150), inv_btn, border_radius=6)
    pygame.draw.rect(screen, (130, 80, 80), next_btn, border_radius=6)
    draw_text("Buy Selected", buy_btn.x + 10, buy_btn.y + 4, use_small=True)
    draw_text("Inventory", inv_btn.x + 10, inv_btn.y + 4, use_small=True)
    draw_text("Next Battle", next_btn.x + 10, next_btn.y + 4, use_small=True)

    return items, row_rects, buy_btn, inv_btn, next_btn


def buy_selected_shop_item():
    global message
    key = list(ITEM_DATABASE.keys())[shop_index]
    item = ITEM_DATABASE[key]
    if player.gold < item.price:
        message = "Not enough gold."
        add_log(f"Could not buy {item.name} (not enough gold).")
        return
    player.gold -= item.price
    player.add_item(key, 1)
    message = f"Bought {item.name}."
    add_log(f"Bought {item.name} for {item.price}g.")


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


def plus_value(value):
    if isinstance(value, (int, float)) and value >= 0:
        return f"+{format_value(value)}"
    return format_value(value)


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


def pretty_key(name):
    key = str(name).replace("_", " ").strip().title()
    aliases = {
        "Crit Chance": "Crit %",
        "Crit Multiplier": "Crit Damage",
        "Attack Pct": "Attack Reduction",
        "Defense Pct": "Defense Reduction",
    }
    return aliases.get(key, key)


def _equipped_item_for_preview(character, item_type):
    if not character:
        return None
    equipped_name = None
    if item_type == "weapon":
        equipped_name = character.equipped_weapon
    elif item_type == "armor":
        equipped_name = character.equipped_armor
    if not equipped_name:
        return None
    _, equipped_item = resolve_item_data(equipped_name)
    return equipped_item


def build_preview_lines(item, character=None):
    lines = []
    lines.append(("STATS", (130, 200, 255)))
    equipped_item = _equipped_item_for_preview(character, item.type)
    if equipped_item:
        lines.append((f"Comparing vs: {equipped_item.name}", (165, 180, 220)))
    if item.bonuses:
        for stat, val in item.bonuses.items():
            stat_name = stat.replace("_", " ").title()
            line_color = (210, 230, 255)
            compare_text = ""
            equipped_bonus = 0
            if (
                equipped_item
                and isinstance(val, (int, float))
                and isinstance(equipped_item.bonuses, dict)
            ):
                eq_val = equipped_item.bonuses.get(stat, 0)
                if isinstance(eq_val, (int, float)):
                    equipped_bonus = eq_val
                diff = val - equipped_bonus
                if diff > 0:
                    line_color = (130, 240, 150)
                    compare_text = f" ({plus_value(diff)})"
                elif diff < 0:
                    line_color = (255, 150, 150)
                    compare_text = f" ({plus_value(diff)})"
                else:
                    line_color = (205, 205, 205)
                    compare_text = " (same)"
            lines.append((f"{stat_name}: {plus_value(val)}{compare_text}", line_color))
    else:
        lines.append(("No stat bonuses", (170, 170, 170)))

    lines.append(("EFFECTS", (255, 215, 130)))
    has_effect_info = False
    if item.effect:
        has_effect_info = True
        effect_name = item.effect.replace("_", " ").title()
        effect_text = f"- {effect_name}: {format_value(item.value)}"
        for line in wrap_small_text(effect_text, 385):
            lines.append((line, (210, 250, 220)))
    if item.special:
        has_effect_info = True
        lines.append(("Special Traits:", (255, 225, 170)))
        for key, val in item.special.items():
            special_line = f"- {pretty_key(key)}: {format_value(val)}"
            for line in wrap_small_text(special_line, 385):
                lines.append((line, (255, 235, 180)))
    if not has_effect_info:
        lines.append(("No special effects", (170, 170, 170)))

    # Add a spacer before description for readability.
    lines.append(("", (225, 225, 225)))
    lines.append(("DESCRIPTION", (170, 210, 255)))
    for line in wrap_small_text(item.description, 385):
        lines.append((line, (225, 225, 225)))
    return lines


def draw_item_preview(panel, item_name, scroll_offset, character=None):
    preview_rect = pygame.Rect(panel.x + 16, panel.y + 238, 420, 140)
    content_rect = pygame.Rect(
        preview_rect.x + 8, preview_rect.y + 54, preview_rect.width - 16, 78
    )
    pygame.draw.rect(screen, (42, 46, 58), preview_rect, border_radius=10)
    pygame.draw.rect(screen, (118, 140, 178), preview_rect, width=2, border_radius=10)

    _, item = resolve_item_data(item_name)
    if not item:
        draw_text(
            "No item data available.",
            preview_rect.x + 10,
            preview_rect.y + 10,
            use_small=True,
        )
        pygame.draw.rect(screen, (35, 38, 48), content_rect, border_radius=6)
        return content_rect, 0

    draw_text(
        "HOVER PREVIEW",
        preview_rect.x + 10,
        preview_rect.y + 6,
        color=(160, 220, 255),
        use_small=True,
    )
    draw_text(
        f"{item.name} [{item.type}] ({item.rarity})",
        preview_rect.x + 10,
        preview_rect.y + 30,
        color=(245, 245, 245),
        use_small=True,
    )

    pygame.draw.rect(screen, (35, 38, 48), content_rect, border_radius=6)

    lines = build_preview_lines(item, character)
    line_height = 18
    visible_lines = max(1, content_rect.height // line_height)
    max_scroll = max(0, len(lines) - visible_lines)
    offset = max(0, min(scroll_offset, max_scroll))
    visible = lines[offset : offset + visible_lines]

    y = content_rect.y + 2
    for text, color in visible:
        draw_text(text, content_rect.x + 6, y, color=color, use_small=True)
        y += line_height

    if offset > 0:
        draw_text(
            "^ more",
            content_rect.right - 70,
            content_rect.y - 2,
            color=(170, 170, 170),
            use_small=True,
        )
    if offset < max_scroll:
        draw_text(
            "v more",
            content_rect.right - 70,
            content_rect.bottom - 16,
            color=(170, 170, 170),
            use_small=True,
        )

    return content_rect, max_scroll


def build_inventory_ui(character, selected_index):
    panel = pygame.Rect(130, 105, 640, 390)
    entries = get_inventory_entries(character)
    list_y = panel.y + 122
    max_rows = 4
    start = max(0, min(selected_index - (max_rows // 2), len(entries) - max_rows))
    visible = entries[start : start + max_rows]

    row_rects = []
    for offset, (item_name, qty) in enumerate(visible):
        i = start + offset
        row_rect = pygame.Rect(panel.x + 16, list_y + (offset * 28), 420, 24)
        row_rects.append((i, row_rect, item_name, qty))

    action_buttons = {
        "use": pygame.Rect(panel.x + 462, panel.y + 138, 155, 32),
        "equip": pygame.Rect(panel.x + 462, panel.y + 176, 155, 32),
        "unequip_weapon": pygame.Rect(panel.x + 462, panel.y + 214, 155, 32),
        "unequip_armor": pygame.Rect(panel.x + 462, panel.y + 252, 155, 32),
        "back": pygame.Rect(panel.x + 462, panel.y + 290, 155, 32),
    }

    return {
        "panel": panel,
        "entries": entries,
        "row_rects": row_rects,
        "buttons": action_buttons,
    }


def draw_inventory_panel(character, selected_index):
    global preview_scroll_offset, preview_max_scroll, preview_item_key, preview_scroll_rect
    rarity_glow = {
        "Common": (190, 190, 190),
        "Uncommon": (90, 210, 120),
        "Rare": (90, 140, 255),
        "Epic": (210, 110, 255),
        "Legendary": (255, 190, 70),
        "Mythic": (255, 80, 80),
    }
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
            _, item = resolve_item_data(item_name)
            glow = (
                rarity_glow.get(item.rarity, (180, 180, 180))
                if item
                else (180, 180, 180)
            )
            pygame.draw.rect(
                screen, glow, row_rect.inflate(2, 2), width=2, border_radius=6
            )
            if i == selected_index:
                pygame.draw.rect(screen, (80, 80, 130), row_rect, border_radius=6)
            elif is_hovered:
                pygame.draw.rect(screen, (65, 65, 85), row_rect, border_radius=6)
            else:
                pygame.draw.rect(screen, (48, 52, 66), row_rect, border_radius=6)
            if is_hovered:
                hovered_item_name = item_name

            item_type = item.type if item else "unknown"
            draw_text(
                f"{item_name} x{qty} [{item_type}]",
                panel.x + 18,
                row_rect.y + 1,
                use_small=True,
            )

        preview_name = hovered_item_name or entries[selected_index][0]
        if preview_name != preview_item_key:
            preview_item_key = preview_name
            preview_scroll_offset = 0
        preview_scroll_rect, preview_max_scroll = draw_item_preview(
            panel, preview_name, preview_scroll_offset, character
        )

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
        "Hover any item for full preview. Use mouse wheel on preview to scroll.",
        panel.x + 18,
        panel.y + 380,
        color=(170, 210, 255),
        use_small=True,
    )


ninja_sprite_frames = load_ninja_sprite_frames()
tank_enemy_sprite_frames = load_tank_enemy_sprite_frames()
player_hp_bar_sprite = None
enemy_hp_bar_sprite = None
battle_log_panel_sprite = load_ui_sprite(
    [
        "assets/sprites/Proto_battlelog.png",
        "assets/sprites/proto_battlelog.png",
        "assets/Proto_battlelog.png",
        "assets/proto_battlelog.png",
        "proto_battlelog.png",
    ]
)


running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEWHEEL and game_state != "choose_character":
            mx, my = pygame.mouse.get_pos()
            log_rect = get_battle_log_panel_rect()
            if log_rect.collidepoint(mx, my):
                visible_lines = 6
                max_scroll = max(0, len(battle_log) - visible_lines)
                battle_log_scroll = max(0, min(max_scroll, battle_log_scroll - event.y))
                continue

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
                    if player_action_used:
                        message = "You already used your action. End turn when ready."
                    else:
                        player.end_defend()
                        result = perform_attack(player, enemy)
                        damage = result["damage"]
                        if damage > 0:
                            enemy_flash_timer = 10
                            add_damage_popup("enemy", damage)
                            if result["crit"]:
                                add_log(
                                    f"CRIT! You hit {enemy.name} for {int(damage)}."
                                )
                            else:
                                add_log(f"You hit {enemy.name} for {int(damage)}.")
                        elif result["dodged"]:
                            add_log(f"{enemy.name} dodged your attack.")
                        else:
                            add_log("You attacked.")
                        player_action_used = True
                        message = "Action used. End turn when ready."
                elif event.key == pygame.K_2:
                    if player_action_used:
                        message = "You already used your action. End turn when ready."
                    else:
                        player.end_defend()
                        player.defend()
                        add_log("You defended.")
                        player_action_used = True
                        message = "Action used. End turn when ready."
                elif event.key == pygame.K_3:
                    inventory_return_state = "player_turn"
                    game_state = "inventory_menu"
                    inventory_index = 0
                    preview_item_key = None
                    preview_scroll_offset = 0
                    message = "Inventory menu opened."
                elif event.key == pygame.K_4:
                    begin_enemy_turn()
                    message = "You ended your turn."
                    add_log("You ended your turn.")
                elif event.key == pygame.K_5:
                    player.save()
                    game_state = "battle_over"
                    message = "Game saved. Press R to choose again."
                    add_log("Saved game.")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                battle_buttons = get_battle_action_buttons()
                if battle_buttons["attack"].collidepoint(mx, my):
                    if player_action_used:
                        message = "You already used your action. End turn when ready."
                    else:
                        player.end_defend()
                        result = perform_attack(player, enemy)
                        damage = result["damage"]
                        if damage > 0:
                            enemy_flash_timer = 10
                            add_damage_popup("enemy", damage)
                            if result["crit"]:
                                add_log(
                                    f"CRIT! You hit {enemy.name} for {int(damage)}."
                                )
                            else:
                                add_log(f"You hit {enemy.name} for {int(damage)}.")
                        elif result["dodged"]:
                            add_log(f"{enemy.name} dodged your attack.")
                        else:
                            add_log("You attacked.")
                        player_action_used = True
                        message = "Action used. End turn when ready."
                elif battle_buttons["defend"].collidepoint(mx, my):
                    if player_action_used:
                        message = "You already used your action. End turn when ready."
                    else:
                        player.end_defend()
                        player.defend()
                        add_log("You defended.")
                        player_action_used = True
                        message = "Action used. End turn when ready."
                elif battle_buttons["inventory"].collidepoint(mx, my):
                    inventory_return_state = "player_turn"
                    game_state = "inventory_menu"
                    inventory_index = 0
                    preview_item_key = None
                    preview_scroll_offset = 0
                    message = "Inventory menu opened."
                elif battle_buttons["save"].collidepoint(mx, my):
                    player.save()
                    game_state = "battle_over"
                    message = "Game saved. Press R to choose again."
                    add_log("Saved game.")
                elif battle_buttons["end_turn"].collidepoint(mx, my):
                    begin_enemy_turn()
                    message = "You ended your turn."
                    add_log("You ended your turn.")

        elif game_state == "inventory_menu" and player and enemy:
            entries = get_inventory_entries(player)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    game_state = inventory_return_state
                    message = "Closed inventory."
                elif event.key == pygame.K_DOWN and entries:
                    inventory_index = min(inventory_index + 1, len(entries) - 1)
                elif event.key == pygame.K_UP and entries:
                    inventory_index = max(inventory_index - 1, 0)
                elif event.key == pygame.K_u and entries:
                    selected_item = entries[inventory_index][0]
                    _, item = resolve_item_data(selected_item)
                    if item and item.type == "consumable":
                        if player_action_used:
                            message = (
                                "You already used your action. End turn when ready."
                            )
                        else:
                            player.end_defend()
                            player.use_item(selected_item)
                            player_action_used = True
                            message = f"Used {selected_item}. End turn when ready."
                            add_log(f"Used {selected_item}.")
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
            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if preview_scroll_rect.collidepoint(mx, my):
                    preview_scroll_offset = max(
                        0, min(preview_max_scroll, preview_scroll_offset - event.y)
                    )
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
                                if player_action_used:
                                    message = "You already used your action. End turn when ready."
                                else:
                                    player.end_defend()
                                    player.use_item(selected_item)
                                    player_action_used = True
                                    message = (
                                        f"Used {selected_item}. End turn when ready."
                                    )
                                    add_log(f"Used {selected_item}.")
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
                        game_state = inventory_return_state
                        message = "Closed inventory."

        elif game_state == "shop" and player:
            items = list(ITEM_DATABASE.keys())
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN and items:
                    shop_index = min(shop_index + 1, len(items) - 1)
                elif event.key == pygame.K_UP and items:
                    shop_index = max(shop_index - 1, 0)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    buy_selected_shop_item()
                elif event.key == pygame.K_i:
                    inventory_return_state = "shop"
                    game_state = "inventory_menu"
                    inventory_index = 0
                    message = "Inventory menu opened."
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    start_next_battle()
                    add_log("Left shop for next battle.")
            elif event.type == pygame.MOUSEWHEEL and items:
                shop_index = max(0, min(len(items) - 1, shop_index - event.y))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                _, row_rects, buy_btn, inv_btn, next_btn = draw_shop_panel()
                for idx, row in row_rects:
                    if row.collidepoint(event.pos):
                        shop_index = idx
                        break
                if buy_btn.collidepoint(event.pos):
                    buy_selected_shop_item()
                elif inv_btn.collidepoint(event.pos):
                    inventory_return_state = "shop"
                    game_state = "inventory_menu"
                    inventory_index = 0
                    message = "Inventory menu opened."
                elif next_btn.collidepoint(event.pos):
                    start_next_battle()
                    add_log("Left shop for next battle.")

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
        player_effects_before = _effect_signature(player)
        player.process_status_effects()
        log_effect_changes("You", player_effects_before, player)
        player_turn_started = False
        if not player.alive():
            handle_battle_end()

    if game_state == "enemy_turn" and player and enemy:
        if not enemy_turn_status_processed:
            enemy_effects_before = _effect_signature(enemy)
            enemy.process_status_effects()
            log_effect_changes("Enemy", enemy_effects_before, enemy)
            enemy_turn_status_processed = True
            if not enemy.alive() or not player.alive():
                handle_battle_end()

        if (
            game_state == "enemy_turn"
            and enemy.alive()
            and player.alive()
            and enemy_turn_started_at is not None
            and (pygame.time.get_ticks() - enemy_turn_started_at)
            >= ENEMY_ATTACK_DELAY_MS
        ):
            enemy.end_defend()
            enemy_action = decide_enemy_action(enemy, player)
            if enemy_action == "defend":
                enemy.defend()
                add_log(enemy_action_text(enemy, "defend"))
            else:
                result = perform_attack(enemy, player)
                damage = result["damage"]
                if damage > 0:
                    player_flash_timer = 10
                    add_damage_popup("player", damage)
                    if result["crit"]:
                        add_log(
                            f"CRIT! {enemy_action_text(enemy, 'attack')} ({int(damage)} dmg)"
                        )
                    else:
                        add_log(
                            f"{enemy_action_text(enemy, 'attack')} ({int(damage)} dmg)"
                        )
                elif result["dodged"]:
                    add_log(f"You dodged {enemy.name}'s attack.")
                else:
                    add_log(enemy_action_text(enemy, "attack"))

            if not player.alive() or not enemy.alive():
                handle_battle_end()
            else:
                game_state = "player_turn"
                player_turn_started = True
                player_action_used = False
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
            40,
            95,
            260,
            18,
            player.health,
            player.max_health,
            player_flash_timer,
            player_hp_bar_sprite,
        )
        draw_text(
            f"Weapon: {player.equipped_weapon or 'None'}", 40, 120, use_small=True
        )
        draw_text(f"Armor: {player.equipped_armor or 'None'}", 40, 145, use_small=True)
        if player.is_defending:
            draw_text("Defending!", 40, 170, color=(140, 210, 255), use_small=True)
        draw_active_effects("Player", player.status_effects, 40, 196)

        draw_text(f"Enemy: {enemy.name}", 560, 30)
        enemy_role = getattr(enemy, "archetype", "Unknown")
        if getattr(enemy, "is_boss", False):
            enemy_role = f"{enemy_role} (BOSS)"
        draw_text(f"Type: {enemy_role}", 560, 52, color=(255, 210, 170), use_small=True)
        draw_text(f"Enemy HP: {int(enemy.health)}", 560, 70)
        draw_hp_bar(
            560,
            95,
            260,
            18,
            enemy.health,
            enemy.max_health,
            enemy_flash_timer,
            enemy_hp_bar_sprite,
        )
        draw_text(
            f"Enemy Weapon: {enemy.equipped_weapon or 'None'}",
            560,
            120,
            use_small=True,
        )
        draw_text(
            f"Enemy Armor: {enemy.equipped_armor or 'None'}",
            560,
            145,
            use_small=True,
        )
        if enemy.is_defending:
            draw_text("Defending!", 560, 170, color=(140, 210, 255), use_small=True)

        # Turn banner
        if game_state in {"player_turn", "enemy_turn"}:
            banner = pygame.Rect(355, 8, 190, 28)
            pygame.draw.rect(screen, (45, 52, 70), banner, border_radius=8)
            pygame.draw.rect(screen, (120, 145, 190), banner, width=2, border_radius=8)
            turn_text = "YOUR TURN" if game_state == "player_turn" else "ENEMY TURN"
            turn_color = (
                (170, 220, 255) if game_state == "player_turn" else (255, 190, 170)
            )
            draw_text(
                turn_text, banner.x + 22, banner.y + 4, color=turn_color, use_small=True
            )
        draw_active_effects("Enemy", enemy.status_effects, 560, 196)

        # Player model (uses ninja sprite sheet when available).
        draw_player_model(player)
        # Enemy model (uses tank sprite sheet for Tank archetype when available).
        draw_enemy_model(enemy)

        log_panel = get_battle_log_panel_rect()
        if battle_log_panel_sprite:
            panel_img = pygame.transform.smoothscale(
                battle_log_panel_sprite, (log_panel.width, log_panel.height)
            )
            screen.blit(panel_img, (log_panel.x, log_panel.y))
        else:
            pygame.draw.rect(screen, (30, 34, 44), log_panel, border_radius=10)
            pygame.draw.rect(
                screen, (110, 128, 168), log_panel, width=2, border_radius=10
            )
            draw_text(
                "BATTLE LOG",
                log_panel.x + 10,
                log_panel.y + 8,
                color=(170, 210, 255),
                use_small=True,
            )
        visible_lines = 6
        max_scroll = max(0, len(battle_log) - visible_lines)
        battle_log_scroll = max(0, min(max_scroll, battle_log_scroll))
        start_idx = max(0, len(battle_log) - visible_lines - battle_log_scroll)
        visible_logs = battle_log[start_idx : start_idx + visible_lines]
        for i, line in enumerate(visible_logs):
            y = log_panel.y + 30 + (i * 16)
            row = pygame.Rect(log_panel.x + 6, y - 1, log_panel.width - 12, 16)
            if i % 2 == 0:
                pygame.draw.rect(screen, (36, 40, 52), row, border_radius=4)
            color = get_battle_log_line_color(line)
            line_number = start_idx + i + 1
            draw_text(
                f"{line_number:03d}. {line}",
                log_panel.x + 10,
                y,
                color=color,
                use_small=True,
            )
        if max_scroll > 0:
            draw_text(
                "Scroll wheel over log to view older entries",
                log_panel.right - 330,
                log_panel.y + 8,
                color=(160, 170, 190),
                use_small=True,
            )

        draw_text(message, 60, 500, use_small=True)

        if game_state == "player_turn":
            mouse_pos = pygame.mouse.get_pos()
            battle_buttons = get_battle_action_buttons()
            labels = {
                "attack": "Attack",
                "defend": "Defend",
                "inventory": "Inventory",
                "save": "Save",
                "end_turn": "End Turn",
            }
            for key, rect in battle_buttons.items():
                hovered = rect.collidepoint(mouse_pos)
                color = (95, 115, 180) if hovered else (70, 85, 145)
                pygame.draw.rect(screen, color, rect, border_radius=6)
                draw_text(labels[key], rect.x + 16, rect.y + 6, use_small=True)

        if game_state == "inventory_menu":
            entries = get_inventory_entries(player)
            if entries:
                inventory_index = max(0, min(inventory_index, len(entries) - 1))
            else:
                inventory_index = 0
            draw_inventory_panel(player, inventory_index)

        if game_state == "shop":
            draw_shop_panel()
            draw_text(
                "Up/Down select  Enter buy  I inventory  Q next battle",
                190,
                540,
                use_small=True,
            )

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
