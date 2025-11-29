"""
Smart Door Camera with Blynk Image Display
===========================================
This script:
1. Detects motion using laptop webcam
2. Takes photos automatically
3. Uploads photos to Imgur (free image hosting)
4. Displays photo URL in Blynk dashboard
5. Sends notifications

Requirements:
    pip install opencv-python requests

Blynk Virtual Pins used by this script:
    V2 - Doorbell trigger (set to 1 when motion detected)
    V5 - Last Photo URL (String) ← Display this in dashboard!
    V6 - Photo timestamp (String)

Note: Lock control is on V8 (handled by Smart_Door_Lock.ino on ESP32 #1).

Author: Bhyresh
Date: November 2025
"""

import cv2
import requests
import time
import threading
import base64
from datetime import datetime
import os

# ============= CONFIGURATION =============
# Blynk Configuration - Use SAME token as ESP32
BLYNK_AUTH_TOKEN = "_U7v-3wvBTNh7ODSoZfjxihGnOWPTs7Z"  # Smart Home Automation token
BLYNK_SERVER = "https://blynk.cloud/external/api"

# ImgBB Configuration (Free image hosting - easier than Imgur!)
# Get your FREE API Key from: https://api.imgbb.com/
IMGBB_API_KEY = "f56cc8d77a16dbb523ecbdcbf0503935"  # ← REPLACE WITH YOUR API KEY

# Imgur Configuration (Alternative - set to "SKIP" to disable)
IMGUR_CLIENT_ID = "SKIP"

# Camera settings
CAMERA_INDEX = 0  # Usually 0 for built-in laptop camera
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Motion detection settings
MOTION_THRESHOLD = 5000  # Adjust this value for sensitivity
MOTION_COOLDOWN = 10  # Seconds between motion alerts
MIN_CONTOUR_AREA = 500  # Minimum area to consider as motion

# Photo save directory
PHOTOS_DIR = "door_photos"

# ============= BLYNK API FUNCTIONS =============

def send_blynk_notification(message):
    """Send a notification through Blynk"""
    try:
        # Trigger event for notification
        url = f"{BLYNK_SERVER}/logEvent"
        params = {
            "token": BLYNK_AUTH_TOKEN,
            "code": "doorbell",
            "description": message
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            print(f"[BLYNK] Notification sent: {message}")
        else:
            print(f"[BLYNK] Failed to send notification: {response.status_code}")
    except Exception as e:
        print(f"[BLYNK] Error sending notification: {e}")


def set_blynk_pin(pin, value):
    """Set a virtual pin value on Blynk"""
    try:
        url = f"{BLYNK_SERVER}/update"
        params = {
            "token": BLYNK_AUTH_TOKEN,
            "pin": pin,
            "value": value
        }
        response = requests.get(url, params=params, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"[BLYNK] Error setting pin {pin}: {e}")
        return False


def get_blynk_pin(pin):
    """Get a virtual pin value from Blynk"""
    try:
        url = f"{BLYNK_SERVER}/get"
        params = {
            "token": BLYNK_AUTH_TOKEN,
            "pin": pin
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()[0]
        return None
    except Exception as e:
        print(f"[BLYNK] Error getting pin {pin}: {e}")
        return None


# ============= IMGUR UPLOAD =============

def upload_to_imgur(image_path):
    """Upload image to Imgur and return URL"""
    if IMGUR_CLIENT_ID == "YOUR_IMGUR_CLIENT_ID" or IMGUR_CLIENT_ID == "SKIP":
        return None
    
    try:
        print("[IMGUR] Uploading photo...")
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        url = "https://api.imgur.com/3/image"
        headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
        data = {"image": image_data, "type": "base64"}
        
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            image_url = response.json()["data"]["link"]
            print(f"[IMGUR] ✅ Uploaded: {image_url}")
            return image_url
        else:
            print(f"[IMGUR] ❌ Upload failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"[IMGUR] Error: {e}")
        return None


# ============= IMGBB UPLOAD (RECOMMENDED) =============

def upload_to_imgbb(image_path):
    """Upload image to ImgBB and return URL"""
    if IMGBB_API_KEY == "YOUR_IMGBB_API_KEY":
        return None
    
    try:
        print("[IMGBB] Uploading photo...")
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": image_data,
        }
        
        response = requests.post(url, payload, timeout=30)
        
        if response.status_code == 200:
            image_url = response.json()["data"]["url"]
            print(f"[IMGBB] ✅ Uploaded: {image_url}")
            return image_url
        else:
            print(f"[IMGBB] ❌ Upload failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"[IMGBB] Error: {e}")
        return None


# ============= CAMERA CLASS =============

class SmartDoorCamera:
    def __init__(self):
        self.cap = None
        self.running = False
        self.last_motion_time = 0
        self.prev_frame = None
        self.motion_detected = False
        self.photos_taken = 0
        self.last_photo_url = None
        
        # Create photos directory
        if not os.path.exists(PHOTOS_DIR):
            os.makedirs(PHOTOS_DIR)
            print(f"[INFO] Created photos directory: {PHOTOS_DIR}")
    
    def start_camera(self):
        """Initialize and start the camera"""
        print("[INFO] Starting camera...")
        
        # Try different camera backends for Windows
        backends = [
            (cv2.CAP_DSHOW, "DirectShow"),
            (cv2.CAP_MSMF, "Media Foundation"),
            (cv2.CAP_ANY, "Default")
        ]
        
        for backend, name in backends:
            print(f"[INFO] Trying {name} backend...")
            self.cap = cv2.VideoCapture(CAMERA_INDEX, backend)
            
            if self.cap.isOpened():
                # Try to read a test frame
                ret, _ = self.cap.read()
                if ret:
                    print(f"[INFO] ✅ Camera opened with {name} backend")
                    break
                else:
                    self.cap.release()
        
        if not self.cap.isOpened():
            print("[ERROR] Could not open camera!")
            print("[TIP] Try changing CAMERA_INDEX to 1 or 2")
            return False
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        
        print(f"[INFO] Camera opened successfully")
        print(f"[INFO] Resolution: {int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
        
        self.running = True
        return True
    
    def stop_camera(self):
        """Stop the camera"""
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera stopped")
    
    def capture_photo(self, frame=None):
        """Capture, save, and upload photo"""
        if frame is None:
            ret, frame = self.cap.read()
            if not ret:
                return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(PHOTOS_DIR, f"door_photo_{timestamp}.jpg")
        cv2.imwrite(filename, frame)
        self.photos_taken += 1
        print(f"[PHOTO] ✅ Saved: {filename}")
        
        # Try to upload to ImgBB first (recommended)
        image_url = upload_to_imgbb(filename)
        
        # If ImgBB not configured, try Imgur
        if not image_url:
            image_url = upload_to_imgur(filename)
        
        # Send to Blynk
        time_str = datetime.now().strftime("%H:%M:%S")
        if image_url:
            self.last_photo_url = image_url
            set_blynk_pin("V5", image_url)  # Image URL for Image widget
            set_blynk_pin("V6", f"📷 {time_str}")
            print(f"[BLYNK] ✅ Photo URL sent to V5")
        else:
            set_blynk_pin("V5", f"Photo saved locally at {time_str}")
            set_blynk_pin("V6", f"📷 {time_str}")
            print("[INFO] Photo saved locally (no upload service configured)")
        
        return filename
    
    def detect_motion(self, frame):
        """Detect motion in the frame"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Initialize previous frame
        if self.prev_frame is None:
            self.prev_frame = gray
            return False, frame
        
        # Calculate difference
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion = False
        display_frame = frame.copy()
        
        for contour in contours:
            if cv2.contourArea(contour) > MIN_CONTOUR_AREA:
                motion = True
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Update previous frame slowly
        self.prev_frame = cv2.addWeighted(self.prev_frame, 0.7, gray, 0.3, 0)
        
        return motion, display_frame
    
    def run(self):
        """Main camera loop"""
        if not self.start_camera():
            return
        
        print("\n" + "="*50)
        print("    SMART DOOR CAMERA RUNNING")
        print("="*50)
        print("Controls:")
        print("  'p' - Take a photo")
        print("  'n' - Send test notification")
        print("  'u' - Unlock door")
        print("  'l' - Lock door")
        print("  'q' - Quit")
        print("="*50 + "\n")
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("[ERROR] Failed to read frame")
                break
            
            # Detect motion
            motion, display_frame = self.detect_motion(frame)
            
            # Handle motion detection
            current_time = time.time()
            if motion:
                if current_time - self.last_motion_time > MOTION_COOLDOWN:
                    self.last_motion_time = current_time
                    self.motion_detected = True
                    print("[MOTION] Person detected at door!")
                    
                    # Take photo
                    photo_path = self.capture_photo(frame)
                    
                    # Send notification via Blynk
                    threading.Thread(
                        target=send_blynk_notification,
                        args=(f"Someone is at your door! Photo saved.",)
                    ).start()
                    
                    # Notify ESP32 via virtual pin V2
                    threading.Thread(
                        target=set_blynk_pin,
                        args=("V2", 1)
                    ).start()
            
            # Add status overlay
            status_color = (0, 255, 0) if not motion else (0, 0, 255)
            cv2.putText(display_frame, f"Status: {'MOTION!' if motion else 'Monitoring'}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            cv2.putText(display_frame, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                       (10, FRAME_HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(display_frame, f"Photos: {self.photos_taken}", 
                       (FRAME_WIDTH - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Display frame
            cv2.imshow("Smart Door Camera", display_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("[INFO] Quit requested")
                break
            elif key == ord('p'):
                self.capture_photo(frame)
            elif key == ord('n'):
                print("[TEST] Sending test notification...")
                threading.Thread(
                    target=send_blynk_notification,
                    args=("Test notification from Smart Door Camera",)
                ).start()
            elif key == ord('u'):
                print("[COMMAND] Unlocking door...")
                set_blynk_pin("V1", 1)
            elif key == ord('l'):
                print("[COMMAND] Locking door...")
                set_blynk_pin("V1", 0)
        
        self.stop_camera()


# ============= MAIN =============

if __name__ == "__main__":
    print("\n" + "="*50)
    print("   SMART DOOR CAMERA SYSTEM")
    print("="*50)
    
    # Check configuration
    if BLYNK_AUTH_TOKEN == "YOUR_AUTH_TOKEN":
        print("\n⚠️  Set BLYNK_AUTH_TOKEN in the script!")
        print("    Get it from Blynk Console > Device > Device Info\n")
    
    if IMGBB_API_KEY != "YOUR_IMGBB_API_KEY":
        print("✅ ImgBB configured - Photos will display in Blynk!\n")
    elif IMGUR_CLIENT_ID != "SKIP":
        print("✅ Imgur configured - Photos will display in Blynk!\n")
    else:
        print("ℹ️  No image hosting configured.")
        print("    Photos saved locally in 'door_photos' folder")
        print("    To display in Blynk, get FREE API key from: https://api.imgbb.com/\n")
    
    camera = SmartDoorCamera()
    
    try:
        camera.run()
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        camera.stop_camera()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        camera.stop_camera()
