const API_BASE = '/api/v1';

export async function runSimulation(params) {
  const response = await fetch(`${API_BASE}/simulation/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`仿真请求失败: ${response.status}`);
  }

  return await response.json();
}

export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/simulation/health`);
    return response.ok;
  } catch {
    return false;
  }
}
