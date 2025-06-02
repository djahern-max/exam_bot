#!/usr/bin/env python3
"""
Setup script for building macOS app bundle
Usage: python setup.py py2app
"""

from setuptools import setup
import py2app
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Main Python file to convert to app
APP = ['src/main.py']

# Any additional files your app needs
DATA_FILES = []

# Configuration for py2app
OPTIONS = {
    'argv_emulation': True,  # Allows drag-and-drop onto app icon
    'iconfile': None,        # You can add an .icns icon file here later
    'plist': {
        'CFBundleName': 'Exam Bot',
        'CFBundleDisplayName': 'Exam Bot',
        'CFBundleGetInfoString': "Automated Multiple Choice Exam Solver v1.0",
        'CFBundleIdentifier': 'com.exambot.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,  # Support for Retina displays
    },
    # Include the packages your app uses
    'packages': ['selenium', 'webdriver_manager'],
    'includes': ['tkinter', 'threading', 'queue', 'time', 're'],
    'excludes': ['matplotlib', 'numpy', 'pandas'],  # Exclude heavy packages we don't need
    'optimize': 1,  # Optimize Python bytecode
}

setup(
    name='ExamBot',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'selenium>=4.15.0',
        'webdriver-manager>=4.0.1',
    ],
)
