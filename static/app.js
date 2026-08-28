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
  if (window.lucide) window.lucide.createIcons();

  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  const toggle = document.getElementById('sidebar-toggle');
  const setSidebar = (open) => {
    if (!sidebar || !backdrop || !toggle) return;
    sidebar.classList.toggle('-translate-x-full', !open);
    backdrop.classList.toggle('hidden', !open);
    toggle.setAttribute('aria-expanded', String(open));
  };
  if (toggle) toggle.addEventListener('click', () => setSidebar(sidebar.classList.contains('-translate-x-full')));
  if (backdrop) backdrop.addEventListener('click', () => setSidebar(false));

  document.querySelectorAll('[data-dismiss]').forEach(btn => {
    btn.addEventListener('click', () => btn.closest('[data-alert]').remove());
  });
});
