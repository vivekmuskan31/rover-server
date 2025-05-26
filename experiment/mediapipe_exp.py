# gesture_demo.py (Fixed for RunningMode.VIDEO)

import cv2
import time
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import mediapipe as mp
from display_help import display_batch_of_images_with_gestures_and_hand_landmarks

MODEL_PATH = "gesture_recognizer.task"  # Make sure the model is downloaded

# Setup base options and recognizer
base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.GestureRecognizerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
)

recognizer = vision.GestureRecognizer.create_from_options(options)

# Open webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 10)

print("Starting gesture recognition...")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Failed to grab frame.")
        break

    # Convert to RGB and wrap in MP Image
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    # Perform recognition
    timestamp = int(time.time() * 1000)
    result = recognizer.recognize_for_video(mp_image, timestamp)

    # Draw label if present
    if result.gestures and len(result.gestures) > 0:
        gesture = result.gestures[0][0]  # Top gesture
        label = f"{gesture.category_name} ({gesture.score:.2f})"
        cv2.putText(frame, label, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Gesture Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()


