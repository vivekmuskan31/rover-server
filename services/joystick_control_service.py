# manual_control_service.py

import asyncio
import time
import pygame
from services.base_service import BaseService
from utils import get_logger, config
from communication_manager import CommunicationManager

DEADZONE = config['Joystick']['Deadzone']
UPDATE_INTERVAL = config['Joystick']['Command_Refresh_Rate']
SENSITIVITY = config['Joystick']['Deadzone_Cutoff']

def clamp(val, min_val=0.1, max_val=1.0):
    return max(min_val, min(max_val, val))

def apply_deadzone(val, threshold=DEADZONE):
    return val if abs(val) > threshold else 0

class JoystickControlService(BaseService):
    def __init__(self, name="JoyStickControlService"):
        super().__init__(name)
        self.logger = get_logger(self.name)
        self.sensitivity = SENSITIVITY

    async def handle(self, data: dict):
        # Not used in this service — we send data proactively
        pass

    def init_joystick(self):
        pygame.init()
        pygame.joystick.init()
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        return joystick

    def compute_motor_speeds(self, x, y, plus=False, minus=False):
        if plus:
            self.sensitivity = clamp(self.sensitivity + 0.05)
        if minus:
            self.sensitivity = clamp(self.sensitivity - 0.05)

        y = -y
        x = apply_deadzone(x)
        y = apply_deadzone(y)

        left = (y - x) * self.sensitivity
        right = (y + x) * self.sensitivity

        left = max(-1, min(1, left))
        right = max(-1, min(1, right))
        return left, right

    async def start(self):
        while True:
            try:
                joystick = self.init_joystick()
                self.logger.info("Joystick connected successfully.")
                break
            except Exception as e:
                self.logger.warning(f"Joystick not found. Retrying in 10s... ({e})")
                await asyncio.sleep(10)

        try:
            self.logger.info("Monitoring Joystck from now every 20ms")
            while True:
                pygame.event.pump()

                ## Mode switching
                l2_pressed = joystick.get_button(9)
                total_modes = len(config['ModeMap'])
                if l2_pressed:
                    config['CurrentMode'] += 1
                    config['CurrentMode'] %= total_modes
                    self.logger.info(f"Mode switched to {config['ModeMap'][config['CurrentMode']]}")
                    time.sleep(0.5)

                if time.time() % UPDATE_INTERVAL > 0.01:
                    await asyncio.sleep(0.05)
                    continue

                x = joystick.get_axis(2)
                y = joystick.get_axis(1)
                plus = joystick.get_button(6)
                minus = joystick.get_button(4)

                if config['ModeMap'][config['CurrentMode']].lower() == "manual":
                    left, right = self.compute_motor_speeds(x, y, plus, minus)
                    if abs(left) < DEADZONE: left = 0
                    if abs(right) < DEADZONE: right = 0

                    if left!=0 or right!=0:
                        data = {
                            "type": "motor_cmd",
                            "left_motor": left,
                            "right_motor": right
                        }
                        await CommunicationManager.get_instance().send_to_all(data)
                        self.logger.info(f"[SENT] {data}")
        finally:
            joystick.quit()
            pygame.quit()
