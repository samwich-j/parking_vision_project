# Parking Vision Project Setup Guide

## Prerequisites

You'll need to install Python dependencies before running this project. Here's how to set it up:

### 1. Install System Dependencies

On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3-pip python3-venv
```

On other systems, follow the [pip installation guide](https://pip.pypa.io/en/stable/installation/).

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Packages

```bash
pip install -r requirements.txt
```

If the full installation fails, try installing minimal packages:
```bash
pip install opencv-python numpy matplotlib Pillow PyYAML
```

### 4. Test Installation

```bash
python3 install_dependencies.py
```

## Quick Start

### 1. Download Test Videos
```bash
python3 src/video_downloader.py
```

### 2. Define Parking Spots
```bash
python3 src/parking_spot_definer.py data/videos/your_video.mp4
```

### 3. Run Parking Monitor
```bash
python3 src/parking_monitor.py --video data/videos/your_video.mp4 --spots data/configs/your_video_spots.json
```

## Project Structure

```
parking_vision/
├── src/                    # Source code
│   ├── car_detector.py     # Vehicle detection
│   ├── parking_spot_definer.py  # Interactive spot definition
│   ├── parking_monitor.py      # Main monitoring system
│   └── video_downloader.py     # Test video downloader
├── data/                   # Data directory
│   ├── videos/            # Video files
│   ├── configs/           # Parking spot configurations
│   └── test_images/       # Test images
├── output/                # Output directory
│   ├── results/           # Detection results
│   ├── logs/              # Log files
│   └── sheets/            # Google Sheets exports
├── docs/                  # Documentation
├── config/                # Configuration files
└── tests/                 # Test files
```

## Usage Examples

### For Beginners

1. **Download a test video:**
   ```bash
   python3 src/video_downloader.py
   ```

2. **Define parking spots on your video:**
   ```bash
   python3 src/parking_spot_definer.py data/videos/parking_lot.mp4
   ```
   - Left-click to add corner points
   - Right-click to complete each spot
   - Press 'n' for normal spots, 'e' for electric, 'r' for reserved
   - Press 's' to save your configuration

3. **Run the monitoring system:**
   ```bash
   python3 src/parking_monitor.py --video data/videos/parking_lot.mp4 --spots data/configs/parking_lot_spots.json
   ```

## Troubleshooting

### Common Issues

1. **"No module named cv2"** - Install OpenCV:
   ```bash
   pip install opencv-python
   ```

2. **"Permission denied"** - Use --user flag:
   ```bash
   pip install --user opencv-python
   ```

3. **Video won't open** - Check supported formats:
   - MP4, AVI, MOV are recommended
   - Make sure file path is correct

### Getting Help

- Check the documentation in `docs/`
- Run `python3 install_dependencies.py` to test your setup
- Look at example configurations in `data/configs/`

## Features

- ✅ Real-time vehicle detection
- ✅ Interactive parking spot definition
- ✅ Support for different spot types (normal, electric, reserved)
- ✅ Orange cone detection for temporary reservations
- ✅ Weather-resistant detection
- ✅ Google Sheets integration for real-time updates
- ✅ JSON output for mobile app integration
- ✅ Beginner-friendly with step-by-step guides