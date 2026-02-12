// RON 88 BOTTLE REJECTION SERVO - TIMED CONTROL


#include <Servo.h>

Servo rejectionServo;

// ========== PIN CONFIGURATION ==========
const int SERVO_PIN = 9;

// ========== SERVO POSITIONS (degrees) ==========
// NOTE: ADJUST THESE based on the physical setup:
const int NORMAL_POS = 0;      // Servo resting position (away from belt)
const int REJECT_POS = 90;     // Servo push position (blocks bottle path)

// ========== TIMING CONFIGURATION ==========

// NOTE: DETECTION_DELAY: Time from when camera detects defect to when servo activates
// How to calculate:
//   1. Measure distance from camera center to servo (in cm)
//   2. Measure belt speed (use stopwatch: distance/time in cm/s)
//   3. Calculate: DETECTION_DELAY = (distance / speed) * 1000
//
// Example:
//   Distance = 30 cm
//   Belt speed = 10 cm/s
//   DETECTION_DELAY = (30 / 10) * 1000 = 3000 ms (3 seconds)
//
const unsigned long DETECTION_DELAY = 5550;  // ← ADJUST THIS (milliseconds)

// NOTE: PUSH_DURATION: How long servo stays in push position
// Too short = bottle not fully pushed
// Too long = servo might hit next bottle
const unsigned long PUSH_DURATION = 1000;     // ← ADJUST THIS (milliseconds)

// NOTE: COOLDOWN: Wait time before ready for next rejection
const unsigned long COOLDOWN = 100;          // ← ADJUST THIS (milliseconds)

// ========== REJECTION QUEUE ==========
const int QUEUE_SIZE = 10;
unsigned long rejectionQueue[QUEUE_SIZE];
int queueHead = 0;
int queueTail = 0;
int queueCount = 0;

// ========== STATE VARIABLES ==========
unsigned long returnTime = 0;
bool isPushing = false;
int rejectionCount = 0;
int goodCount = 0;

// ========== SETUP ==========
void setup() {
  Serial.begin(9600);
  rejectionServo.attach(SERVO_PIN);
  rejectionServo.write(NORMAL_POS);

  // Print configuration
  Serial.println("===== RON 88 BOTTLE REJECTION SYSTEM - READY =====");
  Serial.print("Detection delay:  ");
  Serial.print(DETECTION_DELAY);
  Serial.println(" ms");
  Serial.print("Push duration:    ");
  Serial.print(PUSH_DURATION);
  Serial.println(" ms");
  Serial.print("Cooldown:         ");
  Serial.print(COOLDOWN);
  Serial.println(" ms");
  Serial.print("Normal position:  ");
  Serial.print(NORMAL_POS);
  Serial.println("°");
  Serial.print("Reject position:  ");
  Serial.print(REJECT_POS);
  Serial.println("°");
  Serial.println("===== Commands: R = Reject | G = Good | S = Stats =====");
}

// ========== MAIN LOOP ==========
void loop() {
  // Check for commands from computer
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == 'R') {  // REJECT command (defective Ron 88 or wrong bottle)
      if (queueCount < QUEUE_SIZE) {
        // Add to rejection queue
        rejectionQueue[queueTail] = millis() + DETECTION_DELAY;
        queueTail = (queueTail + 1) % QUEUE_SIZE;
        queueCount++;
        Serial.print("[WARN] DEFECT/WRONG BOTTLE - Rejection queued (");
        Serial.print(queueCount);
        Serial.println(" pending)");
      } else {
        Serial.println("[FULL] Rejection queue full, ignored");
      }
    }
    else if (command == 'G') {  // GOOD command (perfect Ron 88)
      goodCount++;
      Serial.print("[OK] Good Ron 88 bottle (#");
      Serial.print(goodCount);
      Serial.println(")");
    }
    else if (command == 'S') {  // STATS command
      Serial.println("\n SESSION STATISTICS:");
      Serial.print("  Good Ron 88:  ");
      Serial.println(goodCount);
      Serial.print("  Rejected:     ");
      Serial.println(rejectionCount);
      Serial.print("  Total:        ");
      Serial.println(goodCount + rejectionCount);
      if ((goodCount + rejectionCount) > 0) {
        float rejectRate = (float)rejectionCount / (goodCount + rejectionCount) * 100;
        Serial.print("  Reject rate:  ");
        Serial.print(rejectRate, 1);
        Serial.println("%\n");
      }
    }
  }

  // Execute next queued rejection
  if (queueCount > 0 && millis() >= rejectionQueue[queueHead] && !isPushing) {
    // Activate servo
    rejectionServo.write(REJECT_POS);
    isPushing = true;
    returnTime = millis() + PUSH_DURATION;
    queueHead = (queueHead + 1) % QUEUE_SIZE;
    queueCount--;
    rejectionCount++;
    Serial.print("[REJECT] SERVO ACTIVATED (#");
    Serial.print(rejectionCount);
    Serial.print(") - Pushing bottle (");
    Serial.print(queueCount);
    Serial.println(" still pending)");
  }

  // Return servo to normal position
  if (isPushing && millis() >= returnTime) {
    rejectionServo.write(NORMAL_POS);
    isPushing = false;
    delay(COOLDOWN);
    Serial.println("[OK] SERVO RETURNED - Ready for next");
  }
}
