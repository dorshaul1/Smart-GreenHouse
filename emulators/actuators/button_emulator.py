import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from paho.mqtt.client import Client as MQTTClient

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_EMERGENCY = "greenhouse/actuators/emergency_button"


def iso_utc_now() -> str:
    """RFC 3339 timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat()


def publish_emergency(client: MQTTClient) -> None:
    payload = {"pressed": True, "ts": iso_utc_now()}
    client.publish(TOPIC_EMERGENCY, json.dumps(payload))
    print("[BUTTON] EMERGENCY sent")


def main() -> None:
    client = MQTTClient(client_id="button_emulator")
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

    print("[BUTTON] Press Enter to send EMERGENCY; Ctrl+C to exit.")
    try:
        while True:
            input()  # wait for Enter
            publish_emergency(client)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
