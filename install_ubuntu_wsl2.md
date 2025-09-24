# Ubuntu WSL2 Installation Guide

Since this is Ubuntu on WSL2, you'll need to install some system dependencies first. Here are the complete installation steps:

## Step 1: Install System Dependencies

Open a WSL2 terminal and run:

```bash
# Update package list
sudo apt update

# Install Python development tools and pip
sudo apt install -y python3-pip python3-venv python3-dev

# Install system dependencies for OpenCV
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1

# Install additional dependencies for video processing
sudo apt install -y libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev libavfilter-dev

# Install git if not already installed
sudo apt install -y git
```

## Step 2: Install Python Dependencies

After installing pip, run our dependency installer:

```bash
# Navigate to project directory
cd parking_vision

# Install Python packages
python3 -m pip install --user -r requirements.txt
```

## Step 3: Alternative Manual Installation

If the automatic installation fails, install core packages manually:

```bash
# Essential packages
python3 -m pip install --user opencv-python numpy matplotlib Pillow PyYAML

# Video processing
python3 -m pip install --user yt-dlp

# Optional: Machine learning (large download)
python3 -m pip install --user ultralytics torch torchvision

# Optional: Google Sheets integration
python3 -m pip install --user gspread google-auth google-auth-oauthlib
```

## Step 4: Test Installation

```bash
python3 install_dependencies.py
```

## Step 5: WSL2 Specific Notes

### Display Issues
If you encounter display issues when running the GUI components:

```bash
# Install X11 forwarding (if using GUI)
sudo apt install -y x11-apps

# Set display variable (add to ~/.bashrc)
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
```

### Windows Integration
You can access your project files from Windows at:
```
\\wsl$\Ubuntu\home\sam\parking_vision\
```

## Troubleshooting

### "Permission denied" errors
Use `--user` flag with pip:
```bash
python3 -m pip install --user package_name
```

### "No module named cv2" after installation
```bash
python3 -m pip uninstall opencv-python
python3 -m pip install --user opencv-python-headless
```

### Video codec issues
```bash
sudo apt install -y ubuntu-restricted-extras
```

Once you've completed these steps, continue with:
```bash
# Download test videos
python3 src/video_downloader.py

# Test the system
python3 src/car_detector.py
```