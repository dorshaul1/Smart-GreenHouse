async function fetchJSON(url) {
  const res = await fetch(url);
  try {
    return await res.json();
  } catch {
    return null;
  }
}

function tsToLocal(ts) {
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return ts;
  }
}

let dhtChart, lightChart;

function chartOptions() {
  return {
    responsive: true,
    interaction: { mode: "nearest", intersect: false },
    scales: {
      x: { type: "time", time: { unit: "minute" } },
      y: { beginAtZero: false },
    },
    plugins: {
      legend: { labels: { color: "#eef2ff" } },
    },
  };
}

function makeLineChart(canvas, datasets = []) {
  return new Chart(canvas, {
    type: "line",
    data: { datasets },
    options: chartOptions(),
  });
}

function mapDHT(readings) {
  const temp = [];
  const hum = [];
  readings
    .filter((r) => r.sensor === "dht")
    .forEach((r) => {
      temp.push({ x: r.ts, y: r.temperature });
      hum.push({ x: r.ts, y: r.humidity });
    });
  return { temp, hum };
}

function mapLight(readings) {
  const lux = [];
  readings
    .filter((r) => r.sensor === "light")
    .forEach((r) => lux.push({ x: r.ts, y: r.lux }));
  return lux;
}

function renderRelays(relays) {
  const el = document.getElementById("relays");
  if (!el || !relays) return;

  el.innerHTML = `
    <div class="chip ${relays.fan ? "on" : ""}">Fan: ${
    relays.fan ? "ON" : "OFF"
  }</div>
    <div class="chip ${relays.pump ? "on" : ""}">Pump: ${
    relays.pump ? "ON" : "OFF"
  }</div>
    <div class="chip">Updated: ${relays.ts ? tsToLocal(relays.ts) : "-"}</div>
    <a href="/manual" style="color: var(--accent); text-decoration:none; margin-left:8px;">Manual →</a>
  `;
}

function renderAlerts(alerts) {
  const list = document.getElementById("alertsList");
  if (!list || !Array.isArray(alerts)) return;

  list.innerHTML = alerts
    .map(
      (a) =>
        `<li class="alert ${a.level}">
          <strong>${a.level.toUpperCase()}</strong> - ${a.message}
          <small>(${tsToLocal(a.ts)})</small>
        </li>`
    )
    .join("");
}

async function refresh() {
  const [readings, alerts, relays] = await Promise.all([
    fetchJSON("/api/latest"),
    fetchJSON("/api/alerts"),
    fetchJSON("/api/relays"),
  ]);

  // Relays
  renderRelays(relays);

  // DHT
  const { temp, hum } = mapDHT(Array.isArray(readings) ? readings : []);
  dhtChart.data.datasets = [
    { label: "Temperature (°C)", data: temp },
    { label: "Humidity (%)", data: hum },
  ];
  dhtChart.update();

  // Light
  const lux = mapLight(Array.isArray(readings) ? readings : []);
  lightChart.data.datasets = [{ label: "Lux", data: lux }];
  lightChart.update();

  // Alerts
  renderAlerts(Array.isArray(alerts) ? alerts : []);
}

async function refreshRelaysOnly() {
  const relays = await fetchJSON("/api/relays");
  renderRelays(relays);
}

async function init() {
  dhtChart = makeLineChart(document.getElementById("dhtChart"), [
    { label: "Temperature (°C)", data: [] },
    { label: "Humidity (%)", data: [] },
  ]);

  lightChart = makeLineChart(document.getElementById("lightChart"), [
    { label: "Lux", data: [] },
  ]);

  await refresh();

  setInterval(refresh, 60_000);
  setInterval(refreshRelaysOnly, 5_000);
}

window.addEventListener("load", init);
