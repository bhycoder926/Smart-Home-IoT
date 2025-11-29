# Circuit Diagrams

This folder contains the wiring diagrams for both ESP32 subsystems.

## Files

| File | Description |
|------|-------------|
| `Door_Lock_Circuit.png` | ESP32 #1 — Solenoid door lock with TIP122 driver, 7805 regulator, 12V battery supply |
| `Lights_Sensors_Circuit.png` | ESP32 #2 — 4-channel relay (lights), MQ-2 gas sensor, DHT11 temp/humidity, 9V battery |

## Circuit 1: Door Lock

- **Power:** 12V battery → 7805 regulator → 5V to ESP32 VIN
- **Solenoid driver:** GPIO12 → 1kΩ → TIP122 Base; Collector to solenoid; 1N4007 flyback diode
- **Capacitor:** 220µF on 7805 output for stability

## Circuit 2: Lights & Sensors

- **Power:** 9V battery → ESP32 VIN (acceptable range)
- **MQ-2 Gas Sensor:** VCC=5V, AO → GPIO32
- **DHT11:** VCC=3.3V, DATA → GPIO26
- **4-Channel Relay:** VCC=5V, IN3 ← GPIO25 (Light 1), IN4 ← GPIO33 (Light 2)

Refer to `HARDWARE_WIRING.md` in the parent folder for detailed component lists and safety notes.
