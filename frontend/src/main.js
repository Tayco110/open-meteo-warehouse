import { api } from "./api.js";
import {
  loadFilterOptions,
  readFilters,
  renderLocationCheckboxes,
  renderVariableOptions,
} from "./filters.js";
import { renderBarChart, renderLineChart } from "./charts.js";
import { renderKpis } from "./kpis.js";

const DEFAULT_CITIES = ["São Paulo", "New York", "Tokyo", "Reykjavik"];
const DEFAULT_VARIABLE = "temperature_2m_mean";
const DEFAULT_START = "2020-01-01";
const DEFAULT_END = "2024-12-31";

const state = { variables: [] };

async function init() {
  document.getElementById("start-date").value = DEFAULT_START;
  document.getElementById("end-date").value = DEFAULT_END;

  try {
    const { locations, variables } = await loadFilterOptions();
    state.variables = variables;

    renderLocationCheckboxes(
      locations,
      document.getElementById("locations-list"),
      DEFAULT_CITIES,
    );
    renderVariableOptions(
      variables,
      document.getElementById("variable-select"),
      DEFAULT_VARIABLE,
    );
  } catch (err) {
    showError(`Falha ao carregar filtros: ${err.message}`);
    return;
  }

  document.getElementById("apply-btn").addEventListener("click", loadAndRender);
  await loadAndRender();
}

async function loadAndRender() {
  const status = document.getElementById("chart-status");
  const button = document.getElementById("apply-btn");
  status.classList.remove("error");
  status.textContent = "Carregando...";
  button.disabled = true;

  try {
    const filters = readFilters();
    if (filters.locations.length === 0) {
      status.textContent = "Selecione ao menos uma cidade.";
      return;
    }

    const statsParams = {
      locations: filters.locations,
      variables: filters.variables,
      start_date: filters.start_date,
      end_date: filters.end_date,
    };
    const [weather, stats] = await Promise.all([
      api.getWeather(filters),
      api.getStats(statsParams),
    ]);

    const variable = state.variables.find((v) => v.code === filters.variables[0]);
    const unit = variable?.unit ?? "";
    const varName = variable?.name ?? filters.variables[0];

    document.getElementById("chart-title").textContent =
      `${varName} (${unit}): série temporal`;
    document.getElementById("comparison-title").textContent =
      `${varName} (${unit}): média por cidade`;

    renderKpis(document.getElementById("kpis-grid"), stats, unit);
    renderLineChart(document.getElementById("line-chart"), weather, unit);
    renderBarChart(document.getElementById("bar-chart"), stats, unit);

    const totalPoints = weather.series.reduce(
      (sum, s) => sum + s.data.length, 0,
    );
    status.textContent =
      `${weather.series.length} série(s), ${totalPoints} pontos`;
  } catch (err) {
    showError(`Erro: ${err.message}`);
  } finally {
    button.disabled = false;
  }
}

function showError(message) {
  const status = document.getElementById("chart-status");
  status.classList.add("error");
  status.textContent = message;
}

init();
