"""
Pygbag build script for Declare.
Run: python build_web.py
Then serve the build/ directory with any web server.
"""
import subprocess
import sys
import os

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("Building Declare for Web...")
    print("This may take several minutes on first run.")

    try:
        subprocess.run([sys.executable, "-m", "pygbag", "--title", "Declare", "--app-id", "com.declare.cardgame", "."])
        print("\nBuild complete! The 'build/' directory contains the web app.")
        print("To test locally, serve the build directory:")
        print("  python -m http.server 8000 -d build")
        print("Then open http://localhost:8000 in your browser.")
    except Exception as e:
        print(f"Build failed: {e}")
        print("Make sure pygbag is installed: pip install pygbag")

if __name__ == "__main__":
    main()