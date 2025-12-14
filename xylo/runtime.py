import time
from xylo.errors import error

global_vars = {}

# -----------------------
# Helper functions
# -----------------------

def eval_value(value, global_vars, local_vars):
    """Resolve a value: variable, number, or string literal"""
    value = value.strip()
    if value in local_vars:
        return local_vars[value]
    elif value in global_vars:
        return global_vars[value]
    else:
        try:
            return int(value)
        except:
            try:
                return float(value)
            except:
                if value.startswith('"') and value.endswith('"'):
                    return value[1:-1]
                else:
                    return value  # fallback as string

def parse_terminal_write(cmd, global_vars, local_vars):
    """Parse terminal.write and handle concatenation"""
    args = cmd.split("(", 1)[1].rstrip(")")
    output = args.strip()
    parts = [p.strip() for p in output.split("+")]
    final_output = ""
    for part in parts:
        val = eval_value(part, global_vars, local_vars)
        final_output += str(val)
    return final_output

# -----------------------
# Main execute function
# -----------------------

def execute(assets, global_lines, functions):
    global global_vars
    global_vars = {}

    FPS = 60
    dt = 1 / FPS  # seconds per frame

    print("== xylo started ==")

    # Execute global lines (vars + terminal.write)
    for line_no, cmd in global_lines:
        # terminal.write
        if cmd.startswith("terminal.write"):
            output = parse_terminal_write(cmd, global_vars, {})
            print(output)
            continue

        # global var
        if cmd.startswith("var "):
            name_value = cmd[4:].split("=", 1)
            var_name = name_value[0].strip()
            value = eval_value(name_value[1].strip(), global_vars, {})
            global_vars[var_name] = value
            continue

    # Main game loop
    try:
        while True:
            start = time.time()

            # Set delta time variable
            global_vars["dt"] = dt

            execute_function("update", functions, assets)
            execute_function("draw", functions, assets)

            # FPS limit
            elapsed = time.time() - start
            time.sleep(max(0, dt - elapsed))
    except KeyboardInterrupt:
        print("\n== xylo stopped ==")

# -----------------------
# Function executor
# -----------------------

def execute_function(name, functions, assets):
    local_vars = {}

    for line_no, cmd in functions[name]:

        # Local variable
        if cmd.startswith("local var "):
            name_value = cmd[10:].split("=", 1)
            var_name = name_value[0].strip()
            value = eval_value(name_value[1].strip(), global_vars, local_vars)
            if var_name in local_vars:
                error(f"Local variable '{var_name}' already declared", line_no)
            local_vars[var_name] = value
            continue

        # Global variable (plain var)
        if cmd.startswith("var "):
            name_value = cmd[4:].split("=", 1)
            var_name = name_value[0].strip()
            value = eval_value(name_value[1].strip(), global_vars, local_vars)
            if var_name in global_vars:
                error(f"Global variable '{var_name}' already declared", line_no)
            global_vars[var_name] = value
            continue

        # Assignment or augmented assignment
        if "=" in cmd:
            # detect augmented operator
            if "+=" in cmd:
                var_name, value = cmd.split("+=", 1)
                op = "+"
            elif "-=" in cmd:
                var_name, value = cmd.split("-=", 1)
                op = "-"
            elif "*=" in cmd:
                var_name, value = cmd.split("*=", 1)
                op = "*"
            elif "/=" in cmd:
                var_name, value = cmd.split("/=", 1)
                op = "/"
            else:
                var_name, value = cmd.split("=", 1)
                op = None

            var_name = var_name.strip()
            value = value.strip()

            # resolve current value
            if var_name in local_vars:
                current = local_vars[var_name]
            else:
                current = global_vars.get(var_name, 0)

            val = eval_value(value, global_vars, local_vars)

            # perform math if needed
            if op:
                try:
                    current = float(current) if isinstance(current, (int, float)) else current
                    val = float(val) if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace('.', '', 1).isdigit()) else val
                    if op == "+": current += val
                    elif op == "-": current -= val
                    elif op == "*": current *= val
                    elif op == "/": current /= val
                except:
                    error(f"Cannot perform operation {op} on {current} and {val}", line_no)
            else:
                current = val

            # store back
            if var_name in local_vars:
                local_vars[var_name] = current
            else:
                global_vars[var_name] = current
            continue

        # drawImage
        if cmd.startswith("drawImage"):
            if name != "draw":
                error("drawImage() only allowed in draw()", line_no)
            args = cmd.split("(")[1].replace(")", "").split(",")
            sprite = args[0].strip()
            if sprite not in assets:
                error(f"Sprite '{sprite}' not imported", line_no)
            if assets[sprite]["type"] != "sprite":
                error(f"Asset '{sprite}' is not a sprite", line_no)
            print(f"[DRAW] {sprite} -> {assets[sprite]['path']}")
            continue

        # terminal.write inside function
        if cmd.startswith("terminal.write"):
            output = parse_terminal_write(cmd, global_vars, local_vars)
            print(output)
            continue

        # Generic unknown command
        print(f"[{name.upper()}] {cmd}")
