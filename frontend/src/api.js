export const API_BASE = "http://localhost:8000/api";

async function getJson(path, params = {}) {
  const url = new URL(API_BASE + path);
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      value.forEach((v) => url.searchParams.append(key, v));
    } else {
      url.searchParams.set(key, value);
    }
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API ${response.status} em ${path}`);
  }
  return response.json();
}

export const api = {
  getLocations: () => getJson("/locations"),
  getVariables: () => getJson("/variables"),
  getWeather: (params) => getJson("/weather", params),
  getStats: (params) => getJson("/stats", params),
};
