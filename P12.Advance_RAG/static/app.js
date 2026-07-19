function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function setStageState(stageKey, state) {
  const el = document.querySelector(`.stage-item[data-stage="${stageKey}"]`);
  if (!el) return;
  el.classList.remove('active', 'done');
  if (state) el.classList.add(state);
}
