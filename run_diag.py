#!/usr/bin/env python3
"""Wrapper: set UTF-8 IO encoding then run diag_mic.py."""
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Now exec the actual script
import runpy
runpy.run_path(r"C:\Users\kitap\.openclaw\workspace\live2d-fork\diag_mic.py", run_name="__main__")
