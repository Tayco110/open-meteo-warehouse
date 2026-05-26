import { api } from "./api.js";

const CATEGORY_LABELS = {
  temperature: "Temperatura",
  precipitation: "Precipitação",
  wind: "Vento",
  radiation: "Radiação",
};

export async function loadFilterOptions() {
  const [locations, variables] = await Promise.all([
    api.getLocations(),
    api.getVariables(),
  ]);
  return { locations, variables };
}

export function renderLocationCheckboxes(locations, container, defaults) {
  const defaultSet = new Set(defaults);
  container.innerHTML = "";
  for (const loc of locations) {
    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = loc.city;
    checkbox.checked = defaultSet.has(loc.city);
    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(`${loc.city}, ${loc.country}`));
    container.appendChild(label);
  }
}

export function renderVariableOptions(variables, select, defaultCode) {
  select.innerHTML = "";
  const byCategory = new Map();
  for (const v of variables) {
    if (!byCategory.has(v.category)) byCategory.set(v.category, []);
    byCategory.get(v.category).push(v);
  }
  for (const [category, items] of byCategory) {
    const group = document.createElement("optgroup");
    group.label = CATEGORY_LABELS[category] ?? category;
    for (const v of items) {
      const option = document.createElement("option");
      option.value = v.code;
      option.textContent = `${v.name} (${v.unit})`;
      option.selected = v.code === defaultCode;
      group.appendChild(option);
    }
    select.appendChild(group);
  }
}

export function readFilters() {
  const cities = Array.from(
    document.querySelectorAll("#locations-list input:checked"),
  ).map((cb) => cb.value);

  return {
    locations: cities,
    variables: [document.getElementById("variable-select").value],
    start_date: document.getElementById("start-date").value,
    end_date: document.getElementById("end-date").value,
    aggregation: document.getElementById("aggregation").value,
  };
}
