import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from paho.mqtt.client import Client as MQTTClient
from pymongo import MongoClient

load_dotenv()


# ----------------------------
# Env & constants
# ----------------------------
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "greenhouse")

TEMP_MAX_DEFAULT = float(os.getenv("TEMP_MAX", "35"))
HUM_MIN_DEFAULT = float(os.getenv("HUM_MIN", "20"))

TOPIC_DHT = "greenhouse/sensors/dht"
TOPIC_LIGHT = "greenhouse/sensors/light"
TOPIC_BUTTON = "greenhouse/actuators/emergency_button"
TOPIC_KNOB = "greenhouse/actuators/knob"
TOPIC_ALERTS = "greenhouse/alerts"
TOPIC_COMMANDS = "greenhouse/controls/commands"

SUBSCRIPTIONS = (TOPIC_DHT, TOPIC_LIGHT, TOPIC_BUTTON, TOPIC_KNOB)


# ----------------------------
# Helpers
# ----------------------------
def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def try_json(data: bytes | str) -> Optional[Dict[str, Any]]:
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="ignore")
    try:
        return json.loads(data)
    except Exception:
        return None


# ----------------------------
# Main service
# ----------------------------
class GreenhouseHub:
    def __init__(self) -> None:
        # Mongo setup
        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[MONGO_DB]
        self.readings_col = self.db["readings"]
        self.alerts_col = self.db["alerts"]
        self.relays_col = self.db["relays"]

        # Thresholds (hot-swappable at runtime via knob)
        self.thresholds = {
            "TEMP_MAX": TEMP_MAX_DEFAULT,
            "HUM_MIN": HUM_MIN_DEFAULT,
        }

        # MQTT setup
        self.mqtt = MQTTClient(client_id="data_manager")
        self.mqtt.on_connect = self._on_connect
        self.mqtt.on_message = self._on_message
        self.mqtt.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

        print(
            f"[Hub] MQTT {MQTT_HOST}:{MQTT_PORT} | Mongo {MONGO_URI} DB={MONGO_DB}")
        print(f"[Hub] Thresholds: {self.thresholds}")

    # ------------------------
    # MQTT callbacks
    # ------------------------
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        print("[Hub] MQTT connected")
        for topic in SUBSCRIPTIONS:
            client.subscribe(topic)

    def _on_message(self, client, userdata, msg):
        payload = try_json(msg.payload)
        if not payload:
            print(f"[Warn] Non-JSON on {msg.topic}")
            return

        payload.setdefault("ts", iso_utc_now())

        if msg.topic in (TOPIC_DHT, TOPIC_LIGHT):
            sensor = "dht" if msg.topic == TOPIC_DHT else "light"
            payload["sensor"] = sensor
            self.readings_col.insert_one(dict(payload))
            print(f"[Data] {sensor}: {payload}")
            if sensor == "dht":
                self._handle_dht(payload)

        elif msg.topic == TOPIC_BUTTON:
            if payload.get("pressed"):
                self._alert("alarm", "Emergency button pressed → relays OFF")
                self._set_relays(fan=False, pump=False)

        elif msg.topic == TOPIC_KNOB:
            self._handle_knob(payload)

    # ------------------------
    # Logic
    # ------------------------
    def _handle_dht(self, doc: Dict[str, Any]) -> None:
        t = doc.get("temperature")
        h = doc.get("humidity")

        if isinstance(t, (int, float)) and t > self.thresholds["TEMP_MAX"]:
            self._alert(
                "warning",
                f"High temperature: {t}°C > {self.thresholds['TEMP_MAX']} → fan ON",
            )
            self._set_relays(fan=True)

        if isinstance(h, (int, float)) and h < self.thresholds["HUM_MIN"]:
            self._alert(
                "warning",
                f"Low humidity: {h}% < {self.thresholds['HUM_MIN']} → pump ON",
            )
            self._set_relays(pump=True)

    def _handle_knob(self, payload: Dict[str, Any]) -> None:
        target = payload.get("target")
        value = payload.get("value")

        if target == "temperature" and isinstance(value, (int, float)):
            self.thresholds["TEMP_MAX"] = float(value)
            self._alert("info", f"Temperature threshold updated to {value}°C")
        elif target == "humidity" and isinstance(value, (int, float)):
            self.thresholds["HUM_MIN"] = float(value)
            self._alert("info", f"Humidity threshold updated to {value}%")
        else:
            self._alert("info", f"Knob received: {payload}")

    # ------------------------
    # Effects (DB + MQTT)
    # ------------------------
    def _alert(self, level: str, message: str) -> None:
        doc = {"level": level, "message": message, "ts": iso_utc_now()}
        # Insert a copy so MongoDB's _id doesn't pollute the published payload
        self.alerts_col.insert_one(dict(doc))
        self.mqtt.publish(TOPIC_ALERTS, json.dumps(doc), qos=1)
        print(f"[Alert] {level.upper()}: {message}")

    def _set_relays(self, fan: Optional[bool] = None, pump: Optional[bool] = None) -> None:
        # Start from last known state; default to both OFF
        last = self.relays_col.find_one(
            sort=[("_id", -1)]) or {"fan": False, "pump": False}
        if fan is not None:
            last["fan"] = bool(fan)
        if pump is not None:
            last["pump"] = bool(pump)

        last["ts"] = iso_utc_now()
        self.relays_col.insert_one(dict(last))

        to_publish = {"fan": last["fan"], "pump": last["pump"]}
        self.mqtt.publish(TOPIC_COMMANDS, json.dumps(to_publish), qos=1)
        print(f"[Cmd] fan={to_publish['fan']} pump={to_publish['pump']}")

    # ------------------------
    # Run loop
    # ------------------------
    def run(self) -> None:
        self.mqtt.loop_start()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.mqtt.loop_stop()
            self.mqtt.disconnect()
            self.mongo.close()


if __name__ == "__main__":
    GreenhouseHub().run()
