async function postJSON(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data || {}),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function num(id, parser = parseFloat) {
  const v = document.getElementById(id)?.value ?? "";
  const n = parser(v);
  return Number.isNaN(n) ? null : n;
}

async function sendDHT() {
  const temp = num("temp", parseFloat);
  const hum = num("hum", parseFloat);
  const statusId = "dhtStatus";

  try {
    await postJSON("/api/manual/dht", { temperature: temp, humidity: hum });
    setText(statusId, "Sent ✓");
  } catch (e) {
    setText(statusId, "Error: " + e.message);
  }
}

async function sendLight() {
  const lux = num("lux", (v) => parseInt(v, 10));
  const statusId = "lightStatus";

  try {
    await postJSON("/api/manual/light", { lux });
    setText(statusId, "Sent ✓");
  } catch (e) {
    setText(statusId, "Error: " + e.message);
  }
}

async function sendEmergency() {
  const statusId = "btnStatus";

  try {
    await postJSON("/api/manual/emergency", {});
    setText(statusId, "Emergency sent!");
  } catch (e) {
    setText(statusId, "Error: " + e.message);
  }
}

async function sendKnob() {
  const target = document.getElementById("target")?.value;
  const value = num("tval", parseFloat);
  const statusId = "knobStatus";

  try {
    await postJSON("/api/manual/knob", { target, value });
    setText(statusId, "Threshold updated ✓");
  } catch (e) {
    setText(statusId, "Error: " + e.message);
  }
}
