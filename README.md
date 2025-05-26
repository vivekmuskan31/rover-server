# Rover Server


## Task
1. Start simple communication with rover-client `Done`
2. Add Nintendo switch for manual control `Done`
3. Test Hand Tracking and detection using camera `InProgress`


rover_server/
│
├── rover_server.py              # 🚀 FastAPI entrypoint (formerly main.py)
├── communication_manager.py     # 🔁 Handles all WebSocket I/O + routing
├── config.yaml                  # ⚙️ Optional config
├── utils.py                     # 🧰 Shared logging, helpers
│
├── services/                    # 🧠 Each service handles a type of incoming data
│   ├── base_service.py          # 🔹 Abstract base class
│   ├── image_service.py         # 📷 Handles camera_frame packets
│   └── gesture_service.py       # ✋ Mediapipe gesture detection


