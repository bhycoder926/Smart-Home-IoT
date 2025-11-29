# Hardware Wiring & Components — Smart Home Project

This document provides all hardware details: component list, wiring tables, circuit notes, and power-supply guidance for the Smart Home project (two ESP32 Dev Modules + laptop camera).

---

## 1. Components List (Bill of Materials)

| Qty | Component | Notes |
|-----|-----------|-------|
| 2 | ESP32 Dev Module (30-pin) | One for door lock, one for lights/sensors |
| 1 | 12V Solenoid Lock | Electric door lock (≈0.5–1 A draw) |
| 1 | TIP122 NPN Darlington Transistor | Drives solenoid from ESP32 GPIO |
| 1 | 1N4007 Flyback Diode | Protects transistor when solenoid switches off |
| 1 | 1 kΩ Resistor | Base resistor for TIP122 |
| 1 | 4-Channel Relay Module (5V, active-LOW) | Controls two lights (IN3, IN4 used) |
| 1 | DHT11 Sensor | Temperature & humidity |
| 1 | MQ-2 Gas Sensor Module | Detects LPG/smoke (analog output) |
| 2 | 7805 Voltage Regulator (TO-220) | Converts 12V → 5V for each ESP32 |
| 2 | 100 µF Electrolytic Capacitors | Smoothing caps for 7805 output |
| 2 | 0.1 µF Ceramic Capacitors | Decoupling caps for 7805 input |
| 1 | 12V 2A DC Adapter | Powers solenoid & regulators |
| – | Jumper wires, breadboard, screw terminals | As needed |
| 1 | Laptop with Webcam | Runs Python camera script |

Optional:
- Heat-sinks for 7805 regulators if running for extended periods.
- External USB power bank (5V 2A) as an alternative to the 12V + regulator setup.

---

## 2. ESP32 #1 — Door Lock Wiring

**Purpose:** Controls the 12V solenoid lock and reports status to Blynk.

| ESP32 Pin | Connects To | Notes |
|-----------|-------------|-------|
| GPIO12 | TIP122 Base via 1 kΩ resistor | HIGH = unlock (transistor ON) |
| GPIO2 | On-board LED (directly) | Status indicator |
| 3.3V | — | Not used for solenoid circuit |
| 5V (VIN) | 7805 Output (+5V) | Power from regulator |
| GND | Common ground | Shared with 12V supply, TIP122 emitter |

### Solenoid Driver Circuit (TIP122)

```
         +12V ────────┬────────────────────┐
                      │                    │
                   ┌──┴──┐            Solenoid
                   │     │              (+)
                 1N4007 (flyback)        │
                   │     │               │
                   └──┬──┘               │
                      │                  │
                      └───── Solenoid (−)┘
                                  │
                             TIP122
                         Collector ↑
                                  │
          GPIO12 ──[1kΩ]── Base   │
                                  │
                         Emitter ──┴── GND (common)
```

- When GPIO12 goes HIGH, the TIP122 turns on, completing the 12V circuit through the solenoid.
- The 1N4007 across the solenoid protects against voltage spikes.

---

## 3. ESP32 #2 — Lights & Sensors Wiring

**Purpose:** Drives two relays (lights) and reads DHT11 + MQ-2 sensors.

| ESP32 Pin | Connects To | Notes |
|-----------|-------------|-------|
| GPIO25 | Relay Module IN3 | Light 1 control (active LOW) |
| GPIO33 | Relay Module IN4 | Light 2 control (active LOW) |
| GPIO26 | DHT11 Data pin | Pull-up to 3.3V via 10 kΩ (often built-in on module) |
| GPIO32 | MQ-2 AO (Analog Out) | 0–3.3V analog |
| GPIO2 | On-board LED | Status (lights any relay on) |
| 5V (VIN) | 7805 Output (+5V) | Power from regulator |
| GND | Common ground | Relay VCC-GND, sensor GND |

### Relay Module Connections

| Relay Pin | Connects To |
|-----------|-------------|
| VCC | ESP32 5V (VIN) or external 5V |
| GND | ESP32 GND |
| IN3 | ESP32 GPIO25 |
| IN4 | ESP32 GPIO33 |
| COM3 / NO3 | Mains Live line (interrupted by relay) |
| COM4 / NO4 | Second mains line |

> ⚠️ **Safety:** Connecting mains (220V AC) to relay contacts must follow local electrical codes. Use proper insulation and avoid touching live wires.

### DHT11 Connections

| DHT11 Pin | Connects To |
|-----------|-------------|
| VCC | ESP32 3.3V |
| GND | ESP32 GND |
| DATA | ESP32 GPIO26 (with 10 kΩ pull-up to 3.3V if not on module) |

### MQ-2 Gas Sensor Connections

| MQ-2 Pin | Connects To |
|----------|-------------|
| VCC | ESP32 5V (required by heater) |
| GND | ESP32 GND |
| AO | ESP32 GPIO32 |

---

## 4. Power Supply Design (12V → 5V)

Both ESP32s can be powered from a single 12V adapter using 7805 regulators (one per ESP32 recommended to avoid overheating).

### Single ESP32 Power Circuit

```
+12V ──┬──[0.1µF]──┬── 7805 IN ───── 7805 OUT ──┬──[100µF]──┬── +5V to ESP32 VIN
       │           │                            │           │
      GND         GND                          GND         GND
```

- Input capacitor (0.1 µF ceramic): filters high-frequency noise.
- Output capacitor (100 µF electrolytic): stabilizes 5V output.
- The 7805 GND pin connects to the common ground shared by ESP32, solenoid circuit, and 12V supply negative.

> **Tip:** If powering **two** ESP32s, use **two separate 7805 regulators** to split the load. A single 7805 can supply ~1 A; each ESP32 with peripherals can draw 200–400 mA, so two regulators keep things cool.

### Alternative: USB Power Bank

You can skip the 7805 circuit entirely and power each ESP32 from a USB power bank (5V 2A) connected to its micro-USB port. The solenoid still needs the 12V supply; just share a common ground between the 12V negative and the ESP32 GND.

---

## 5. Common Ground Reminder

All circuits **must share a common ground**:
- 12V adapter (−)
- TIP122 emitter
- ESP32 GND (both boards)
- Relay module GND
- Sensor GNDs (DHT11, MQ-2)
- 7805 GND pins

Without a common ground, GPIO signals cannot switch transistors or relays reliably.

---

## 6. Flashing / Upload Tips

- Disconnect the solenoid and relay loads while flashing the ESP32 to avoid power surges that cause upload failures ("chip stopped responding").
- Use a **data-capable** USB cable (not a charge-only cable).
- If upload fails, hold the **BOOT** button on the ESP32 while clicking upload, then release after upload starts.
- Lower the upload baud rate to 115200 if you see frequent timeouts.

---

## 7. Quick Reference — GPIO Summary

| GPIO | ESP32 #1 (Lock) | ESP32 #2 (Lights) |
|------|-----------------|-------------------|
| 2 | Status LED | Status LED |
| 12 | Solenoid (TIP122) | — |
| 25 | — | Relay IN3 (Light 1) |
| 26 | — | DHT11 Data |
| 32 | — | MQ-2 Analog Out |
| 33 | — | Relay IN4 (Light 2) |

---

## 8. Safety Notes

- Never connect 12V directly to ESP32 VIN — always use a 5V regulator.
- Use a flyback diode on all inductive loads (solenoid, relay coils).
- Avoid auto-unlock automation without manual verification (security risk).
- If handling mains voltage on relay outputs, follow your country's electrical safety standards and consider using a licensed electrician.

---

If you have questions about component sourcing or alternative parts, feel free to ask!
