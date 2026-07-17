#!/usr/bin/env python3
"""
Bible Reference App - Debug Wrapper
This script runs the app and catches any errors for debugging
"""

import sys
import traceback
from pathlib import Path

def main():
    try:
        print("=" * 60)
        print("Bible Reference Study Tool - Debug Mode")
        print("=" * 60)
        print()
        
        # Import the main app
        print("[*] Loading application modules...")
        from bible_reference_app import BibleReferenceApp
        
        print("[*] Initializing application...")
        app = BibleReferenceApp()
        
        print("[*] Starting main loop...")
        print("[✓] Application started successfully!")
        print()
        print("If the app doesn't appear, check that you have all required")
        print("Bible data files in the data/ directory.")
        print()
        
        app.mainloop()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR: Application failed to start!")
        print("=" * 60)
        print()
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print()
        print("Full Traceback:")
        print("-" * 60)
        traceback.print_exc()
        print("-" * 60)
        print()
        print("Please check:")
        print("1. Do you have Python 3.7+ installed?")
        print("2. Do you have tkinter installed?")
        print("3. Is the bible_reference_app.py file in the same directory?")
        print("4. Do you have required data files in the data/ folder?")
        print()
        input("Press Enter to close this window...")
        sys.exit(1)

if __name__ == "__main__":
    main()
