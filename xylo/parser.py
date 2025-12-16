from xylo.errors import error

def parse_file(filename):
    assets = {}
    functions = {}
    global_vars = []
    current_func = None
    line_number = 0
    brace_depth = 0

    with open(filename, "r") as f:
        for raw in f:
            line_number += 1
            line = raw.strip()

            if not line:
                continue

            # ------------------------
            # Asset import
            # ------------------------
            if line.startswith("asset.import"):
                try:
                    before_type, asset_type = line.split(":")
                    inside = before_type.split("(")[1].replace(")", "")
                    name, path = [x.strip().replace('"', "") for x in inside.split(",")]

                    assets[name] = {
                        "type": asset_type.strip(),
                        "path": path
                    }
                except:
                    error("Invalid asset.import syntax", line_number)
                continue

            # ------------------------
            # Asset delete
            # ------------------------
            if line.startswith("asset.del"):
                name = line.split("(")[1].replace(")", "").replace('"', "")
                if name not in assets:
                    error(f"Asset '{name}' not found", line_number)
                del assets[name]
                continue

            # ------------------------
            # Function start
            # ------------------------
            if line.startswith("function") and line.endswith("{"):
                fname = line.split()[1].split("(")[0]
                functions[fname] = []
                current_func = fname
                brace_depth = 1
                continue

            # ------------------------
            # Inside function
            # ------------------------
            if current_func:
                if line.endswith("{"):
                    brace_depth += 1

                if line == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        current_func = None
                        continue

                functions[current_func].append((line_number, line))
                continue

            # ------------------------
            # Global variable
            # ------------------------
            if line.startswith("var ") and current_func is None:
                global_vars.append((line_number, line))
                continue

            # ------------------------
            # Terminal write (global allowed)
            # ------------------------
            if line.startswith("terminal.write") and current_func is None:
                global_vars.append((line_number, line))
                continue

            error("Code outside function", line_number)

    return assets, global_vars, functions
