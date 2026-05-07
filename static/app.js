// Confirmação de exclusão
function confirmDelete(msg) {
  return confirm(msg || 'Tem certeza que deseja excluir?');
}

// Toggle tema claro/escuro
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.classList.toggle('dark');
  // Persiste via POST silencioso
  fetch('/profile/theme', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'theme=' + (isDark ? 'dark' : 'light'),
  }).catch(() => {});
}

// Fecha alertas ao clicar
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-dismiss]').forEach(btn => {
    btn.addEventListener('click', () => btn.closest('[data-alert]').remove());
  });
});
