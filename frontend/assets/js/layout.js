// Samachar Layout Controller: Header Auth, Theme switcher, Mobile Bottom Nav, Search Modal

(function() {
  const saved = localStorage.getItem('samachar_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

document.addEventListener('DOMContentLoaded', () => {
  // 1. Live Date display
  const dateEl = document.getElementById('currentDateDisplay');
  if (dateEl) {
    const options = { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' };
    dateEl.textContent = new Date().toLocaleDateString('en-US', options);
  }

  // 2. Theme Switcher
  const themeToggleBtn = document.getElementById('themeToggle');
  const updateThemeIcon = (theme) => {
    if (!themeToggleBtn) return;
    if (theme === 'dark') {
      themeToggleBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="5"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
      `;
      themeToggleBtn.setAttribute('title', 'Switch to Editorial Light');
    } else {
      themeToggleBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      `;
      themeToggleBtn.setAttribute('title', 'Switch to Obsidian Dark');
    }
  };

  const initialTheme = document.documentElement.getAttribute('data-theme') || 'dark';
  updateThemeIcon(initialTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('samachar_theme', next);
      updateThemeIcon(next);
      if (typeof showToast === 'function') {
        showToast(`Switched to ${next === 'dark' ? 'Obsidian Dark' : 'Editorial Light'}`, 'info');
      }
    });
  }

  // 3. Header Authentication State
  const authContainer = document.getElementById('headerAuth');
  const user = getUser();

  if (authContainer) {
    if (user) {
      authContainer.innerHTML = `
        <div class="flex items-center gap-2">
          <a href="bookmarks.html" class="btn btn-ghost btn-sm" title="Saved Bookmarks">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>
            <span class="hide-mobile">Saved</span>
          </a>
          <a href="profile.html" class="btn btn-secondary btn-sm flex items-center gap-2">
            <div style="width:20px;height:20px;border-radius:50%;background:var(--accent);color:#08090C;font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center">
              ${(user.full_name || user.username || 'U')[0].toUpperCase()}
            </div>
            <span class="hide-mobile">${user.username}</span>
          </a>
          <button onclick="logoutUser()" class="btn btn-ghost btn-sm" title="Sign Out">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        </div>
      `;
    } else {
      authContainer.innerHTML = `
        <a href="login.html" class="btn btn-ghost btn-sm">Sign In</a>
        <a href="register.html" class="btn btn-primary btn-sm">Get Started</a>
      `;
    }
  }

  // 4. Clean Header Auth Initialization Complete

  // 5. Universal Search Command Palette & Modal
  let searchOverlay = document.getElementById('searchOverlay');
  
  if (!searchOverlay && !window.location.pathname.includes('login') && !window.location.pathname.includes('register')) {
    searchOverlay = document.createElement('div');
    searchOverlay.id = 'searchOverlay';
    searchOverlay.className = 'search-overlay';
    searchOverlay.innerHTML = `
      <div class="search-modal">
        <div class="search-input-header">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="color:var(--accent);flex-shrink:0;"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input type="text" id="globalSearch" class="search-input-field" placeholder="Search verified news, claims, topics (Press Enter to view all)..." autocomplete="off" />
          <div class="flex items-center gap-2 flex-shrink-0">
            <kbd class="hide-mobile" style="font-family:var(--font-mono);font-size:10px;padding:3px 8px;background:var(--bg-surface-2);border:1px solid var(--border);border-radius:6px;color:var(--text-muted)">ESC</kbd>
            <button id="closeSearchModalBtn" type="button" class="btn btn-ghost btn-sm" style="padding:4px 8px;color:var(--text-secondary);font-size:14px;line-height:1;" title="Close search (ESC)">✕</button>
          </div>
        </div>
        <div id="globalSearchResults" class="search-results-list" style="display:none"></div>
        <div class="p-5 text-xs text-muted" id="searchDefaultTrending">
          <div class="font-bold mb-3" style="color:var(--text-primary);letter-spacing:0.5px;text-transform:uppercase;font-size:11px;">🔥 Popular Trending Topics:</div>
          <div class="flex items-center" style="flex-wrap:wrap;gap:8px;">
            <a href="latest.html?q=semiconductor" class="search-tag-pill">#Semiconductors</a>
            <a href="latest.html?q=hydrogen" class="search-tag-pill">#GreenHydrogen</a>
            <a href="latest.html?q=malaria" class="search-tag-pill">#MalariaVaccine</a>
            <a href="latest.html?q=settlement" class="search-tag-pill">#ProjectNexus</a>
          </div>
        <div class="search-modal-footer">
          <div class="flex items-center gap-3">
            <span><kbd style="padding:2px 5px;background:var(--bg-surface-2);border-radius:4px;border:1px solid var(--border)">↵</kbd> View All</span>
            <span><kbd style="padding:2px 5px;background:var(--bg-surface-2);border-radius:4px;border:1px solid var(--border)">ESC</kbd> Close</span>
          </div>
          <span class="text-accent font-semibold">Samachar Spotlight 2.0</span>
        </div>
      </div>
    `;
    document.body.appendChild(searchOverlay);

    document.getElementById('closeSearchModalBtn')?.addEventListener('click', () => {
      closeSearch();
    });
  }

  const globalSearchInput = document.getElementById('globalSearch');
  const resultsContainer = document.getElementById('globalSearchResults');
  const trendingContainer = document.getElementById('searchDefaultTrending');
  let debounceTimeout = null;

  function openSearch() {
    if (!searchOverlay) return;
    searchOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    globalSearchInput?.focus();
  }

  function closeSearch() {
    if (!searchOverlay) return;
    searchOverlay.classList.remove('active');
    document.body.style.overflow = '';
    if (globalSearchInput) globalSearchInput.value = '';
    if (resultsContainer) {
      resultsContainer.style.display = 'none';
      resultsContainer.innerHTML = '';
    }
    if (trendingContainer) trendingContainer.style.display = 'block';
  }

  document.querySelectorAll('#searchToggle, [data-action="search"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openSearch();
    });
  });

  if (searchOverlay) {
    searchOverlay.addEventListener('click', (e) => {
      if (e.target === searchOverlay) closeSearch();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && searchOverlay?.classList.contains('active')) {
      closeSearch();
    }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (searchOverlay?.classList.contains('active')) {
        closeSearch();
      } else {
        openSearch();
      }
    }
  });

  if (globalSearchInput) {
    globalSearchInput.addEventListener('input', () => {
      const query = globalSearchInput.value.trim();
      clearTimeout(debounceTimeout);

      if (!query || query.length < 2) {
        if (resultsContainer) {
          resultsContainer.style.display = 'none';
          resultsContainer.innerHTML = '';
        }
        if (trendingContainer) trendingContainer.style.display = 'block';
        return;
      }

      debounceTimeout = setTimeout(async () => {
        try {
          const res = await getArticles({ q: query, limit: 5 });
          if (trendingContainer) trendingContainer.style.display = 'none';
          if (resultsContainer) {
            resultsContainer.style.display = 'block';
            if (res.articles && res.articles.length) {
              resultsContainer.innerHTML = res.articles.map(a => `
                <a href="article.html?id=${a.id}" class="search-result-item">
                  <div style="flex:1;min-width:0;">
                    <div class="title line-clamp-1">${sanitize(a.title)}</div>
                    <div class="meta">${sanitize(a.category?.name || 'Top News')} · ${sanitize(a.source?.name || 'Wire')} · ${timeAgo(a.published_at)}</div>
                  </div>
                  <span class="badge badge-verified" style="font-size:10px;padding:3px 7px;flex-shrink:0;">🟢 ${a.credibility_score || 95}%</span>
                </a>
              `).join('') + `
                <a href="latest.html?q=${encodeURIComponent(query)}" class="search-result-item" style="background:var(--bg-surface-2);justify-content:center;color:var(--accent);font-weight:600;font-size:12px;">
                  View All Matching Stories for "${sanitize(query)}" &rarr;
                </a>
              `;
            } else {
              resultsContainer.innerHTML = `<div class="p-4 text-center text-xs text-muted">No verified stories found for "${sanitize(query)}". Press Enter to browse.</div>`;
            }
          }
        } catch (err) {
          if (resultsContainer) {
            resultsContainer.innerHTML = `<div class="p-3 text-center text-xs text-muted">Press Enter to search for "${sanitize(query)}"</div>`;
          }
        }
      }, 250);
    });

    globalSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const query = globalSearchInput.value.trim();
        if (query) {
          window.location.href = `latest.html?q=${encodeURIComponent(query)}`;
        }
      }
    });
  }

  // 6. Sidebar Drawer (Mobile)
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  if (sidebarToggle && sidebar && sidebarOverlay) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.add('active');
      sidebarOverlay.classList.add('active');
    });

    sidebarOverlay.addEventListener('click', () => {
      sidebar.classList.remove('active');
      sidebarOverlay.classList.remove('active');
    });
  }
});
