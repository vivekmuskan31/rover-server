# image_service.py

import base64
import io
import time
import numpy as np
import cv2
from PIL import Image

from services.base_service import BaseService
from utils import get_logger, config
from services.gesture_service import detect_hand_gesture, GestureCommandController


class ImageService(BaseService):
    def __init__(self, name="ImageService"):
        super().__init__(name)
        self.logger = get_logger(self.name)
        self.frame_buffer = {}  # seq: image
        self.gesture_controller = None

    async def handle(self, data: dict):
        try:
            seq = data.get("seq")
            encoded_image = data.get("data")
            timestamp = data.get("timestamp")

            image = self.decode_image(encoded_image)

            if not image:
                self.logger.warning("No image was decoded or received")
                return
            
            np_frame = np.array(image)  # Convert PIL → RGB NumPy
            np_frame = cv2.cvtColor(np_frame, cv2.COLOR_RGB2BGR)  # Convert to BGR

            gesture, frame = detect_hand_gesture(np_frame)
            # self.logger.info(label)

            if not self.gesture_controller:
                self.gesture_controller = GestureCommandController()
            
            if config['ModeMap'][config['CurrentMode']].lower() == "gesture":
                await self.gesture_controller.handle_gesture(gesture)
            await self.stream_frame(seq, frame, timestamp)
            
        except Exception as e:
            self.logger.error(f"Failed to handle image data: {e}")

    def decode_image(self, encoded: str):
        try:
            decoded_bytes = base64.b64decode(encoded)
            image_stream = io.BytesIO(decoded_bytes)
            return Image.open(image_stream).convert("RGB")
        except Exception as e:
            self.logger.error(f"Image decode error: {e}")
            return None

    async def stream_frame(self, seq: int, image: Image.Image, timestamp: float):
        """
        Display video feed on Mac using OpenCV window.
        """
        if image is None:
            self.logger.warning(f"[Seq {seq}] Image was None, skipping")
            return

        self.frame_buffer[seq] = image

        # Convert PIL image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        cv2.imshow("Live Feed", cv_image)
        cv2.waitKey(5)  # Needed to update the window

        # self.logger.info(f"[Seq {seq}] Frame displayed at {timestamp:.2f}")

    