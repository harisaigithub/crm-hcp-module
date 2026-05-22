const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json();
}

export const api = {
  listHcps: () => request("/hcps"),
  createHcp: (payload) =>
    request("/hcps", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listInteractions: (hcpId) => request(`/interactions${hcpId ? `?hcp_id=${hcpId}` : ""}`),
  createInteraction: (payload) =>
    request("/interactions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateInteraction: (id, payload) =>
    request(`/interactions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  chat: ({
    message,
    session_id,
    selected_hcp_id
  }) =>
    request("/agent/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        session_id,
        selected_hcp_id,
      }),
    }),
};
