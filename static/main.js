let chart;

async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function loadSymbols() {
  const symbols = await fetchJSON("/api/symbols");
  const sel = document.getElementById("symbolSelect");
  sel.innerHTML = "";
  symbols.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s; opt.textContent = s;
    sel.appendChild(opt);
  });
  return symbols[0];
}

function renderChart(labels, data, label) {
  const ctx = document.getElementById("priceChart");
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        fill: false,
        tension: 0.2,
        pointRadius: 2
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { ticks: { callback: v => "$" + v } }
      }
    }
  });
}

async function loadSeries(symbol) {
  const data = await fetchJSON(`/api/series?symbol=${encodeURIComponent(symbol)}`);
  renderChart(data.dates, data.prices, `${data.symbol} price`);
}

document.addEventListener("DOMContentLoaded", async () => {
  const defaultSymbol = await loadSymbols();
  await loadSeries(defaultSymbol);

  const sel = document.getElementById("symbolSelect");
  sel.addEventListener("change", e => loadSeries(e.target.value));

  document.getElementById("reloadBtn").addEventListener("click", async () => {
    await loadSeries(sel.value);
  });
});
