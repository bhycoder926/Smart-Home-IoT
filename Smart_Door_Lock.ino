/*************************************************************
  Smart Door Lock System - ESP32
  ==============================
  
  This controls a 12V solenoid lock using ESP32 and Blynk.
  
  Features:
  - Control lock from Blynk app
  - Auto-lock after timeout
  - Status LED indicator
  
  Hardware Connections (ESP32 Dev Module):
  - GPIO12: Solenoid Lock (via TIP122 transistor)
  - GPIO2:  Built-in LED (status indicator)
  
  Blynk Virtual Pins:
  - V7: Lock Status Display (String)
  - V8: Lock Control Button (0=Locked, 1=Unlocked)
  
  Author: Bhyresh
  Date: November 2025
 *************************************************************/

// ==================== BLYNK CREDENTIALS ====================
// Using Smart Home Automation template
#define BLYNK_TEMPLATE_ID "TMPL3wb1zwGMa"
#define BLYNK_TEMPLATE_NAME "Smart Home Automation"
#define BLYNK_AUTH_TOKEN "_U7v-3wvBTNh7ODSoZfjxihGnOWPTs7Z"      // Replace with your Auth Token

#define BLYNK_PRINT Serial

// ==================== LIBRARIES ====================
#include <WiFi.h>
#include <BlynkSimpleEsp32.h>

// ==================== WIFI CREDENTIALS ====================
char ssid[] = "vivo T3 5G";
char pass[] = "htbs*926";

// ==================== PIN DEFINITIONS ====================
#define LOCK_PIN      12    // GPIO12 - Solenoid lock control (via TIP122)
#define LED_PIN       2     // GPIO2  - Built-in LED for status

// ==================== LOCK STATES ====================
#define LOCKED    0
#define UNLOCKED  1

// ==================== TIMING SETTINGS ====================
#define AUTO_LOCK_DELAY    5000    // Auto-lock after 5 seconds (milliseconds)

// ==================== GLOBAL VARIABLES ====================
int lockState = LOCKED;
unsigned long unlockTime = 0;

BlynkTimer timer;

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(100);
  
  printHeader();
  
  // Initialize pins
  pinMode(LOCK_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Start with door locked
  setLock(LOCKED);
  
  // Connect to WiFi and Blynk
  Serial.println("[WIFI] Connecting...");
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
  
  Serial.println("[WIFI] Connected!");
  Serial.print("[WIFI] IP Address: ");
  Serial.println(WiFi.localIP());
  
  // Setup timers
  timer.setInterval(500L, checkAutoLock);    // Check auto-lock every 500ms
  timer.setInterval(10000L, sendHeartbeat);  // Heartbeat every 10 seconds
  
  // Sync with Blynk
  Blynk.syncVirtual(V8);
  
  Serial.println("\n[READY] System is ready!");
  Serial.println("========================================\n");
}

// ==================== MAIN LOOP ====================
void loop() {
  Blynk.run();
  timer.run();
}

// ==================== LOCK CONTROL ====================
void setLock(int state) {
  lockState = state;
  digitalWrite(LOCK_PIN, state);
  digitalWrite(LED_PIN, state);  // LED ON when unlocked
  
  // Update Blynk
  if (state == UNLOCKED) {
    Blynk.virtualWrite(V7, "🔓 UNLOCKED");
    unlockTime = millis();
    Serial.println("[LOCK] Door UNLOCKED");
  } else {
    Blynk.virtualWrite(V7, "🔒 LOCKED");
    Serial.println("[LOCK] Door LOCKED");
  }
  Blynk.virtualWrite(V8, state);
}

// ==================== BLYNK HANDLERS ====================

// V8: Lock control button from Blynk app
BLYNK_WRITE(V8) {
  int value = param.asInt();
  Serial.print("[BLYNK] Lock command: ");
  Serial.println(value == UNLOCKED ? "UNLOCK" : "LOCK");
  setLock(value);
}

// When Blynk connects
BLYNK_CONNECTED() {
  Serial.println("[BLYNK] Connected to server!");
  Blynk.syncVirtual(V8);
}

// ==================== AUTO-LOCK ====================
void checkAutoLock() {
  if (lockState == UNLOCKED) {
    if (millis() - unlockTime > AUTO_LOCK_DELAY) {
      Serial.println("[AUTO] Auto-locking door...");
      setLock(LOCKED);
    }
  }
}

// ==================== HEARTBEAT ====================
void sendHeartbeat() {
  // Print status (removed V3 to avoid conflict with Humidity)
  Serial.print("[STATUS] Uptime: ");
  Serial.print(millis() / 1000);
  Serial.print("s | Lock: ");
  Serial.print(lockState == UNLOCKED ? "UNLOCKED" : "LOCKED");
  Serial.print(" | WiFi: ");
  Serial.println(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
}

// ==================== UTILITY ====================
void printHeader() {
  Serial.println("\n");
  Serial.println("========================================");
  Serial.println("    SMART DOOR LOCK SYSTEM - ESP32");
  Serial.println("========================================");
  Serial.println("Controls:");
  Serial.println("  Blynk app = Remote control");
  Serial.println("  Auto-lock after 5 seconds");
  Serial.println("========================================\n");
}
