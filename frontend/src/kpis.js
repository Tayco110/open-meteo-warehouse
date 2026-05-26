// Renderiza 4 KPI cards a partir do retorno de /api/stats.

export function renderKpis(container, stats, unit) {
  container.innerHTML = "";
  if (stats.length === 0) {
    container.innerHTML = '<p class="empty">Sem dados no período selecionado.</p>';
    return;
  }

  const minItem = stats.reduce((acc, s) => (s.min < acc.min ? s : acc));
  const maxItem = stats.reduce((acc, s) => (s.max > acc.max ? s : acc));
  const totalCount = stats.reduce((sum, s) => sum + s.count, 0);
  const weightedAvg =
    stats.reduce((sum, s) => sum + s.avg * s.count, 0) / totalCount;

  const cards = [
    { label: "Mínimo", value: fmt(minItem.min, unit), detail: minItem.city },
    { label: "Máximo", value: fmt(maxItem.max, unit), detail: maxItem.city },
    { label: "Média",  value: fmt(weightedAvg, unit), detail: `${stats.length} cidade(s)` },
    {
      label: "Medições",
      value: totalCount.toLocaleString("pt-BR"),
      detail: "registros no fato",
    },
  ];

  for (const card of cards) {
    const el = document.createElement("div");
    el.className = "kpi";
    el.innerHTML = `
      <span class="kpi-label">${card.label}</span>
      <span class="kpi-value">${card.value}</span>
      <span class="kpi-detail">${card.detail}</span>
    `;
    container.appendChild(el);
  }
}

function fmt(value, unit) {
  return `${value.toFixed(2)} ${unit}`.trim();
}
