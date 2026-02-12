# 🏭 Ron 88 Bottle Quality Inspection System

A production-grade conveyor belt quality inspection system using computer vision to detect defects in Ron 88 water bottles. The system uses YOLOv8s object detection to identify various defects and controls an Arduino-based servo mechanism to automatically reject defective bottles in real-time.

**Project Highlights:**
- 1,500 images collected and annotated entirely by myself using CVAT
- Trained on Kaggle (T4 GPU) using YOLOv8s (Small)
- Real-time detection across 7 classes with bounding box annotations
- Multi-defect capable: detects multiple issues on a single bottle simultaneously
- Arduino UNO + MG90S servo rejection system with calibrated timing
- Streamlit dashboard for production analytics

## 📺 Demo

[![YouTube Demo](https://img.shields.io/badge/YouTube-Demo-red?logo=youtube)](https://youtu.be/JA_5Sh8w96o?si=3z7rx-KOIAFZf6KR)

**Links:**
- **Training (Kaggle)**: [soon](#)
- **Dataset (Kaggle)**: [Water Bottle Defect-Level Detection Dataset](https://www.kaggle.com/datasets/jihadakbr/water-bottle-defect-level-detection-dataset)

> The dataset includes 1,500 annotated images with CVAT annotations. Feel free to use it for your own projects!

## Features

- **Real-time Defect Detection**: Detects multiple defect types including:
  - Low fill level
  - Missing cap
  - Loose cap
  - Debris contamination
  - Label damage
  - Wrong brand detection

- **Automated Rejection**: Arduino-controlled servo mechanism automatically pushes defective bottles off the conveyor belt

- **Production Monitoring**: Real-time statistics and quality metrics tracking

- **Interactive Dashboard**: Streamlit-based dashboard for viewing inspection reports and analytics

## System Components

### 1. Computer Vision Detection (`script/ron88_defect_production.py`)
- YOLO-based multi-class detection system
- Defect-level quality inspection
- Real-time frame processing with detection zones
- Multi-defect accumulation across frames
- Automatic CSV report generation

**Detection Strategy:**
- **Stage 1**: Detect bottle type (Ron 88 or other brand)
- **Stage 2**: Detect defects (supports multiple defects per bottle)
- **Decision**: PASS only if Ron 88 with NO defects

**Key Features:**
- Detection cooldown to prevent duplicate processing
- Frame accumulation for stable defect detection
- Persistent decision display
- Quality rate tracking
- Per-bottle logging with unique IDs

### 2. Dataset Capture Tool (`script/capture_dataset.py`)
- Interactive camera-based dataset collection
- Manual camera settings control (brightness, contrast, exposure, gain)
- Visual guides for consistent bottle positioning
- Organized dataset folder structure by defect category

**Supported Categories:**
- good
- underfilled
- no_cap
- loose_cap
- debris
- damaged_label
- wrong_bottle

### 3. Arduino Servo Control (`arduino/ron88_servo_control/`)
- Timed rejection mechanism
- Queued rejection system (handles up to 10 pending rejections)
- Configurable timing parameters:
  - Detection delay (time from camera to servo)
  - Push duration (how long servo stays active)
  - Cooldown period between rejections

**Commands:**
- `R` - Queue bottle rejection
- `G` - Log good bottle
- `S` - Display session statistics

### 4. Streamlit Dashboard (`streamlit/ron88_dashboard.py`)
- Session report viewer
- Visual analytics:
  - Pass/Reject pie chart
  - Defect breakdown bar chart
- Filterable inspection log
- Summary metrics display

## Dataset

**Total Images**: 1,500 images (all collected and annotated by myself)

**Annotation Tool**: CVAT (Computer Vision Annotation Tool)

**Annotation Strategy**: Defect-level detection with bounding boxes
- Each image contains multiple bounding boxes
- Stage 1: Entire bottle detection (brand identification)
- Stage 2: Specific defect localization (precise issue pinpointing)

**Distribution**:
- **Good Ron 88**: 600 images (no defects, proper quality)
- **Underfilled**: 250 images (various fill levels)
- **No Cap**: 150 images (missing cap completely)
- **Loose Cap**: 150 images (tilted, half-screwed, or cracked caps)
- **Debris**: 150 images (contamination)
- **Damaged Label**: 100 images (torn, crooked, peeled, missing labels)
- **Wrong Bottle**: 100 images (Golda, Coca Cola, other brands)

**Data Collection**:
- Fixed camera position (30-50cm overhead, perpendicular to belt)
- Consistent lighting setup
- Multiple bottle rotations for good coverage
- Various defect severities captured

**Annotation Format**: YOLO 1.1 format with bounding boxes

## Model

The system uses **YOLOv8s (Small)** trained on Kaggle with T4 GPU.

**Two-Stage Detection Approach:**

**Stage 1: Bottle Detection & Brand Classification**
- `bottle_ron88` (class 0) - Detects entire Ron 88 bottle
- `bottle_other_brand` (class 1) - Detects non-Ron 88 bottles (wrong brand)

**Stage 2: Defect Detection & Localization**
- `defect_low_fill` (class 2) - Water level below acceptable threshold
- `defect_no_cap` (class 3) - Bottle neck/cap area missing cap
- `defect_loose_cap` (class 4) - Cap tilted, half-screwed, or damaged
- `defect_debris` (class 5) - Contamination spots (can detect multiple per bottle)
- `defect_label_damage` (class 6) - Torn, crooked, or missing label

**Detection Thresholds:**
- Bottle confidence: 0.70 (higher threshold for bottle detection)
- Defect confidence: 0.60 (slightly lower for defect sensitivity)

**Model Files:**
- `model/best.pt` - PyTorch model (used in production)
- `model/best.onnx` - ONNX format (for edge deployment)

**Training Platform**: Kaggle (NVIDIA Tesla T4 GPU)

**Key Capabilities:**
- **Multi-defect detection**: Single bottle can have multiple defects detected simultaneously
- **Frame accumulation**: Collects defects across 5 frames before final decision
- **Brand discrimination**: Rejects any non-Ron 88 bottles regardless of quality

## Inference Results

The system automatically generates CSV reports in `inference_result/`:

**Per-bottle report** (`report_YYYYMMDD_HHMMSS.csv`):
- Bottle ID (unique timestamp-based ID)
- Timestamp
- Bottle number
- Result (PASS/REJECT)
- Bottle type
- Defects detected

**Session summary** (`summary_YYYYMMDD_HHMMSS.csv`):
- Session date and duration
- Total inspected
- Good Ron 88 count
- Rejected count
- Quality rate percentage
- Defect breakdown by type
- Multi-defect bottle count

## Equipment & Hardware

### Conveyor Belt Construction
The conveyor belt was built manually using:
- Blackboard frame (base structure)
- Stainless steel rails
- PVC pipes (rollers)
- Bearings
- Motorcycle seat cover material (belt fabric)
- Acrylic lane divider (to separate good/reject lanes)
- JGY-370 DC Gearbox Motor (30 RPM, 7.4 kg.cm torque, 12V)
- 12V Power Supply

### Computer Vision & Control
- Logitech C270 HD 720p Webcam (fixed overhead position)
- Arduino UNO (microcontroller for servo control)
- MG90S Servo Motor (2.2 kg/cm torque, 6.6V)
- Laptop/Computer for inference

### Wiring Diagram
```
MG90S Servo (3 wires):
├─ Signal (Orange) ──→ Arduino Pin 9
├─ VCC (Red)       ──→ Arduino 5V
└─ GND (Brown)     ──→ Arduino GND

Arduino:
├─ Pin 9   ──→ Servo Signal (Orange)
├─ 5V      ──→ Servo VCC (Red)
├─ GND     ──→ Servo GND (Brown)
└─ USB     ──→ Computer (for serial communication)
```

## Requirements

### Python Dependencies
```bash
pip install ultralytics opencv-python pyserial streamlit pandas plotly
```

**Required packages:**
- `opencv-python` (cv2) - Camera capture and image processing
- `ultralytics` - YOLOv8 object detection
- `pyserial` - Arduino serial communication
- `streamlit` - Dashboard web interface
- `pandas` - Data handling
- `plotly` - Interactive charts

## Usage

### 1. Capture Dataset
```bash
python script/capture_dataset.py
```
- Set the `category` variable in the script
- Press SPACEBAR to capture images
- Press Q to quit

### 2. Run Production Inspection
```bash
python script/ron88_defect_production.py
```
- Configure `MODEL_PATH` and `ARDUINO_PORT`
- Press Q to quit
- Press R to reset statistics
- Press S to view statistics

### 3. View Dashboard
```bash
streamlit run streamlit/ron88_dashboard.py
```
- Select inspection session from sidebar
- View metrics and analytics
- Filter inspection log by result

## Configuration

### Detection System
- Adjust confidence thresholds in `ron88_defect_production.py`:
  - `BOTTLE_CONFIDENCE`: Threshold for bottle detection (default: 0.70)
  - `DEFECT_CONFIDENCE`: Threshold for defect detection (default: 0.60)
  - `DETECTION_COOLDOWN`: Seconds between detections (default: 2.5)
  - `ACCUMULATION_FRAMES`: Frames to collect before decision (default: 5)

### Arduino Timing
- Adjust in `ron88_servo_control.ino`:
  - `DETECTION_DELAY`: Time from detection to servo activation (calculate based on belt speed)
  - `PUSH_DURATION`: How long servo pushes (default: 1000ms)
  - `COOLDOWN`: Wait time after rejection (default: 100ms)

## System Workflow

The complete detection and rejection workflow:

```
1. Logitech C270 HD 720p webcam captures frames from fixed overhead position
                              ↓
2. Python processes each frame through YOLOv8s model
   - Detects bottles (Ron 88 vs other brands)
   - Classifies defects with bounding boxes
                              ↓
3. Decision logic determines PASS or REJECT
   - PASS: Ron 88 bottle with NO defects
   - REJECT: Wrong brand OR Ron 88 with defects
                              ↓
4. Serial command sent to Arduino UNO
   - 'G' = Good (pass through)
   - 'R' = Reject (activate servo)
                              ↓
5. Arduino triggers MG90S servo after calibrated delay
   - Delay calculated: (distance / belt_speed) × 1000 ms
   - Accounts for time between detection and servo position
                              ↓
6. Servo pushes defective bottles off main lane
   - Push duration: 1000ms (configurable)
   - Returns to normal position automatically
                              ↓
7. Each bottle logged to CSV with unique ID
   - Timestamp, result, defects detected
   - Viewable through Streamlit dashboard
```

## System Architecture

```
┌─────────────┐
│   Webcam    │ (USB)
│  C270 720p  │
└──────┬──────┘
       │ Video frames
       ▼
┌─────────────────────────────┐
│   Laptop / Computer         │
│  ┌────────────────────────┐ │
│  │ ron88_defect_          │ │
│  │ production.py          │ │
│  │                        │ │
│  │ - OpenCV capture       │ │
│  │ - YOLOv8s inference    │ │
│  │ - Multi-defect logic   │ │
│  │ - CSV logging          │ │
│  └───────┬────────────────┘ │
└──────────┼──────────────────┘
           │ Serial USB
           │ Commands: 'R' / 'G'
           ▼
    ┌──────────────┐
    │  Arduino UNO │
    │              │
    │ - Serial RX  │
    │ - Timing     │
    │ - Queue      │
    └──────┬───────┘
           │ PWM (Pin 9)
           ▼
    ┌──────────────┐
    │ MG90S Servo  │
    │  2.2kg/cm    │
    │              │
    │ Rejection    │
    │ Mechanism    │
    └──────────────┘
           │
           ▼
    Defective bottles
    pushed to reject lane



Reports & Analytics:
┌─────────────────┐
│ inference_result│
│  - CSV logs     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Streamlit       │
│ Dashboard       │
│  - Metrics      │
│  - Charts       │
│  - Filter log   │
└─────────────────┘
```

## Tools & Technologies

**Computer Vision & ML:**
- Python 3.x
- OpenCV (cv2) - Image processing and camera capture
- Ultralytics YOLOv8s - Object detection model
- CVAT (cvat.ai) - Dataset annotation platform
- Kaggle - Model training platform (Tesla T4 GPU)

**Hardware & Control:**
- Arduino IDE - Arduino programming
- PySerial - Serial communication Python library
- Arduino UNO - Microcontroller
- MG90S Servo Motor (2.2kg/cm, 6.6V)
- Logitech C270 HD 720p Webcam

**Dashboard & Analytics:**
- Streamlit - Interactive web dashboard
- Plotly - Data visualization and charts
- Pandas - Data manipulation

**Mechanical:**
- JGY-370 DC Gearbox Motor (30 RPM, 12V)
- 12V Power Supply
- Custom conveyor belt (blackboard frame, stainless steel, PVC pipes, bearings)
