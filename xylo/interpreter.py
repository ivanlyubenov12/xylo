from xylo.parser import parse_file
from xylo.runtime import execute
from xylo.errors import error

REQUIRED_FUNCS = {"init", "update", "draw"}

def run_xylo(filename):
    if not filename.endswith(".xy"):
        error("File must have .xy extension")

    assets, global_lines, functions = parse_file(filename)

    for fn in REQUIRED_FUNCS:
        if fn not in functions:
            error(f"Missing required function: {fn}()")

    execute(assets, global_lines, functions)
