export async function generateTestPlan(ticketId, settings) {
  const response = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticketId, ...settings })
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || 'Generation failed');
  return data;
}

export async function loadConfig() {
  const response = await fetch('/api/config');
  if (!response.ok) throw new Error('Could not load server config');
  return response.json();
}
