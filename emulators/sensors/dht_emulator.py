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
TOPIC_DHT = "greenhouse/sensors/dht"


def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def next_reading(t: float, h: float) -> tuple[float, float, dict]:
    # Small random drift for realism
    t += random.uniform(-0.3, 0.5)
    h += random.uniform(-1.0, 1.0)
    payload = {
        "temperature": round(t, 2),
        "humidity": round(h, 2),
        "ts": iso_utc_now(),
    }
    return t, h, payload


def main() -> None:
    client = MQTTClient(client_id="dht_emulator")
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

    print(f"[DHT] → {MQTT_HOST}:{MQTT_PORT} topic {TOPIC_DHT}")

    temp, hum = 28.0, 45.0
    try:
        while True:
            temp, hum, payload = next_reading(temp, hum)
            client.publish(TOPIC_DHT, json.dumps(payload))
            print("[DHT]", payload)
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
