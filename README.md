# 🌱 Smart Greenhouse IOT

A complete **IOT greenhouse system** for real-time monitoring and control.

Includes:

- Sensor & actuator emulators
- Data Manager for collecting and processing readings
- Web GUI (Flask + Chart.js) for live dashboards and alerts
- MongoDB database and MQTT broker (:contentReference[oaicite:0]{index=0}) via :contentReference[oaicite:1]{index=1}

---

## Quick Start (with :contentReference[oaicite:2]{index=2})

### Prerequisites

- :contentReference[oaicite:3]{index=3} (or Docker Engine on Linux)
- Docker Compose

```bash
git clone https://github.com/GuyBloch29/Smart_GreenHouse
cd Smart_GreenHouse
```

### Build & Run

```bash
docker compose up -d --build
```

Check status:

```bash
docker compose ps
```

### Access the UI

- Dashboard: http://localhost:5001
- Manual Input: http://localhost:5001/manual
- Mongo Express: http://localhost:8081

### Stop

```bash
docker compose down
```
