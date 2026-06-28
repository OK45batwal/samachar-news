const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
  const y = window.scrollY;
  header?.classList.toggle('header-scrolled', y > 50);
});

const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');

function openSidebar() {
  sidebar?.classList.add('open');
  sidebarOverlay?.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeSidebar() {
  sidebar?.classList.remove('open');
  sidebarOverlay?.classList.remove('open');
  document.body.style.overflow = '';
}
sidebarToggle?.addEventListener('click', openSidebar);
sidebarOverlay?.addEventListener('click', closeSidebar);

const searchToggle = document.getElementById('searchToggle');
const searchOverlay = document.getElementById('searchOverlay');
const searchInput = document.getElementById('globalSearch');

searchToggle?.addEventListener('click', () => {
  searchOverlay?.classList.toggle('open');
  searchInput?.focus();
});
searchOverlay?.addEventListener('click', (e) => {
  if (e.target === searchOverlay) searchOverlay.classList.remove('open');
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') { closeSidebar(); searchOverlay?.classList.remove('open'); }
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    searchOverlay?.classList.toggle('open');
    searchInput?.focus();
  }
});

// Theme toggle — persists to localStorage, icon sync on load
const savedTheme = localStorage.getItem('samachar_theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);
let isDark = savedTheme === 'dark';

const sunSVG = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
const moonSVG = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

const themeToggle = document.getElementById('themeToggle');
function setThemeIcon(dark) {
  if (themeToggle) themeToggle.innerHTML = dark ? sunSVG : moonSVG;
}
setThemeIcon(isDark);

themeToggle?.addEventListener('click', () => {
  isDark = !isDark;
  const theme = isDark ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('samachar_theme', theme);
  setThemeIcon(isDark);
});

function updateTime() {
  const el = document.getElementById('liveTime');
  if (el) el.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
}
updateTime();
setInterval(updateTime, 1000);

function showSkeleton(container, count = 6) {
  const html = Array.from({ length: count }, () =>
    `<div class="skeleton-card">
      <div class="skeleton" style="aspect-ratio:16/9;margin-bottom:12px"></div>
      <div class="skeleton" style="height:14px;width:60%;margin-bottom:8px"></div>
      <div class="skeleton" style="height:12px;width:40%"></div>
    </div>`
  ).join('');
  if (container) container.innerHTML = html;
}
