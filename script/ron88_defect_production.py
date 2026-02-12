# RON 88 DEFECT-LEVEL QUALITY INSPECTION

import cv2
from ultralytics import YOLO
import serial
import time
import sys
import csv
import os
from datetime import datetime, timezone, timedelta

# ========== CONFIGURATION ==========
MODEL_PATH = 'C:\\Users\\jihad\\D\\! All\\! Project\\23. Conveyor Belt\\model\\best.pt'
ARDUINO_PORT = 'COM7'  # Change to your port

# Detection thresholds
BOTTLE_CONFIDENCE = 0.70      # NOTE: For bottle detection (class 0, 1)
DEFECT_CONFIDENCE = 0.60      # NOTE: For defect detection (class 2-6)

# Class definitions (must match training)
CLASS_NAMES = {
    0: 'bottle_ron88',
    1: 'bottle_other_brand',
    2: 'defect_low_fill',
    3: 'defect_no_cap',
    4: 'defect_loose_cap',
    5: 'defect_debris',
    6: 'defect_label_damage'
}

BOTTLE_CLASSES = [0, 1]  # Bottle detection classes
DEFECT_CLASSES = [2, 3, 4, 5, 6]  # Defect detection classes

# Detection zone
ZONE_WIDTH = 400
ZONE_HEIGHT = 650

# Timing
DETECTION_COOLDOWN = 2.5  # Seconds between bottle detections
ACCUMULATION_FRAMES = 5   # Number of frames to accumulate defects before deciding

# ========== CAMERA SETUP ==========
print("="*70)
print(" RON 88 PRODUCTION-GRADE INSPECTION SYSTEM")
print("="*70)
print("\n Initializing camera...")

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("[ERROR] ERROR: Cannot open camera!")
    sys.exit(1)

ret, frame = cap.read()
if not ret:
    print("[ERROR] ERROR: Cannot read from camera!")
    sys.exit(1)

FRAME_HEIGHT, FRAME_WIDTH = frame.shape[:2]
CENTER_X, CENTER_Y = FRAME_WIDTH // 2, FRAME_HEIGHT // 2

ZONE_X1 = CENTER_X - ZONE_WIDTH // 2
ZONE_X2 = CENTER_X + ZONE_WIDTH // 2
ZONE_Y1 = 0
ZONE_Y2 = ZONE_HEIGHT

print(f"[OK] Camera: {FRAME_WIDTH}x{FRAME_HEIGHT} @ {cap.get(cv2.CAP_PROP_FPS)} FPS")

# ========== MODEL SETUP ==========
print(f"\n Loading defect-level detection model...")

try:
    model = YOLO(MODEL_PATH)
    print("[OK] Model loaded!")
    print(f"   Classes: {list(CLASS_NAMES.values())}")
except Exception as e:
    print(f"[ERROR] ERROR: {e}")
    sys.exit(1)

# ========== ARDUINO SETUP ==========
print(f"\n Connecting to Arduino on {ARDUINO_PORT}...")

arduino = None
try:
    arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)
    time.sleep(2)
    print("[OK] Arduino connected!")
    time.sleep(0.5)
    while arduino.in_waiting:
        print(f"   {arduino.readline().decode().strip()}")
except Exception as e:
    print(f"[WARN] WARNING: {e}")
    print("   Running in TEST MODE")
    arduino = None

# ========== STATISTICS ==========
total_bottles = 0
good_ron88 = 0
rejected_bottles = 0
wrong_brand_count = 0
last_detection_time = 0
session_start_time = time.time()

# Defect counters
defect_stats = {
    'low_fill': 0,
    'no_cap': 0,
    'loose_cap': 0,
    'debris': 0,
    'label_damage': 0
}

# Multi-defect tracking
multi_defect_bottles = 0

# Per-bottle log: each entry is a dict with bottle_id, timestamp, result, bottle_type, defects
bottle_log = []

def generate_bottle_id():
    """Generate bottle ID based on current timestamp (WIB, down to second)"""
    now = datetime.now(timezone(timedelta(hours=7)))
    return now.strftime("BTL-%Y%m%d-%H%M%S")

# Accumulation state: collect defects across multiple frames before deciding
accumulating = False
accum_frame_count = 0
accum_bottle_type = None
accum_defects = set()

# Persistent decision display
last_decision_text = ""
last_decision_color = (255, 255, 255)

# ========== HELPER FUNCTIONS ==========

def is_in_zone(box_center_x, box_center_y):
    """Check if detection is in the detection zone"""
    return (ZONE_X1 <= box_center_x <= ZONE_X2 and
            ZONE_Y1 <= box_center_y <= ZONE_Y2)

def get_box_center(box):
    """Get center coordinates of bounding box"""
    x1, y1, x2, y2 = map(int, box.xyxy[0])
    return (x1 + x2) // 2, (y1 + y2) // 2

def analyze_detections(results):
    """
    Analyze all detections in frame
    Returns: bottle_type, defects_list, all_boxes_data
    """
    bottle_type = None
    defects = []
    all_boxes = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            center_x, center_y = get_box_center(box)

            # Check if in detection zone
            if not is_in_zone(center_x, center_y):
                continue

            # Store box data
            box_data = {
                'class_id': class_id,
                'class_name': CLASS_NAMES[class_id],
                'confidence': confidence,
                'bbox': (x1, y1, x2, y2),
                'center': (center_x, center_y)
            }
            all_boxes.append(box_data)

            # Categorize detection
            if class_id in BOTTLE_CLASSES:
                if confidence >= BOTTLE_CONFIDENCE:
                    bottle_type = class_id
            elif class_id in DEFECT_CLASSES:
                if confidence >= DEFECT_CONFIDENCE:
                    defects.append(class_id)

    return bottle_type, defects, all_boxes

def draw_detections(frame, boxes_data):
    """Draw all bounding boxes with appropriate colors"""
    for box_data in boxes_data:
        class_id = box_data['class_id']
        class_name = box_data['class_name']
        confidence = box_data['confidence']
        x1, y1, x2, y2 = box_data['bbox']

        # Color coding
        if class_id == 0:  # Ron 88 bottle
            color = (0, 255, 0)  # Green
            thickness = 3
        elif class_id == 1:  # Other brand
            color = (0, 0, 255)  # Red
            thickness = 3
        else:  # Defects
            color = (0, 165, 255)  # Orange
            thickness = 2

        # Draw box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        # Label
        label = f'{class_name.replace("bottle_", "").replace("defect_", "")}'
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]

        # Background for text
        cv2.rectangle(frame, (x1, y1 - label_size[1] - 8),
                     (x1 + label_size[0], y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 4),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Confidence
        cv2.putText(frame, f'{confidence:.2f}', (x1, y2 + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

# ========== MAIN LOOP ==========
print("\n" + "="*70)
print(" PRODUCTION SYSTEM ACTIVE")
print("="*70)
print("Detection Strategy:")
print("  - Stage 1: Detect bottle (Ron 88 or other brand)")
print("  - Stage 2: Detect defects (multi-box capable)")
print("  - Decision: PASS only if Ron 88 with NO defects")
print("\nControls: Q=Quit | R=Reset | S=Stats")
print("="*70 + "\n")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Draw crosshair at center
        cross_size = 20
        cv2.line(frame, (CENTER_X - cross_size, CENTER_Y), (CENTER_X + cross_size, CENTER_Y), (0, 255, 0), 2)
        cv2.line(frame, (CENTER_X, CENTER_Y - cross_size), (CENTER_X, CENTER_Y + cross_size), (0, 255, 0), 2)

        # Draw detection zone
        cv2.rectangle(frame, (ZONE_X1, ZONE_Y1), (ZONE_X2, ZONE_Y2),
                     (255, 255, 0), 3)
        cv2.putText(frame, "INSPECTION ZONE", (ZONE_X1, ZONE_Y1 - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        # Run detection
        results = model.predict(frame, conf=0.3, verbose=False)  # Low conf, filter later

        # Analyze detections
        current_time = time.time()
        bottle_type, defects, all_boxes = analyze_detections(results)

        # Draw all detections
        draw_detections(frame, all_boxes)

        # Start accumulation when bottle detected (with cooldown)
        if bottle_type is not None and not accumulating and (current_time - last_detection_time) > DETECTION_COOLDOWN:
            accumulating = True
            accum_frame_count = 0
            accum_bottle_type = bottle_type
            accum_defects = set()

        # Accumulate defects across frames
        if accumulating:
            if bottle_type is not None:
                accum_bottle_type = bottle_type
            for d in defects:
                accum_defects.add(d)
            accum_frame_count += 1

        # Make decision after accumulating enough frames
        if accumulating and accum_frame_count >= ACCUMULATION_FRAMES:
            accumulating = False
            last_detection_time = current_time
            total_bottles += 1

            is_ron88 = (accum_bottle_type == 0)
            final_defects = sorted(accum_defects)

            bottle_id = generate_bottle_id()
            bottle_timestamp = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")

            if not is_ron88:
                # Wrong brand - always reject
                rejected_bottles += 1
                wrong_brand_count += 1

                if arduino:
                    arduino.write(b'R')
                    arduino.flush()

                bottle_log.append({
                    'bottle_id': bottle_id,
                    'timestamp': bottle_timestamp,
                    'bottle_number': total_bottles,
                    'result': 'REJECT',
                    'bottle_type': 'other_brand',
                    'defects': 'WRONG_BRAND'
                })

                print(f"[REJECT] {bottle_id} | WRONG BRAND (not Ron 88)")

                last_decision_text = "WRONG BRAND - REJECT"
                last_decision_color = (0, 0, 255)

            elif len(final_defects) > 0:
                # Ron 88 but has defects - reject
                rejected_bottles += 1

                # Count defects (unique only)
                defect_names = []
                for defect_id in final_defects:
                    if defect_id == 2:
                        defect_stats['low_fill'] += 1
                        defect_names.append('LOW_FILL')
                    elif defect_id == 3:
                        defect_stats['no_cap'] += 1
                        defect_names.append('NO_CAP')
                    elif defect_id == 4:
                        defect_stats['loose_cap'] += 1
                        defect_names.append('LOOSE_CAP')
                    elif defect_id == 5:
                        defect_stats['debris'] += 1
                        defect_names.append('DEBRIS')
                    elif defect_id == 6:
                        defect_stats['label_damage'] += 1
                        defect_names.append('LABEL_DMG')

                # Track multi-defect bottles
                if len(final_defects) > 1:
                    multi_defect_bottles += 1

                if arduino:
                    arduino.write(b'R')
                    arduino.flush()

                defect_str = ' + '.join(defect_names)

                bottle_log.append({
                    'bottle_id': bottle_id,
                    'timestamp': bottle_timestamp,
                    'bottle_number': total_bottles,
                    'result': 'REJECT',
                    'bottle_type': 'ron88',
                    'defects': defect_str
                })

                print(f"[REJECT] {bottle_id} | Ron88 DEFECTS ({defect_str})")

                last_decision_text = f"DEFECT: {defect_str}"
                last_decision_color = (0, 0, 255)

            else:
                # Perfect Ron 88 - pass
                good_ron88 += 1

                if arduino:
                    arduino.write(b'G')
                    arduino.flush()

                bottle_log.append({
                    'bottle_id': bottle_id,
                    'timestamp': bottle_timestamp,
                    'bottle_number': total_bottles,
                    'result': 'PASS',
                    'bottle_type': 'ron88',
                    'defects': ''
                })

                print(f"[OK] {bottle_id} | Perfect Ron 88 (PASS #{good_ron88})")

                last_decision_text = "RON 88 - PASS"
                last_decision_color = (0, 255, 0)

        # ========== STATISTICS OVERLAY ==========
        # Status indicator
        status_color = (0, 255, 0) if arduino else (0, 100, 255)
        status = "ACTIVE" if arduino else "TEST MODE"

        # Calculate panel height dynamically
        panel_h = 330
        overlay = frame.copy()
        cv2.rectangle(overlay, (8, 8), (320, panel_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        cv2.rectangle(frame, (8, 8), (320, panel_h), (80, 80, 80), 1)

        y = 32
        gap = 24

        # Title + status
        cv2.putText(frame, "RON 88 QC", (18, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(frame, status, (200, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2)
        y += gap + 8

        # Separator
        cv2.line(frame, (18, y - 6), (310, y - 6), (80, 80, 80), 1)

        # Main stats
        cv2.putText(frame, f"Total:       {total_bottles}", (18, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        y += gap

        cv2.putText(frame, f"Good:        {good_ron88}", (18, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
        y += gap

        cv2.putText(frame, f"Rejected:    {rejected_bottles}", (18, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 1)
        y += gap

        if total_bottles > 0:
            quality_rate = (good_ron88 / total_bottles) * 100
            q_color = (0, 255, 0) if quality_rate >= 90 else (0, 165, 255) if quality_rate >= 70 else (0, 0, 255)
            cv2.putText(frame, f"Quality:     {quality_rate:.1f}%", (18, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.55, q_color, 1)
        y += gap + 4

        # Separator
        cv2.line(frame, (18, y - 6), (310, y - 6), (80, 80, 80), 1)

        # Defect breakdown (compact)
        cv2.putText(frame, "Defects:", (18, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        y += gap - 2

        defect_items = [
            (f"Brand:  {wrong_brand_count}", (255, 100, 100)),
            (f"Fill:   {defect_stats['low_fill']}", (255, 150, 100)),
            (f"NoCap:  {defect_stats['no_cap']}", (255, 150, 100)),
            (f"Loose:  {defect_stats['loose_cap']}", (255, 150, 100)),
            (f"Debris: {defect_stats['debris']}", (255, 150, 100)),
            (f"Label:  {defect_stats['label_damage']}", (255, 150, 100)),
        ]

        # Render defects in 2 columns
        for i, (text, color) in enumerate(defect_items):
            col_x = 18 if i % 2 == 0 else 170
            row_y = y + (i // 2) * (gap - 2)
            cv2.putText(frame, text, (col_x, row_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

        # Decision status (bottom-right, persistent)
        if last_decision_text:
            text_size = cv2.getTextSize(last_decision_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3)[0]
            text_x = FRAME_WIDTH - text_size[0] - 20
            text_y = FRAME_HEIGHT - 25
            # Background for readability
            dec_overlay = frame.copy()
            cv2.rectangle(dec_overlay, (text_x - 10, text_y - text_size[1] - 10),
                         (FRAME_WIDTH - 5, text_y + 10), (0, 0, 0), -1)
            cv2.addWeighted(dec_overlay, 0.3, frame, 0.7, 0, frame)
            cv2.putText(frame, last_decision_text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, last_decision_color, 3)

        # Display
        cv2.imshow('Ron 88 Production Quality Control', frame)

        # Controls
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('r'):
            total_bottles = 0
            good_ron88 = 0
            rejected_bottles = 0
            wrong_brand_count = 0
            defect_stats = {k: 0 for k in defect_stats}
            multi_defect_bottles = 0
            bottle_log = []
            accumulating = False
            accum_frame_count = 0
            accum_defects = set()
            last_decision_text = ""
            print("\n Statistics reset!\n")
        elif key == ord('s'):
            print("\n" + "="*70)
            print(" PRODUCTION STATISTICS")
            print("="*70)
            print(f"Total inspected:     {total_bottles}")
            print(f"Good Ron 88:         {good_ron88}")
            print(f"Rejected:            {rejected_bottles}")
            if total_bottles > 0:
                print(f"Quality rate:        {(good_ron88/total_bottles)*100:.1f}%")
                print(f"Rejection rate:      {(rejected_bottles/total_bottles)*100:.1f}%")
            print("\nRejection breakdown:")
            print(f"  Wrong brand:       {wrong_brand_count}")
            print(f"  Low fill:          {defect_stats['low_fill']}")
            print(f"  No cap:            {defect_stats['no_cap']}")
            print(f"  Loose cap:         {defect_stats['loose_cap']}")
            print(f"  Debris:            {defect_stats['debris']}")
            print(f"  Label damage:      {defect_stats['label_damage']}")
            print(f"  Multi-defect:      {multi_defect_bottles}")
            print("="*70 + "\n")

except KeyboardInterrupt:
    print("\n\n[WARN] Interrupted")

finally:
    print("\n Shutting down...")
    cap.release()
    if arduino:
        arduino.close()
    cv2.destroyAllWindows()

    # Final report
    print("\n" + "="*70)
    print(" FINAL PRODUCTION REPORT")
    print("="*70)
    print(f"Session duration: {time.time() - session_start_time:.0f}s")
    print(f"Total inspected:  {total_bottles}")
    print(f"Good Ron 88:      {good_ron88}")
    print(f"Rejected:         {rejected_bottles}")
    if total_bottles > 0:
        print(f"Quality rate:     {(good_ron88/total_bottles)*100:.1f}%")

    if rejected_bottles > 0:
        print("\nDefect analysis:")
        total_defects = sum(defect_stats.values())
        for defect, count in defect_stats.items():
            if count > 0:
                print(f"  {defect:15s}: {count:3d} ({count/total_defects*100:5.1f}%)")
        print(f"  wrong_brand:     {wrong_brand_count:3d}")
        print(f"\nMulti-defect bottles: {multi_defect_bottles}")

    # Save report to CSV
    REPORT_DIR = r'C:\Users\jihad\D\! All\! Project\23. Conveyor Belt\inference_result'
    os.makedirs(REPORT_DIR, exist_ok=True)

    timestamp = datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d_%H%M%S")
    duration = time.time() - session_start_time
    quality_rate = (good_ron88 / total_bottles * 100) if total_bottles > 0 else 0.0

    # Save per-bottle detail report
    csv_path = os.path.join(REPORT_DIR, f'report_{timestamp}.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['bottle_id', 'timestamp', 'bottle_number', 'result', 'bottle_type', 'defects'])
        for entry in bottle_log:
            writer.writerow([
                entry['bottle_id'],
                entry['timestamp'],
                entry['bottle_number'],
                entry['result'],
                entry['bottle_type'],
                entry['defects']
            ])

    # Save summary report
    summary_path = os.path.join(REPORT_DIR, f'summary_{timestamp}.csv')
    with open(summary_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['session_date', datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(['session_duration_s', f'{duration:.0f}'])
        writer.writerow(['total_inspected', total_bottles])
        writer.writerow(['good_ron88', good_ron88])
        writer.writerow(['rejected', rejected_bottles])
        writer.writerow(['quality_rate_%', f'{quality_rate:.1f}'])
        writer.writerow(['wrong_brand', wrong_brand_count])
        writer.writerow(['defect_low_fill', defect_stats['low_fill']])
        writer.writerow(['defect_no_cap', defect_stats['no_cap']])
        writer.writerow(['defect_loose_cap', defect_stats['loose_cap']])
        writer.writerow(['defect_debris', defect_stats['debris']])
        writer.writerow(['defect_label_damage', defect_stats['label_damage']])
        writer.writerow(['multi_defect_bottles', multi_defect_bottles])

    print(f"\n[OK] Bottle log saved: {csv_path}")
    print(f"[OK] Summary saved:    {summary_path}")

    print("="*70)
    print("[OK] Production system shut down")
    print("="*70)
