from xylo.errors import error

global_vars = {}

def execute(assets, global_lines, functions):
    global global_vars
    global_vars = {}

    print("========================")

    # Execute global lines (vars + terminal.write)
    for line_no, cmd in global_lines:

        # terminal.write
        if cmd.startswith("terminal.write"):
            args = cmd.split("(", 1)[1].rstrip(")")
            output = args.strip()
            parts = [p.strip() for p in output.split("+")]
            final_output = ""
            for part in parts:
                if part.startswith('"') and part.endswith('"'):
                    final_output += part[1:-1]
                elif part in global_vars:
                    final_output += str(global_vars[part])
                else:
                    error(f"Unknown variable or invalid string '{part}'", line_no)
            print(final_output)
            continue

        # global var
        if cmd.startswith("var "):
            name_value = cmd[4:].split("=", 1)
            var_name = name_value[0].strip()
            value = name_value[1].strip()
            if var_name in global_vars:
                error(f"Global variable '{var_name}' already declared", line_no)
            global_vars[var_name] = value
            continue

    # Execute functions
    execute_function("init", functions, assets)
    execute_function("update", functions, assets)
    execute_function("draw", functions, assets)


def execute_function(name, functions, assets):
    local_vars = {}

    for line_no, cmd in functions[name]:

        # Local variable
        if cmd.startswith("local var "):
            name_value = cmd[10:].split("=", 1)
            var_name = name_value[0].strip()
            value = name_value[1].strip()
            if var_name in local_vars:
                error(f"Local variable '{var_name}' already declared", line_no)
            local_vars[var_name] = value
            continue

        # Global variable (plain var) — allowed inside functions
        if cmd.startswith("var "):
            name_value = cmd[4:].split("=", 1)
            var_name = name_value[0].strip()
            value = name_value[1].strip()
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

            # resolve current variable value
            if var_name in local_vars:
                current = local_vars[var_name]
            elif var_name in global_vars:
                current = global_vars[var_name]
            else:
                error(f"Variable '{var_name}' not declared", line_no)

            # resolve value
            if value in local_vars:
                val = local_vars[value]
            elif value in global_vars:
                val = global_vars[value]
            else:
                try:
                    val = int(value)
                except:
                    try:
                        val = float(value)
                    except:
                        val = value.strip('"')  # treat as string

            # perform math if possible
            if op:
                try:
                    current = float(current) if "." in str(current) else int(current)
                    val = float(val) if "." in str(val) else int(val)
                    if op == "+":
                        current += val
                    elif op == "-":
                        current -= val
                    elif op == "*":
                        current *= val
                    elif op == "/":
                        current /= val
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
            args = cmd.split("(", 1)[1].rstrip(")")
            output = args.strip()
            parts = [p.strip() for p in output.split("+")]
            final_output = ""
            for part in parts:
                if part.startswith('"') and part.endswith('"'):
                    final_output += part[1:-1]
                elif part in local_vars:
                    final_output += str(local_vars[part])
                elif part in global_vars:
                    final_output += str(global_vars[part])
                else:
                    error(f"Unknown variable or invalid string '{part}'", line_no)
            print(final_output)
            continue

        # Generic command
        print(f"[{name.upper()}] {cmd}")

