import sys

def error(msg, line=None):
    if line is not None:
        print(f"[xylo error] Line {line}: {msg}")
    else:
        print(f"[xylo error] {msg}")
    sys.exit(1)
