import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from paho.mqtt.client import Client as MQTTClient

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_KNOB = "greenhouse/actuators/knob"


def iso_utc_now() -> str:
    """RFC 3339 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def make_payload(kind: str, value: float) -> dict:
    """Build a knob message for temperature or humidity."""
    target = "temperature" if kind == "t" else "humidity"
    return {"target": target, "value": value, "ts": iso_utc_now()}


def main() -> None:
    client = MQTTClient(client_id="knob_emulator")
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

    print("Use: 't 32' to set TEMP_MAX, or 'h 25' to set HUM_MIN. Ctrl+C to exit.")
    try:
        while True:
            raw = input("> ").strip()
            if not raw:
                continue

            parts = raw.split()
            if len(parts) != 2:
                print("Format: t 32 | h 25")
                continue

            kind, value_str = parts[0].lower(), parts[1]

            if kind not in ("t", "h"):
                print("Unknown target. Use 't' (temperature) or 'h' (humidity).")
                continue

            try:
                value = float(value_str)
            except ValueError:
                print("Value must be a number.")
                continue

            payload = make_payload(kind, value)
            client.publish(TOPIC_KNOB, json.dumps(payload))
            print("[KNOB] sent:", payload)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
