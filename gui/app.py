import os
import json
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from paho.mqtt.client import Client as MQTTClient
from pymongo import MongoClient

load_dotenv()

# --- Env / constants ----------------------------------------------------------

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "greenhouse")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

TOPIC_DHT = "greenhouse/sensors/dht"
TOPIC_LIGHT = "greenhouse/sensors/light"
TOPIC_BUTTON = "greenhouse/actuators/emergency_button"
TOPIC_KNOB = "greenhouse/actuators/knob"


# --- App & DB ----------------------------------------------------------------

app = Flask(__name__)
CORS(app)

mongo = MongoClient(MONGO_URI)
db = mongo[MONGO_DB]


# --- Helpers -----------------------------------------------------------------

def iso_utc_now() -> str:
    """RFC 3339 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def minutes_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=n)).isoformat()


def hours_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=n)).isoformat()


def mqtt_publish(topic: str, payload: dict) -> None:
    """Publish a single message (short-lived client)."""
    client = MQTTClient()
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.publish(topic, json.dumps(payload))
    client.disconnect()


# --- Pages -------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/manual")
def manual():
    return render_template("manual.html")


# --- APIs --------------------------------------------------------------------

@app.route("/api/latest")
def api_latest():
    since = minutes_ago(15)
    docs = (
        db["readings"]
        .find({"ts": {"$gte": since}}, {"_id": 0})
        .sort("ts", 1)
    )
    return jsonify(list(docs))


@app.route("/api/alerts")
def api_alerts():
    since = hours_ago(1)
    docs = (
        db["alerts"]
        .find({"ts": {"$gte": since}}, {"_id": 0})
        .sort("ts", -1)
        .limit(50)
    )
    return jsonify(list(docs))


@app.route("/api/relays")
def api_relays():
    doc = db["relays"].find_one(sort=[("_id", -1)], projection={"_id": 0})
    if not doc:
        doc = {"fan": False, "pump": False, "ts": None}
    return jsonify(doc)


# --- Manual endpoints ---------------------------------------------------------

@app.route("/api/manual/dht", methods=["POST"])
def manual_dht():
    data = request.get_json(force=True) or {}
    t = data.get("temperature")
    h = data.get("humidity")
    if t is None or h is None:
        return jsonify({"error": "temperature and humidity are required"}), 400

    mqtt_publish(
        TOPIC_DHT,
        {"temperature": float(t), "humidity": float(h), "ts": iso_utc_now()},
    )
    return jsonify({"ok": True})


@app.route("/api/manual/light", methods=["POST"])
def manual_light():
    data = request.get_json(force=True) or {}
    lux = data.get("lux")
    if lux is None:
        return jsonify({"error": "lux is required"}), 400

    mqtt_publish(TOPIC_LIGHT, {"lux": int(lux), "ts": iso_utc_now()})
    return jsonify({"ok": True})


@app.route("/api/manual/emergency", methods=["POST"])
def manual_emergency():
    mqtt_publish(TOPIC_BUTTON, {"pressed": True, "ts": iso_utc_now()})
    return jsonify({"ok": True})


@app.route("/api/manual/knob", methods=["POST"])
def manual_knob():
    data = request.get_json(force=True) or {}
    target = data.get("target")
    value = data.get("value")

    if target not in ("temperature", "humidity") or value is None:
        return (
            jsonify(
                {"error": "target must be temperature|humidity and value is required"}),
            400,
        )

    mqtt_publish(
        TOPIC_KNOB,
        {"target": target, "value": float(value), "ts": iso_utc_now()},
    )
    return jsonify({"ok": True})


# --- Run ---------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)
