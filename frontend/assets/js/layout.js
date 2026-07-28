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
function setThemeIcon(dark) {
  if (themeToggle) themeToggle.innerHTML = dark ? sunSVG : moonSVG;
}
function updateTime() {
  const el = document.getElementById('liveTime');
  if (el) el.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
}
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

const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
  const y = window.scrollY;
  header?.classList.toggle('header-scrolled', y > 50);
});

const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');

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
  if (e.key === 'Escape') {
    closeSidebar();
    searchOverlay?.classList.remove('open');
    document.querySelector('.map-inspector-drawer')?.classList.remove('open');
  }
  if (((e.metaKey || e.ctrlKey) && e.key === 'k') || (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA')) {
    e.preventDefault();
    searchOverlay?.classList.toggle('open');
    searchInput?.focus();
  }
});

function initMobileNav() {
  if (document.querySelector('.mobile-bottom-nav')) return;
  const nav = document.createElement('nav');
  nav.className = 'mobile-bottom-nav';
  const path = window.location.pathname;
  const isHome = path.endsWith('home.html') || path.endsWith('index.html') || path === '/';
  const isLatest = path.endsWith('latest.html');
  const isMap = path.endsWith('map.html');
  const isBm = path.endsWith('bookmarks.html');
  const isProf = path.endsWith('profile.html');

  nav.innerHTML = `
    <a href="home.html" class="mobile-nav-item ${isHome ? 'active' : ''}">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      <span>Home</span>
    </a>
    <a href="latest.html" class="mobile-nav-item ${isLatest ? 'active' : ''}">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9h2"/><path d="M10 6h6"/><path d="M10 10h6"/></svg>
      <span>Latest</span>
    </a>
    <a href="map.html" class="mobile-nav-item ${isMap ? 'active' : ''}">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
      <span>Map</span>
    </a>
    <a href="bookmarks.html" class="mobile-nav-item ${isBm ? 'active' : ''}">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>
      <span>Bookmarks</span>
    </a>
    <a href="profile.html" class="mobile-nav-item ${isProf ? 'active' : ''}">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
      <span>Profile</span>
    </a>
  `;
  document.body.appendChild(nav);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMobileNav);
} else {
  initMobileNav();
}

// Theme toggle — persists to localStorage, icon sync on load
const savedTheme = localStorage.getItem('samachar_theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);
let isDark = savedTheme === 'dark';

const sunSVG = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
const moonSVG = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

const themeToggle = document.getElementById('themeToggle');

setThemeIcon(isDark);

themeToggle?.addEventListener('click', () => {
  isDark = !isDark;
  const theme = isDark ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('samachar_theme', theme);
  setThemeIcon(isDark);
});

updateTime();
setInterval(updateTime, 1000);

window.openSidebar = openSidebar;
window.closeSidebar = closeSidebar;
window.showSkeleton = showSkeleton;
