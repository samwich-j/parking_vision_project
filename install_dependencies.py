#!/usr/bin/env python3
"""
Dependency Installation Script for Parking Vision Project
Attempts to install required packages using different methods
"""

import subprocess
import sys
import os


def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_python():
    """Check Python version and available package managers"""
    print("🐍 Checking Python installation...")

    # Check Python version
    version = sys.version_info
    print(f"   Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ⚠️  Warning: Python 3.8+ recommended")
    else:
        print("   ✅ Python version OK")

    # Check for pip
    success, _, _ = run_command("python3 -m pip --version")
    if success:
        print("   ✅ pip available via python3 -m pip")
        return True

    success, _, _ = run_command("pip3 --version")
    if success:
        print("   ✅ pip3 available")
        return True

    success, _, _ = run_command("pip --version")
    if success:
        print("   ✅ pip available")
        return True

    print("   ❌ pip not found")
    return False


def install_basic_packages():
    """Install basic packages that are likely to work"""
    basic_packages = [
        "opencv-python",
        "numpy",
        "matplotlib",
        "Pillow",
        "PyYAML",
        "requests"
    ]

    print(f"\n📦 Attempting to install basic packages...")

    pip_commands = [
        "python3 -m pip install --user",
        "pip3 install --user",
        "pip install --user"
    ]

    for pip_cmd in pip_commands:
        print(f"   Trying: {pip_cmd}")
        success, stdout, stderr = run_command(f"{pip_cmd} {' '.join(basic_packages)}")

        if success:
            print("   ✅ Basic packages installed successfully!")
            return True
        else:
            print(f"   ❌ Failed: {stderr}")

    return False


def create_requirements_minimal():
    """Create a minimal requirements file for manual installation"""
    minimal_requirements = """# Minimal requirements that can be installed manually
# Essential packages
opencv-python
numpy
matplotlib
Pillow
PyYAML

# Optional packages (install if possible)
# yt-dlp
# ultralytics
# gspread
# pandas
# scikit-image
# tqdm
"""

    with open("requirements_minimal.txt", "w") as f:
        f.write(minimal_requirements)

    print("📝 Created requirements_minimal.txt with essential packages only")


def main():
    print("🚗 Parking Vision Project - Dependency Installation")
    print("=" * 50)

    # Check if we're in the right directory
    if not os.path.exists("requirements.txt"):
        print("❌ Error: requirements.txt not found. Are you in the project directory?")
        return

    # Check Python installation
    if not check_python():
        print("\n❌ pip not available. Please install pip first:")
        print("   Ubuntu/Debian: sudo apt install python3-pip")
        print("   Or follow: https://pip.pypa.io/en/stable/installation/")
        return

    # Try to install packages
    print(f"\n📦 Installing packages from requirements.txt...")

    pip_commands = [
        "python3 -m pip install --user -r requirements.txt",
        "pip3 install --user -r requirements.txt",
        "pip install --user -r requirements.txt"
    ]

    installed = False
    for pip_cmd in pip_commands:
        print(f"   Trying: {pip_cmd}")
        success, stdout, stderr = run_command(pip_cmd)

        if success:
            print("   ✅ All packages installed successfully!")
            installed = True
            break
        else:
            print(f"   ❌ Failed: {stderr}")

    if not installed:
        print(f"\n⚠️  Full installation failed. Trying basic packages...")
        if install_basic_packages():
            create_requirements_minimal()
            print(f"\n✅ Basic installation complete!")
            print(f"   You can manually install additional packages later")
        else:
            create_requirements_minimal()
            print(f"\n❌ Automatic installation failed.")
            print(f"   Please install packages manually:")
            print(f"   pip3 install --user opencv-python numpy matplotlib")

    # Test installation
    print(f"\n🧪 Testing core imports...")
    try:
        import cv2
        print(f"   ✅ OpenCV version: {cv2.__version__}")
    except ImportError:
        print(f"   ❌ OpenCV not available")

    try:
        import numpy as np
        print(f"   ✅ NumPy version: {np.__version__}")
    except ImportError:
        print(f"   ❌ NumPy not available")

    print(f"\n🎉 Setup complete! You can now run:")
    print(f"   python3 src/car_detector.py")
    print(f"   python3 src/parking_spot_definer.py <video_file>")


if __name__ == "__main__":
    main()