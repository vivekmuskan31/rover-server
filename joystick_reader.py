import pygame
import time
import asyncio

DEADZONE = 0.1
UPDATE_INTERVAL = 0.1  # 100 ms

last_sent = time.time()

sensitivity = 0.5  # Starts at 50%

# Clamp helper
def clamp(val, min_val=0.1, max_val=1.0):
    return max(min_val, min(max_val, val))

# Apply deadzone filter
def apply_deadzone(val, threshold=DEADZONE):
    return val if abs(val) > threshold else 0

# Compute motor speeds based on joystick input and sensitivity adjustment
def compute_motor_speeds(x, y, plus=False, minus=False):
    global sensitivity

    # Adjust sensitivity
    if plus:
        sensitivity = clamp(sensitivity + 0.05)
    if minus:
        sensitivity = clamp(sensitivity - 0.05)

    y = -y  # Invert Y for forward motion
    x = apply_deadzone(x)
    y = apply_deadzone(y)

    left = (y - x) * sensitivity
    right = (y + x) * sensitivity

    left = max(-1, min(1, left))
    right = max(-1, min(1, right))

    return left, right


# Joystick initialization
def init_joystick():
    pygame.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    return joystick

def print_joystick_state(joystick):
    axes = joystick.get_numaxes()
    buttons = joystick.get_numbuttons()
    hats = joystick.get_numhats()

    # print(f"Axes ({axes}): {[joystick.get_axis(i) for i in range(axes)]}")
    print(f"Buttons ({buttons}): {[joystick.get_button(i) for i in range(buttons)]}")
    # print(f"Hats ({hats}): {[joystick.get_hat(i) for i in range(hats)]}")


# Async function to monitor joystick and send data when L2 is pressed
async def monitor_joystick(send_to_client):
    joystick = init_joystick()
    try:
        manual_mode = False
        while True:
            pygame.event.pump()

            now = time.time()
            global last_sent
            if now - last_sent < UPDATE_INTERVAL:
                await asyncio.sleep(0.05)
                continue

            x = joystick.get_axis(2) # Left Joystick throttel
            y = joystick.get_axis(1) # Right joystick roll
            minus = joystick.get_button(4)
            plus = joystick.get_button(6)
            buttons = joystick.get_numbuttons()

            l2_pressed = joystick.get_button(9)  # L2 button (adjust index if needed)
            print_joystick_state(joystick)

            if l2_pressed:
                if manual_mode:
                    print("Manual Mode OFF. Stopped.") 
                manual_mode = not manual_mode
            if manual_mode:
                print("Manual Mode ON. Streaming cmd....")
                left, right = compute_motor_speeds(x, y, plus=plus, minus=minus)

                data = {
                    "type": "joystick",
                    "left_motor": left,
                    "right_motor": right
                }
                
                await send_to_client(data, dtype='json')
                print(f"[Sent] {data}")

            last_sent = now

    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        joystick.quit()
        pygame.quit()

if __name__ == "__main__":
    asyncio.run(monitor_joystick())
