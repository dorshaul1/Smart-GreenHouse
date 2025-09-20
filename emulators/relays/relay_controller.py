import json
import os
import time
from datetime import datetime, timezone
from typing import Dict

from dotenv import load_dotenv
from paho.mqtt.client import Client as MQTTClient

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_COMMANDS = "greenhouse/controls/commands"


def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RelayController:
    def __init__(self) -> None:
        self.state: Dict[str, object] = {
            "fan": False, "pump": False, "ts": None}
        self.client = MQTTClient(client_id="relay_controller")
        self.client.on_message = self._on_message

    def _on_message(self, client, userdata, msg) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8", errors="ignore"))
        except Exception:
            print("[Relay] Non-JSON")
            return

        # Update state with new values, keep existing if missing
        if "fan" in payload:
            self.state["fan"] = bool(payload["fan"])
        if "pump" in payload:
            self.state["pump"] = bool(payload["pump"])
        self.state["ts"] = iso_utc_now()

        print(
            f"[Relay] fan={self.state['fan']} pump={self.state['pump']} @ {self.state['ts']}")

    def run(self) -> None:
        self.client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        self.client.subscribe(TOPIC_COMMANDS)
        print(
            f"[Relay] Listening {MQTT_HOST}:{MQTT_PORT} topic {TOPIC_COMMANDS}")

        self.client.loop_start()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == "__main__":
    RelayController().run()
