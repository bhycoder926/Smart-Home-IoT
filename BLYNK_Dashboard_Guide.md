# Blynk Dashboard Guide — Smart Home Security

This document explains how to design the Blynk IoT dashboard for the Smart Home Security project (two ESP32 devices + laptop camera). It covers creating a Template, adding Devices, building the Web and Mobile dashboards, datastream (virtual pin) definitions, Automation/Event rules, API usage, and best practices.

> This guide matches the code in this project. Virtual pin assignments and example widget types are listed so you can replicate the same dashboard used by the sketches and Python script.

---

## 1. Overview & Goals

- Centralize control and monitoring of:
  - Door lock (ESP32 #1)
  - Lights + sensors (ESP32 #2)
  - Motion-triggered photos (laptop Python script uploads photos and posts URLs)
- Keep both ESP32s online simultaneously by using the same Template but separate Device Auth Tokens.
- Expose a simple mobile and web dashboard to view statuses, control actuators, and receive alerts.

---

## 2. Blynk Concepts (quick)

- Template: reusable blueprint that defines datastreams (virtual pins), device resources, and default widget config.
- Device: an instance of a Template with its own Auth Token. Each physical ESP32 must be a Device to appear online.
- Datastreams: the Template-level definition mapping to Virtual Pins (V0, V1...). Each datastream has a type (integer, string, double) and a name.
- Widgets: controls and displays you add to a Dashboard (Web or Mobile) and bind to datastreams.
- Eventor / Automation: server-side rules that react to datastream values, send notifications, or call webhooks.

---

## 3. Template Setup (create once)

1. Open Blynk Console (https://blynk.cloud) and log in.
2. Click `Templates` → `Create Template`.
   - Name: `Smart Home Automation` (or similar)
   - Template ID: auto-generated (record it if needed)
3. Add Datastreams (virtual pins) to the Template — the names and types below match this project:

| Datastream (Virtual Pin) | Type    | Purpose |
|--------------------------|---------|---------|
| V0                       | Digital | Light 1 control (0/1) |
| V1                       | Digital | Light 2 control (0/1) |
| V2                       | Double  | Temperature (°C) |
| V3                       | Double  | Humidity (%) |
| V4                       | Integer| Gas analog reading (0–4095) |
| V5                       | String  | Last Photo URL (string) |
| V6                       | String  | Photo timestamp / label |
| V7                       | String  | Lock Status (string) |
| V8                       | Digital | Lock control (0=Locked,1=Unlocked) |

Notes:
- Datastream `V5` is used by the Python script to post the image URL so it can be displayed with an Image widget or Label.
- Choose sensible types for each datastream to allow widgets to present them correctly.

4. (Optional) Add metadata and description to Template so collaborators understand the mapping.

---

## 4. Create Devices (one per physical board)

You need one Device per ESP32. Each Device will belong to the same Template.

1. In the Template view, click `Create Device`.
2. Fill in Device details:
   - Device name: `DoorLock-ESP32` (or `Lock`) for the lock board.
   - Device name: `Lights-ESP32` (or `Lights`) for the lights/sensors board.
3. After creation, open each Device's `Device Info` and copy the `Auth Token`. You will paste these tokens into the respective `.ino` files:
   - `Smart_Door_Lock.ino` — uses the Lock device token (this repo currently has a value in the file; consider removing tokens before publishing to GitHub).
   - `Smart_Lights.ino` — uses the Lights device token.
4. Keep tokens private — anyone with a token can control the device.

Important: Do NOT use the same Auth Token on multiple physical devices. Using the same token will cause one device to go offline when another connects. The Template can be the same for both devices.

---

## 5. Web Dashboard vs Mobile Dashboard

Blynk provides a Web Console (dashboard builder) and a Mobile app. The Template and Datastreams are shared, but you create Widgets in a Dashboard (Web or Mobile) and bind them to the template datastreams.

- Web Dashboard: easier for arranging many widgets, supports larger layouts.
- Mobile App: convenient for handheld control and notifications.

Create the dashboard after the Template and Devices exist:

1. Open `Dashboards` → `Create Dashboard` → Choose Template `Smart Home Automation`.
2. Add Widgets and bind to Template Datastreams.

Recommended Widgets and bindings (suggested layout):

- Row 1 (Controls)
  - `Button` (switch) → bind to `V0` (Light 1). Mode: Switch.
  - `Button` (switch) → bind to `V1` (Light 2).
  - `Button` (momentary) or `Slider` → bind to `V8` (Lock Control) — set as Switch where ON=Unlock, OFF=Lock.

- Row 2 (Sensors)
  - `Value Display` → bind to `V2` (Temperature).
  - `Value Display` → bind to `V3` (Humidity).
  - `Gauge` or `Value` → bind to `V4` (Gas Level).

- Row 3 (Camera + Logs)
  - `Label` or `Text` → bind to `V7` (Lock Status).
  - `Image` widget or `Label` → bind to `V5` (Last Photo URL). If Image widget supports URL input, set it to display the URL; otherwise show the URL in a Label widget so users can click/open.
  - `Value Display` → bind to `V6` (Photo timestamp).

- Notifications and Events
  - Use `Eventor` (Automation) to send push notifications when `V4` (Gas Level) exceeds threshold.
  - Use `Eventor` to send push or email when `V5` (Photo URL) updates.

Widget Tips:
- For Image widgets, some Blynk dashboards accept a direct URL string and will show the image. If not, use the Label widget and open the image in a browser.
- Add descriptive labels and icons to make the dashboard user-friendly.

---

## 6. Automation (examples)

### Gas Alert
- Trigger: `V4 > 600` (the code threshold uses 600)
- Actions:
  - Push Notification: "🚨 Gas leakage detected!"
  - Send Email or Webhook (optional)
  - Log an event

### Motion / Photo Notification
- Trigger: `V5` changes (non-empty)
- Actions:
  - Push Notification: "Someone is at the door — photo available"
  - (Optional) Call webhook to your home server with the photo URL

### Doorbell / Lock Events
- Trigger: `V2 == 1` (Doorbell virtual pin set by camera script when motion detected)
- Actions:
  - Send notification to phone
  - Flash lights (set V0 and V1 momentarily) — use a small automation script or the Eventor.

---

## 7. Blynk REST API Examples

Blynk provides a REST API to read/update virtual pins from scripts (used by `smart_door_camera.py`).

- Base URL used in the Python script: `https://blynk.cloud/external/api`

Update a virtual pin (example, set V5 to a string):

```bash
# HTTP GET example
curl "https://blynk.cloud/external/api/update?token=<AUTH_TOKEN>&pin=V5&value=https://i.ibb.co/yourimage.jpg"
```

Python `requests` example (used by the project):

```python
import requests
url = 'https://blynk.cloud/external/api/update'
params = { 'token': AUTH_TOKEN, 'pin': 'V5', 'value': image_url }
requests.get(url, params=params, timeout=5)
```

Get a virtual pin value:

```bash
curl "https://blynk.cloud/external/api/get?token=<AUTH_TOKEN>&pin=V2"
```

Log an event (server-side event) or create a notification:

```bash
curl "https://blynk.cloud/external/api/logEvent?token=<AUTH_TOKEN>&code=doorbell&description=Someone%20is%20at%20the%20door"
```

Notes:
- Replace `<AUTH_TOKEN>` with the device token of the Device you want to control or whose virtual pin you want to update.
- The Python script in this repo uses these endpoints to push `V5` (photo URL), `V6` (photo time), and to set `V2` (doorbell trigger).

---

## 8. Mapping the Project Files to Dashboard

- `Smart_Door_Lock.ino` (Device: DoorLock-ESP32)
  - Reads/writes: V7 (status string), V8 (control digital)
  - Use: Bind V8 to a Button widget (Switch). Bind V7 to a Label or Text.

- `Smart_Lights.ino` (Device: Lights-ESP32)
  - Reads/writes: V0 (Light1 switch), V1 (Light2 switch), V2 (temperature), V3 (humidity), V4 (gas)
  - Use: Buttons/Switches for V0/V1; Value widgets for V2–V4; Eventor for gas alerts.

- `smart_door_camera.py` (runs on laptop, uses Blynk REST API)
  - Writes: V5 (image URL), V6 (time label), V2 (doorbell trigger)
  - Use: Image/Label widgets to show images; automation to notify when photo URL updates.

---

## 9. Best Practices & Security

- Keep Auth Tokens out of public repos. Replace tokens in committed files with placeholders or use a `secrets.h` / `.env` file that you don't commit.
- Use separate tokens per physical device to avoid connection conflicts.
- Limit automation actions that trigger actuator-heavy loads (e.g., do not auto-fire solenoid continuously).
- Test automations with conservative thresholds (e.g., gas threshold slightly above ambient noise).

---

## 10. Troubleshooting

- If a device does not appear online:
  - Check Wi-Fi credentials in the sketch.
  - Confirm the correct Auth Token is used for that device.
  - Make sure only one device uses each token.

- If the Python script cannot post images:
  - Verify your ImgBB API key (or Imgur client ID) is valid.
  - Check the laptop’s internet connection and firewall.

- If image widget doesn't display images:
  - Check that `V5` is being updated with a public URL reachable from the internet (ImgBB works well).
  - If Blynk Image widget requires a specific input, use a Label and click the URL to open in browser.

---

## 11. Quick Checklist Before Use

- [ ] Add Blynk Template and datastreams (V0–V8)
- [ ] Create two Devices (Lock and Lights) and note their Auth Tokens
- [ ] Update Auth Tokens in `Smart_Door_Lock.ino`, `Smart_Lights.ino`, and `smart_door_camera.py` (or use environment-based secrets)
- [ ] Flash both ESP32 devices with their respective sketches
- [ ] Configure dashboard widgets and automations
- [ ] Start `smart_door_camera.py` and verify image uploads and V5 updates

---

## 12. Using Door + Camera Together (End-to-End)

This section explains the typical interactions when the laptop camera and door-lock ESP32 work together, and how to test and automate their combined behavior.

- Typical flow when motion is detected:
  - `smart_door_camera.py` detects motion and captures a photo.
  - The script uploads the photo to ImgBB and writes the public URL to `V5` and a timestamp to `V6` using the Blynk REST API.
  - The script sets `V2 = 1` (doorbell trigger) so other devices or automations can react.
  - The dashboard receives the new photo URL and shows it in the Image/Label widget. A notification can be sent via Eventor.

- Example actions you can take from the dashboard after a photo:
  - Inspect the picture on the dashboard (Image widget or open the URL from the Label).
  - If authorized, press the Lock control (`V8`) to unlock the door remotely.
  - Use Light controls (`V0`/`V1`) to turn on lights for visibility or to deter intruders.

- Automations you can configure safely:
  - Motion -> Notification: When `V5` updates (non-empty), send a push notification and include the photo URL in the message.
  - Motion -> Flash Lights: When `V2 == 1`, toggle `V0`/`V1` briefly to flash lights; use conservative timing to avoid wear on relays.
  - (Optional, use with caution) Motion -> Auto-unlock: If you want the door to auto-unlock on verified motion, create an automation that sets `V8 = 1` when `V5` updates and a verification condition is met (e.g., face recognition or manual confirmation). Auto-unlock is a security-sensitive action — test thoroughly and consider requiring manual approval.

- How to test the full stack (step-by-step):
  1. Start both ESP32 devices so they appear online in the Blynk Console.
  2. Start the camera script on your laptop:

```powershell
cd 'c:\Users\harsh\Documents\Bhyresh\Programs\Smart_Home_Security'
python .\smart_door_camera.py
```

  3. Trigger motion (walk in front of the camera) and watch the script log showing upload and API calls.
  4. Verify `V5` and `V6` update on the dashboard and that the Image/Label widget shows the new photo/time.
  5. From the dashboard press the Lock control (V8) and check the door-lock ESP32 log/serial to verify it received the command and actuated the solenoid.
  6. Use the Light controls (V0/V1) to verify relays toggle and sensors report values.

- Troubleshooting combined behavior:
  - Photo not showing: confirm `smart_door_camera.py` printed the ImgBB URL and that `V5` was updated using the correct device token.
  - Dashboard doesn't update: ensure you're viewing the Dashboard for the correct Template/Device instance and that the device token used by the script matches the Device that owns the `V5` datastream.
  - Lock command not received: check the DoorLock serial logs for messages from Blynk; confirm `V8` is bound to the correct Device and the token in `Smart_Door_Lock.ino` matches that Device.

- Security & safety notes specific to combined use:
  - Do not publish device Auth Tokens. Move tokens to a non-committed `secrets.h` or use environment variables for the Python script.
  - Require confirmation before auto-unlock. Use automations that assist the user (notify + show photo) rather than automatically disabling physical security unless you have robust verification.
  - Rate-limit actions that trigger heavy loads (solenoid, multiple relay toggles) to avoid damaging hardware.

If you want, I can also add a short example automation JSON or an Eventor rule script for the dashboard that implements "Motion → Notify + Flash Lights" and place it in the repo.


