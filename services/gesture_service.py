# gesture_demo.py (refactored into a function)

import cv2
import time
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import mediapipe as mp
from utils import get_logger, config

MODEL_PATH = "gesture_recognizer.task"  # Make sure the model is downloaded
SENSITIVITY_ROTATION = config['Gesture']['Sensitivity']['Rotational']
SENSITIVITY_MOVEMENT = config['Gesture']['Sensitivity']['Translational']
GESTURE_TO_CMD = config['Gesture']['To_Command']

# Setup gesture recognizer once
base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.GestureRecognizerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
)
recognizer = vision.GestureRecognizer.create_from_options(options)

def detect_hand_gesture(frame: np.ndarray):
    """
    Takes a BGR frame as input.
    Returns: (gesture_label, confidence), annotated_frame (BGR)
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    timestamp = int(time.time() * 1000)
    result = recognizer.recognize_for_video(mp_image, timestamp)

    annotated_frame = frame.copy()
    label = None

    if result.gestures and len(result.gestures) > 0:
        gesture = result.gestures[0][0]  # Top prediction
        label = (gesture.category_name, gesture.score)
        cv2.putText(
            annotated_frame,
            f"{label[0]} ({label[1]:.2f}) -> {GESTURE_TO_CMD.get(label[0], 'STOP')} \nMode = {config['ModeMap'][config['CurrentMode']]}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    return label, annotated_frame


from collections import deque, Counter
from communication_manager import CommunicationManager  # Adjust path

class GestureCommandController:
    def __init__(self, history_size=5):
        self.cmd_stabilizer = deque(maxlen=history_size)
        self.current_label = "STOP"
        self.logger = get_logger("GestureController")

        self.cmd_to_motor = {
            "STOP": (0.0, 0.0),
            "FORWARD": (SENSITIVITY_MOVEMENT, SENSITIVITY_MOVEMENT),
            "BACKWARD": (-SENSITIVITY_MOVEMENT, -SENSITIVITY_MOVEMENT),
            "TURN_LEFT": (-SENSITIVITY_ROTATION, SENSITIVITY_ROTATION),
            "TURN_RIGHT": (SENSITIVITY_ROTATION, -SENSITIVITY_ROTATION),
            "SPIN": (1.0, -1.0)
        }

    async def handle_gesture(self, gesture):
        if gesture:
            label, confidence = gesture
            # self.logger.info(f"{gesture}\t {self.cmd_stabilizer}")
            if confidence >= 0.5:
                self.cmd_stabilizer.append(label) 
            stable_label = Counter(self.cmd_stabilizer).most_common(1)[0][0]

            # if stable_label != self.current_label:
            #     self.current_label = stable_label
            await self.send_motor_command(stable_label)

    async def send_motor_command(self, label: str):
        #self.logger.info("CMD = {self.gesture_to_cmd(label)}")
        left, right = self.cmd_to_motor.get(
            GESTURE_TO_CMD.get(label, "STOP"), (0.0, 0.0)
            )
        packet = {
            "type": "motor_cmd",
            "left_motor": left,
            "right_motor": right
        }
        comm = CommunicationManager.get_instance()
        await comm.send_to_all(packet)
        self.logger.info(f"[Sent] : {packet}")


# Optional: run demo loop
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 10)
    print("Starting gesture recognition demo...")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        label, annotated = detect_hand_gesture(frame)
        cv2.imshow("Gesture Recognition", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
