const API_BASE = "https://stock-terminal-371c.onrender.com";

document.getElementById("fetchBtn").addEventListener("click", handleSearch);
document.getElementById("ticker").addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleSearch();
});

function animateNumber(el, target, prefix = "") {
  const start = 0;
  const duration = 600;
  const startTime = performance.now();

  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const value = start + (target - start) * progress;
    el.textContent = `${prefix}${value.toFixed(2)}`;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function addLog(text) {
  const logBody = document.getElementById("logBody");
  const muted = logBody.querySelector(".muted");
  if (muted) muted.remove();

  const line = document.createElement("div");
  line.className = "log-line";
  const time = new Date().toLocaleTimeString();
  line.textContent = `[${time}] ${text}`;
  logBody.prepend(line);
}

async function handleSearch() {
  const query = document.getElementById("ticker").value.trim();
  if (!query) return;

  addLog(`Searching for "${query}"...`);

  try {
    const searchRes = await fetch(`${API_BASE}/search/${encodeURIComponent(query)}`);
    const matches = await searchRes.json();

    if (!matches.length) {
      addLog(`No NSE/BSE match found for "${query}"`);
      return;
    }

    const match = matches.find(m => m.symbol.endsWith(".NS")) || matches[0];
    addLog(`Resolved to ${match.symbol} (${match.name})`);

    await loadStock(match.symbol);
  } catch (err) {
    addLog(`ERROR: search failed — is the backend running?`);
  }
}

async function loadStock(ticker) {
  try {
    console.log("Calling loadChart with ticker:", ticker);
    loadChart(ticker);

    const [predictRes, infoRes, newsRes] = await Promise.all([
      fetch(`${API_BASE}/stock/${ticker}/predict`),
      fetch(`${API_BASE}/stock/${ticker}/info`),
      fetch(`${API_BASE}/stock/${ticker}/news`)
    ]);

    const predict = await predictRes.json();
    const info = await infoRes.json();
    const news = await newsRes.json();

    const diff = predict.next_day_prediction - predict.last_close;
    const trendClass = diff >= 0 ? "up" : "down";
    const trendSymbol = diff >= 0 ? "▲ UP" : "▼ DOWN";

    animateNumber(document.getElementById("statLast"), predict.last_close, "₹");
    animateNumber(document.getElementById("statPred"), predict.next_day_prediction, "₹");
    animateNumber(document.getElementById("statMae"), predict.mae, "₹");

    const trendEl = document.getElementById("statTrend");
    trendEl.textContent = trendSymbol;
    trendEl.className = `stat-value ${trendClass}`;

    const infoBody = document.getElementById("infoBody");
    if (info.error) {
      infoBody.innerHTML = `<div class="log-line muted">${info.error}</div>`;
    } else {
      infoBody.innerHTML = `
        <div class="info-row"><span class="label">Company</span><span>${info.name || "-"}</span></div>
        <div class="info-row"><span class="label">Sector</span><span>${info.sector || "-"}</span></div>
        <div class="info-row"><span class="label">Industry</span><span>${info.industry || "-"}</span></div>
        <div class="info-row"><span class="label">Market Cap</span><span>₹${formatLargeNumber(info.market_cap)}</span></div>
        <div class="info-row"><span class="label">P/E Ratio</span><span>${info.pe_ratio ? info.pe_ratio.toFixed(2) : "-"}</span></div>
        <div class="info-row"><span class="label">EPS</span><span>${info.eps ?? "-"}</span></div>
        <div class="info-row"><span class="label">52W High</span><span>₹${info["52_week_high"] ?? "-"}</span></div>
        <div class="info-row"><span class="label">52W Low</span><span>₹${info["52_week_low"] ?? "-"}</span></div>
        <div class="info-row"><span class="label">Dividend Yield</span><span>${info.dividend_yield ?? "-"}%</span></div>
      `;
    }

    const newsBody = document.getElementById("newsBody");
    if (news.length) {
      newsBody.innerHTML = news.map(item => `
        <a class="news-item" href="${item.link}" target="_blank">
          <div class="news-title">${item.title || "Untitled"}</div>
          <div class="news-meta">${item.publisher || "Unknown source"}</div>
        </a>
      `).join("");
    } else {
      newsBody.innerHTML = `<div class="log-line muted">No recent news found</div>`;
    }

    addLog(`Loaded ${ticker} — predicted ₹${predict.next_day_prediction.toFixed(2)} (MAE ₹${predict.mae.toFixed(2)})`);
  } catch (err) {
    addLog(`ERROR loading ${ticker} data`);
  }
}

function formatLargeNumber(num) {
  if (!num) return "-";
  if (num >= 1e12) return (num / 1e12).toFixed(2) + "T";
  if (num >= 1e9) return (num / 1e9).toFixed(2) + "B";
  if (num >= 1e7) return (num / 1e7).toFixed(2) + "Cr";
  if (num >= 1e5) return (num / 1e5).toFixed(2) + "L";
  return num.toString();
}

let chart = null;
let candleSeries = null;

async function loadChart(ticker) {
  try {
    const res = await fetch(`${API_BASE}/stock/${ticker}/chart`);
    const data = await res.json();

    if (!data.length) {
      addLog(`No chart data available for ${ticker}`);
      return;
    }

    const container = document.getElementById("tvChartContainer");
    container.innerHTML = "";

    chart = LightweightCharts.createChart(container, {
      width: container.clientWidth,
      height: 350,
      layout: { background: { color: "#0a0a0a" }, textColor: "#a3a3a3" },
      grid: { vertLines: { color: "#1a1a1a" }, horzLines: { color: "#1a1a1a" } },
      timeScale: { borderColor: "#262626" },
      rightPriceScale: { borderColor: "#262626" },
    });

    candleSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    candleSeries.setData(data);
    chart.timeScale().fitContent();
  } catch (err) {
    addLog(`ERROR loading chart for ${ticker}`);
  }
}