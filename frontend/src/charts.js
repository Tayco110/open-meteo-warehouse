// Paleta categórica usada nas séries do gráfico de linhas.
const COLORS = [
  "#0ea5e9", "#f97316", "#10b981", "#a855f7",
  "#ef4444", "#eab308", "#3b82f6", "#ec4899",
  "#14b8a6", "#6366f1",
];

let lineChart = null;
let barChart = null;

export function renderLineChart(canvas, weatherResponse, unit) {
  const datasets = weatherResponse.series.map((s, i) => ({
    label: s.city,
    data: s.data.map((p) => ({ x: p.date, y: p.value })),
    borderColor: COLORS[i % COLORS.length],
    backgroundColor: COLORS[i % COLORS.length],
    borderWidth: 2,
    pointRadius: 1.5,
    pointHoverRadius: 5,
    tension: 0.15,
  }));

  const config = {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "top", labels: { boxWidth: 12, padding: 12 } },
        tooltip: {
          callbacks: {
            label: (ctx) =>
              `${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(2)} ${unit}`,
          },
        },
      },
      scales: {
        x: {
          type: "time",
          time: { unit: "month", displayFormats: { month: "MMM/yy" } },
          title: { display: false },
        },
        y: {
          title: { display: true, text: unit },
        },
      },
    },
  };

  if (lineChart) lineChart.destroy();
  lineChart = new Chart(canvas, config);
}

export function renderBarChart(canvas, stats, unit) {
  // Mantém a mesma cor por cidade que o line chart (ordem alfabética vinda do backend).
  const colorByCity = {};
  stats.forEach((s, i) => {
    colorByCity[s.city] = COLORS[i % COLORS.length];
  });

  const sorted = [...stats].sort((a, b) => b.avg - a.avg);

  const config = {
    type: "bar",
    data: {
      labels: sorted.map((s) => s.city),
      datasets: [
        {
          label: "Média",
          data: sorted.map((s) => s.avg),
          backgroundColor: sorted.map((s) => colorByCity[s.city]),
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: "x",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y?.toFixed(2)} ${unit}`,
          },
        },
      },
      scales: {
        y: { title: { display: true, text: unit } },
      },
    },
  };

  if (barChart) barChart.destroy();
  barChart = new Chart(canvas, config);
}
