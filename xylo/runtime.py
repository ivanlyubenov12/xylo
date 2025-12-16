from os import environ
import os
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
from xylo.errors import error


# -----------------------
# Paths / window icon
# -----------------------

BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "art_assets")

pygame.init()
programIcon = pygame.image.load(
    os.path.join(ASSETS_DIR, "runtime_icon.png")
)
pygame.display.set_icon(programIcon)


# -----------------------
# Engine state
# -----------------------

global_vars = {}
loaded_assets = {}
draw_queue = []
keys = {}


# -----------------------
# Built-in colors
# -----------------------

BUILTIN_COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "gray": (128, 128, 128)
}


# -----------------------
# Helpers
# -----------------------

def eval_value(value, global_vars, local_vars):
    value = value.strip()

    if value.lower() == "none":
        return None

    if value in BUILTIN_COLORS:
        return BUILTIN_COLORS[value]

    if value in local_vars:
        return local_vars[value]
    if value in global_vars:
        return global_vars[value]

    try:
        if "." in value:
            return float(value)
        return int(value)
    except:
        pass

    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]

    error(f"Invalid or undeclared value '{value}'")


# -----------------------
# Input
# -----------------------

KEY_MAP = {}
for attr in dir(pygame):
    if attr.startswith("K_"):
        KEY_MAP[getattr(pygame, attr)] = attr[2:].lower()

def update_keys():
    pressed = pygame.key.get_pressed()
    for k, name in KEY_MAP.items():
        keys[name] = pressed[k]


# -----------------------
# Runtime
# -----------------------

def execute(assets, global_lines, functions):
    global global_vars, loaded_assets, draw_queue

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("xylo. Runtime")
    clock = pygame.time.Clock()

    # Load assets
    for name, data in assets.items():
        if data["type"] == "sprite":
            loaded_assets[name] = pygame.image.load(data["path"]).convert_alpha()

    print("== xylo started ==")

    # Globals
    for _, cmd in global_lines:
        if cmd.startswith("var "):
            n, v = cmd[4:].split("=", 1)
            global_vars[n.strip()] = eval_value(v, global_vars, {})
        elif cmd.startswith("terminal.write"):
            print(eval_value(cmd.split("(",1)[1].rstrip(")"), global_vars, {}))

    execute_function("init", functions)

    running = True
    while running:
        clock.tick(60)
        update_keys()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((20, 20, 20))
        draw_queue.clear()

        execute_function("update", functions)
        execute_function("draw", functions)

        # -----------------------
        # Render
        # -----------------------
        for item in draw_queue:

            # Sprite
            if isinstance(item, tuple):
                sprite, x, y, sx, sy, rot = item
                try:
                    sx = max(0.01, float(sx))
                    sy = max(0.01, float(sy))

                    w = max(1, int(sprite.get_width() * sx))
                    h = max(1, int(sprite.get_height() * sy))

                    img = pygame.transform.scale(sprite, (w, h))

                    if rot != 0:
                        img = pygame.transform.rotate(img, -float(rot))

                    screen.blit(img, (x, y))
                except Exception as e:
                    print("[DRAW ERROR]", e)

            # Rectangle
            elif item["type"] == "rect":
                rect = pygame.Rect(item["x"], item["y"], item["w"], item["h"])

                # Stroke width
                stroke_width = item["strokewidth"] if isinstance(item["strokewidth"], (int, float)) else 0

                # Draw filled
                if item["fill"] is not None:
                    pygame.draw.rect(screen, item["fill"], rect)

                # Draw outline
                if item["stroke"] is not None and stroke_width > 0:
                    pygame.draw.rect(screen, item["stroke"], rect, stroke_width)

            # Circle
            elif item["type"] == "circle":
                stroke_width = item["strokewidth"] if isinstance(item["strokewidth"], (int, float)) else 0

                if item["fill"] is not None:
                    pygame.draw.circle(screen, item["fill"], (int(item["x"]), int(item["y"])), int(item["r"]))

                if item["stroke"] is not None and stroke_width > 0:
                    pygame.draw.circle(screen, item["stroke"], (int(item["x"]), int(item["y"])), int(item["r"]), stroke_width)

        pygame.display.flip()

    pygame.quit()
    print("== xylo stopped ==")


# -----------------------
# Function execution
# -----------------------

def execute_function(name, functions):
    local_vars = {}

    if name not in functions:
        return

    lines = functions[name]
    i = 0
    skip_stack = []

    while i < len(lines):
        line_no, cmd = lines[i]

        # Skip block
        if skip_stack and skip_stack[-1]:
            if cmd.endswith("{"):
                skip_stack.append(True)
            elif cmd == "}":
                skip_stack.pop()
            i += 1
            continue

        # IF block
        if cmd.startswith("if "):
            condition = cmd[3:].strip()
            if not condition.endswith("{"):
                error("Missing '{' after if", line_no)
            condition = condition[:-1].strip()

            execute = False
            if condition.startswith("key."):
                execute = keys.get(condition.split(".")[1], False)
            else:
                error("Invalid if condition", line_no)

            skip_stack.append(not execute)
            i += 1
            continue

        if cmd == "}":
            i += 1
            continue

        # local var
        if cmd.startswith("local var "):
            n, v = cmd[10:].split("=", 1)
            local_vars[n.strip()] = eval_value(v, global_vars, local_vars)
            i += 1
            continue

        # global var
        if cmd.startswith("var "):
            n, v = cmd[4:].split("=", 1)
            global_vars[n.strip()] = eval_value(v, global_vars, local_vars)
            i += 1
            continue

        # math
        if "+=" in cmd:
            n, v = cmd.split("+=", 1)
            global_vars[n.strip()] += eval_value(v, global_vars, local_vars)
            i += 1
            continue

        if "-=" in cmd:
            n, v = cmd.split("-=", 1)
            global_vars[n.strip()] -= eval_value(v, global_vars, local_vars)
            i += 1
            continue

        if "=" in cmd:
            n, v = cmd.split("=", 1)
            global_vars[n.strip()] = eval_value(v, global_vars, local_vars)
            i += 1
            continue

        # image.draw
        if cmd.startswith("image.draw"):
            args = cmd.split("(")[1].rstrip(")").split(",")
            if len(args) < 6:
                error("image.draw requires 6 arguments", line_no)
            sprite_name = args[0].strip()
            x = eval_value(args[1], global_vars, local_vars)
            y = eval_value(args[2], global_vars, local_vars)
            sx = eval_value(args[3], global_vars, local_vars)
            sy = eval_value(args[4], global_vars, local_vars)
            rot = eval_value(args[5], global_vars, local_vars)
            if sprite_name not in loaded_assets:
                error(f"Asset '{sprite_name}' not loaded", line_no)
            draw_queue.append((
                loaded_assets[sprite_name],
                x, y, sx, sy, rot
            ))
            i += 1
            continue

        # shape.rect
        if cmd.startswith("shape.rect"):
            args = cmd.split("(")[1].rstrip(")").split(",")
            fill = eval_value(args[0], global_vars, local_vars)
            stroke = eval_value(args[1], global_vars, local_vars)
            strokewidth = eval_value(args[2], global_vars, local_vars)
            x = eval_value(args[3], global_vars, local_vars)
            y = eval_value(args[4], global_vars, local_vars)
            w = eval_value(args[5], global_vars, local_vars)
            h = eval_value(args[6], global_vars, local_vars)
            draw_queue.append({
                "type": "rect",
                "fill": fill,
                "stroke": stroke,
                "strokewidth": strokewidth,
                "x": x, "y": y,
                "w": w, "h": h
            })
            i += 1
            continue

        # shape.circle
        if cmd.startswith("shape.circle"):
            args = cmd.split("(")[1].rstrip(")").split(",")
            fill = eval_value(args[0], global_vars, local_vars)
            stroke = eval_value(args[1], global_vars, local_vars)
            strokewidth = eval_value(args[2], global_vars, local_vars)
            x = eval_value(args[3], global_vars, local_vars)
            y = eval_value(args[4], global_vars, local_vars)
            r = eval_value(args[5], global_vars, local_vars)
            draw_queue.append({
                "type": "circle",
                "fill": fill,
                "stroke": stroke,
                "strokewidth": strokewidth,
                "x": x, "y": y,
                "r": r
            })
            i += 1
            continue

        error(f"Unknown command '{cmd}'", line_no)
