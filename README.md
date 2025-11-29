# Smart Home Security — ESP32 + Laptop Camera

A lightweight Smart Home project that integrates two ESP32-based devices (door lock and lights/sensors) with a laptop camera for motion-triggered photos. The project uses Blynk IoT for remote control and ImgBB for image hosting.

## Contents

- `Smart_Door_Lock.ino` — ESP32 sketch to control a 12V solenoid lock via TIP122. Uses Blynk virtual pins V7 (status) and V8 (control).
- `Smart_Lights.ino` — ESP32 sketch for relay-controlled lights, DHT11 temperature/humidity, and MQ-2 gas sensor. Uses Blynk virtual pins V0–V4.
- `smart_door_camera.py` — Python script using OpenCV to detect motion, capture photos, upload to ImgBB, and send the image URL to Blynk (V5 for URL, V6 for timestamp).
- `BLYNK_Dashboard_Guide.md` — Comprehensive guide to setting up Blynk: templates, devices, datastreams, widgets, automations, and combined door + camera usage.
- `HARDWARE_WIRING.md` — Component list, wiring diagrams, power-supply design, and safety notes.
- `requirements.txt` — Python dependencies for the camera script.
- `.gitignore` — Useful ignores (photos folder, caches).
- `LICENSE` — MIT license.

## Quick Setup

1. Open `Smart_Door_Lock.ino` and `Smart_Lights.ino` in Arduino IDE (with ESP32 board support installed).
   - Install libraries: `Blynk` and `DHT` (Adafruit DHT sensor library).
   - Update `BLYNK_AUTH_TOKEN` placeholders with your device tokens.

2. Configure Wi-Fi credentials in both sketches (`ssid` / `pass`).

3. Flash `Smart_Door_Lock.ino` to the ESP32 that will control the lock and `Smart_Lights.ino` to the ESP32 that will control lights/sensors. Use separate device tokens in Blynk (same Template is OK).

4. Python camera:
   - Install Python 3.8+ and dependencies:

```powershell
python -m pip install -r requirements.txt
```

   - Edit `smart_door_camera.py` and set `BLYNK_AUTH_TOKEN` and `IMGBB_API_KEY`.
   - Run:

```powershell
python .\smart_door_camera.py
```

## Notes & Recommendations

- When flashing ESP32 while solenoid or relays are connected, disconnect the high-current loads or power the boards from USB-only to avoid flash failures.
- Use separate device Auth Tokens in Blynk for each ESP32 if you want them online simultaneously under the same Template.
- `door_photos/` is where captured images are saved locally. This folder can be git-ignored to avoid pushing images.

## How to push to GitHub

From the `Smart_Home_Security` folder:

```powershell
git init
git add .
git commit -m "Add Smart Home Security project: door lock, lights, camera"
# Create a GitHub repository then:
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

If you want, I can create the commit for you locally and show the exact commands.

## Contributors & Roles

This project was completed collaboratively. Special thanks to:

| Name                | Role(s) & Contribution                |
|---------------------|---------------------------------------|
| Bhyresh B S (bhycoder926) | Project lead, hardware design, coding, documentation |
| Busetty Sugnesh     | Role:  hardware, coding, testing, dashboard |
| Chandana M     | Role:  wiring, code review, presentation |
| Hansika     | Role:  research, debugging, deployment |

_Add more rows as needed. Please fill in your friends' names and their specific roles._

## License

This project is MIT licensed. See `LICENSE` for details.
