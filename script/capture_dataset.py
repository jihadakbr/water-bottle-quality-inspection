import cv2
import os
from datetime import datetime, timezone, timedelta

# ========== CONFIGURATION ==========
# Change this for each capture session:
category = 'underfilled'  # Options: good, underfilled, no_cap, loose_cap, debris, damaged_label, wrong_bottle

# Create folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, '..', 'dataset')
categories = ['good', 'underfilled', 'no_cap', 'loose_cap',
              'debris', 'damaged_label', 'wrong_bottle']
for cat in categories:
    os.makedirs(os.path.join(DATASET_DIR, cat), exist_ok=True)

# ========== CAMERA SETUP ==========
# Logitech C270 = index 1 via DirectShow
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

# Disable auto-exposure for manual control
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # 1 = manual, 3 = auto

if not cap.isOpened():
    print("[ERROR] Cannot open camera!")
    exit()

# ========== CAMERA ADJUSTMENT TRACKBARS ==========
cv2.namedWindow('Camera Settings')

# Track which settings the user has touched
settings_changed = {'brightness': False, 'contrast': False, 'exposure': False, 'gain': False}

def on_brightness(x): settings_changed['brightness'] = True
def on_contrast(x):   settings_changed['contrast'] = True
def on_exposure(x):   settings_changed['exposure'] = True
def on_gain(x):       settings_changed['gain'] = True

# All sliders start at middle/zero — camera keeps its own defaults until we move a slider
cv2.createTrackbar('Brightness', 'Camera Settings', 102, 255, on_brightness)
cv2.createTrackbar('Contrast',   'Camera Settings', 28, 255, on_contrast)
cv2.createTrackbar('Exposure',   'Camera Settings', 0,   13,  on_exposure)   # Slider value = abs(exposure), so 6 → -6
cv2.createTrackbar('Gain',       'Camera Settings', 0,   255, on_gain)

# ========== CAPTURE LOOP ==========
count = 0
print("\n" + "="*60)
print(f"CAPTURING: {category.upper()}")
print("="*60)
print("Controls:")
print("  SPACEBAR = Capture image")
print("  Q = Quit")
print("="*60 + "\n")

while True:
    # Only apply settings the user has actually touched
    if settings_changed['brightness']:
        brightness = cv2.getTrackbarPos('Brightness', 'Camera Settings')
        cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
    if settings_changed['contrast']:
        contrast = cv2.getTrackbarPos('Contrast', 'Camera Settings')
        cap.set(cv2.CAP_PROP_CONTRAST, contrast)
    if settings_changed['exposure']:
        exposure = cv2.getTrackbarPos('Exposure', 'Camera Settings')
        cap.set(cv2.CAP_PROP_EXPOSURE, -(exposure))
    if settings_changed['gain']:
        gain = cv2.getTrackbarPos('Gain', 'Camera Settings')
        cap.set(cv2.CAP_PROP_GAIN, gain)

    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to grab frame")
        break

    # Keep a clean copy for saving
    clean_frame = frame.copy()

    # Get frame dimensions
    h, w = frame.shape[:2]
    center_x, center_y = w // 2, h // 2

    # Draw reference guides (on display frame only)
    cv2.line(frame, (center_x, 0), (center_x, h), (0, 255, 0), 2)
    cv2.line(frame, (0, center_y), (w, center_y), (0, 255, 0), 2)
    cv2.circle(frame, (center_x, center_y), 150, (0, 255, 0), 2)

    # Instructions overlay
    cv2.putText(frame, f"Category: {category}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Count: {count}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, "Center bottle in green circle", (20, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow('Dataset Capture - Ron 88 Production Grade', frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord(' '):
        timestamp = datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(DATASET_DIR, category, f'{category}_{count:04d}_{timestamp}.jpg')
        cv2.imwrite(filename, clean_frame)
        count += 1
        print(f'Saved: {filename}')
        
    elif key == ord('q'):
        break

# Save slider values before destroying windows
final_brightness = cv2.getTrackbarPos('Brightness', 'Camera Settings')
final_contrast   = cv2.getTrackbarPos('Contrast', 'Camera Settings')
final_exposure   = cv2.getTrackbarPos('Exposure', 'Camera Settings')
final_gain       = cv2.getTrackbarPos('Gain', 'Camera Settings')

cap.release()
cv2.destroyAllWindows()
print(f"\nSession complete! Total captured: {count} images")
print(f"\nFinal camera settings:")
print(f"   Brightness: {final_brightness}")
print(f"   Contrast:   {final_contrast}")
print(f"   Exposure:   -{final_exposure}")
print(f"   Gain:       {final_gain}\n")