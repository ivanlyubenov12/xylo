from xylo.errors import error

def parse_file(filename):
    assets = {}
    functions = {}
    global_lines = []   # includes global var and terminal.write
    current_func = None
    line_number = 0

    with open(filename, "r") as f:
        for raw in f:
            line_number += 1
            line = raw.strip()

            if not line:
                continue

            # Asset import
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

            # Asset delete
            if line.startswith("asset.del"):
                name = line.split("(")[1].replace(")", "").replace('"', "")
                if name not in assets:
                    error(f"Asset '{name}' not found", line_number)
                del assets[name]
                continue

            # Global var or terminal.write outside functions
            if current_func is None and (line.startswith("var ") or line.startswith("terminal.write")):
                global_lines.append((line_number, line))
                continue

            # Function start
            if line.startswith("function") and line.endswith("{"):
                fname = line.split()[1].split("(")[0]
                functions[fname] = []
                current_func = fname
                continue

            # Function end
            if line == "}":
                current_func = None
                continue

            # Inside function
            if current_func:
                functions[current_func].append((line_number, line))
            else:
                error("Code outside function", line_number)

    return assets, global_lines, functions
