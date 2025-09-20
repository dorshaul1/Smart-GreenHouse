import json
import os
import random
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from paho.mqtt.client import Client as MQTTClient

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_LIGHT = "greenhouse/sensors/light"


def iso_utc_now() -> str:
    """RFC 3339 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def next_lux(current: int) -> tuple[int, dict]:
    """Small random walk for lux readings."""
    nxt = max(0, current + random.randint(-15, 15))
    payload = {"lux": int(nxt), "ts": iso_utc_now()}
    return nxt, payload


def main() -> None:
    client = MQTTClient(client_id="light_emulator")
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

    print(f"[LIGHT] → {MQTT_HOST}:{MQTT_PORT} topic {TOPIC_LIGHT}")

    lux = 300
    try:
        while True:
            lux, payload = next_lux(lux)
            client.publish(TOPIC_LIGHT, json.dumps(payload))
            print("[LIGHT]", payload)
            time.sleep(2.5)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
