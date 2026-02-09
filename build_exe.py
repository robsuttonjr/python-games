"""
Build script for Dungeon Crawl 4 - creates standalone executable for itch.io
Usage:
    python build_exe.py

Requirements:
    pip install pyinstaller pygame numpy

Creates a folder in dist/DungeonCrawl4/ - zip it up and upload to itch.io.
Players unzip and run DungeonCrawl4.exe (or DungeonCrawl4 on Mac/Linux).

Build on each target platform (Windows for .exe, macOS for .app, Linux for binary).
"""
import PyInstaller.__main__
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
game_file = os.path.join(script_dir, "Dungeon Crawl 4.py")

PyInstaller.__main__.run([
    game_file,
    "--windowed",
    "--name=DungeonCrawl4",
    "--noconfirm",
    "--clean",
    "--hidden-import=numpy",
    "--hidden-import=pygame",
    "--hidden-import=pygame.sndarray",
])
