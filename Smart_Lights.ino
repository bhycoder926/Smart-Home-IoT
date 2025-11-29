/*************************************************************
  SMART HOME - LIGHTS & SENSORS (ESP32 #2)
  =========================================
  
  Controls lights and monitors temperature/gas.
  Uses SAME Auth Token as Door Lock for ONE dashboard.
  
  Hardware:
  - GPIO25: Relay 1 (Light 1)
  - GPIO33: Relay 2 (Light 2)
  - GPIO32: MQ-2 Gas Sensor (Analog)
  - GPIO26: DHT11 Temperature/Humidity
  - GPIO2:  Status LED
  
  Virtual Pins (matching your existing datastreams):
  - V0: Light 1 Control
  - V1: Light 2 Control
  - V2: Temperature Display
  - V3: Humidity Display
  - V4: Gas Level Display
  
  Author: Bhyresh
  Date: November 2025
*************************************************************/

// ==================== BLYNK CREDENTIALS ====================
// DIFFERENT Auth Token from Door Lock - Lights Device
#define BLYNK_TEMPLATE_ID "TMPL3wb1zwGMa"
#define BLYNK_TEMPLATE_NAME "Smart Home"
#define BLYNK_AUTH_TOKEN "31zwAyXYhMpGo2QCX4Vu8eqOV36IUMBT"

#define BLYNK_PRINT Serial

// ==================== LIBRARIES ====================
#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include <DHT.h>

// ==================== WIFI CREDENTIALS ====================
char ssid[] = "vivo T3 5G";
char pass[] = "htbs*926";

// ==================== PIN DEFINITIONS ====================
#define RELAY1_PIN    25    // Light 1
#define RELAY2_PIN    33    // Light 2
#define GAS_PIN       32    // MQ-2 Gas Sensor
#define DHT_PIN       26    // DHT11 Sensor
#define LED_PIN       2     // Status LED

// ==================== DHT SENSOR ====================
#define DHT_TYPE DHT11
DHT dht(DHT_PIN, DHT_TYPE);

// ==================== SETTINGS ====================
#define GAS_THRESHOLD 600

// ==================== GLOBAL VARIABLES ====================
bool light1State = false;
bool light2State = false;
bool gasAlertSent = false;

BlynkTimer timer;

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n========================================");
  Serial.println("   SMART HOME - LIGHTS & SENSORS");
  Serial.println("         (ESP32 #2)");
  Serial.println("========================================");
  
  // Initialize pins
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(GAS_PIN, INPUT);
  
  // Start with relays OFF (Active LOW)
  digitalWrite(RELAY1_PIN, HIGH);
  digitalWrite(RELAY2_PIN, HIGH);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("[INIT] Relays initialized (OFF)");
  
  // Initialize DHT sensor
  dht.begin();
  Serial.println("[INIT] DHT11 sensor initialized");
  
  // Connect to WiFi and Blynk
  Serial.println("[WIFI] Connecting...");
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
  
  Serial.println("[WIFI] Connected!");
  Serial.print("[WIFI] IP: ");
  Serial.println(WiFi.localIP());
  
  // Setup timers
  timer.setInterval(5000L, readSensors);      // Read sensors every 5 sec
  timer.setInterval(10000L, sendHeartbeat);   // Heartbeat every 10 sec
  
  // Sync with Blynk
  Blynk.syncVirtual(V0, V1);
  
  Serial.println("\n========================================");
  Serial.println("   SYSTEM READY!");
  Serial.println("========================================\n");
}

// ==================== MAIN LOOP ====================
void loop() {
  Blynk.run();
  timer.run();
}

// ==================== LIGHT CONTROL ====================
void setLight(int lightNum, bool state) {
  if (lightNum == 1) {
    digitalWrite(RELAY1_PIN, state ? LOW : HIGH);  // Active LOW
    light1State = state;
    Serial.print("[LIGHT] Light 1 → ");
  } else {
    digitalWrite(RELAY2_PIN, state ? LOW : HIGH);  // Active LOW
    light2State = state;
    Serial.print("[LIGHT] Light 2 → ");
  }
  Serial.println(state ? "ON" : "OFF");
  
  // Update status LED
  digitalWrite(LED_PIN, (light1State || light2State) ? HIGH : LOW);
}

// ==================== BLYNK HANDLERS ====================

// Light 1 Control (V0)
BLYNK_WRITE(V0) {
  bool state = param.asInt() == 1;
  setLight(1, state);
}

// Light 2 Control (V1)
BLYNK_WRITE(V1) {
  bool state = param.asInt() == 1;
  setLight(2, state);
}

// When connected to Blynk
BLYNK_CONNECTED() {
  Serial.println("[BLYNK] Connected to server!");
  Blynk.syncVirtual(V0, V1);
}

// ==================== SENSOR READING ====================
void readSensors() {
  Serial.println("\n---------------------------------");
  
  // Read DHT11
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  
  if (!isnan(temp) && !isnan(hum)) {
    Blynk.virtualWrite(V2, temp);
    Blynk.virtualWrite(V3, hum);
    
    Serial.print("🌡️ Temp: ");
    Serial.print(temp);
    Serial.print("°C | Humidity: ");
    Serial.print(hum);
    Serial.println("%");
  } else {
    Serial.println("❌ DHT read failed");
  }
  
  // Read Gas Sensor
  int gasLevel = analogRead(GAS_PIN);
  Blynk.virtualWrite(V4, gasLevel);
  
  Serial.print("💨 Gas Level: ");
  Serial.print(gasLevel);
  
  if (gasLevel > GAS_THRESHOLD) {
    Serial.println(" 🚨 GAS DETECTED!");
    if (!gasAlertSent) {
      Blynk.logEvent("gas_alert", "🚨 Gas Leakage Detected!");
      gasAlertSent = true;
    }
  } else {
    Serial.println(" ✓ Normal");
    gasAlertSent = false;
  }
}

// ==================== HEARTBEAT ====================
void sendHeartbeat() {
  Serial.print("[STATUS] Lights: ");
  Serial.print(light1State ? "1-ON " : "1-OFF ");
  Serial.print(light2State ? "2-ON" : "2-OFF");
  Serial.print(" | Uptime: ");
  Serial.print(millis() / 1000);
  Serial.println("s");
}
