# run_all.py
import subprocess
import sys
import os
import time

services = [
    ("Data Manager", ["python", "data_manager/manager.py"]),
    ("Relay Controller", ["python", "emulators/relays/relay_controller.py"]),
    ("DHT Emulator", ["python", "emulators/sensors/dht_emulator.py"]),
    ("Light Emulator", ["python", "emulators/sensors/light_emulator.py"]),
    ("GUI", ["python", "gui/app.py"]),
]

processes = []

env = os.environ.copy()
env.setdefault("MQTT_HOST", "localhost")
env.setdefault("MQTT_PORT", "1883")
env.setdefault("MONGO_URI", "mongodb://localhost:27017")
env.setdefault("MONGO_DB", "greenhouse")
env.setdefault("FLASK_PORT", "5001")

try:
    print("🚀 Starting Smart Greenhouse services...\n")
    for name, cmd in services:
        print(f"→ Starting {name}...")
        p = subprocess.Popen(cmd, env=env)
        processes.append((name, p))
        time.sleep(1)

    print("\n✅ All services are running. Press Ctrl+C to stop.\n")

    # Wait for all processes
    for _, p in processes:
        p.wait()

except KeyboardInterrupt:
    print("\n🛑 Stopping all services...")
    for name, p in processes:
        p.terminate()
    sys.exit(0)
