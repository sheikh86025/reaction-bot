# Compatibility: lets the old start command `python3 -m PurviReaction` run the new bot.
import os
import runpy
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
runpy.run_path(os.path.join(ROOT, "main.py"), run_name="__main__")
