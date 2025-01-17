# Face and Hand Tracker

This program uses computer vision and machine learning to track faces, hands, and arms in real-time using your webcam. It utilizes MediaPipe for ML-powered tracking and OpenCV for webcam handling and visualization.

## Requirements
- Python 3.8+
- Webcam
- Required packages (listed in requirements.txt)

## Installation
1. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage
1. Run the tracker:
```bash
python tracker.py
```

2. The webcam feed will open with tracking overlay
3. Press 'q' to quit the application

## Features
- Real-time face tracking with mesh overlay
- Hand tracking with skeletal overlay
- Arm/pose tracking
- Smooth and efficient performance using MediaPipe's optimized ML models
