from xylo.interpreter import run_xylo
import sys

if len(sys.argv) != 2:
    print("Usage: python main.py game.xy")
    exit(1)

run_xylo(sys.argv[1])
