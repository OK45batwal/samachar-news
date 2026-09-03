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
    });
  }

  // 3. Header Authentication State
  const authContainer = document.getElementById('headerAuth');
  let user = null;
  try {
    if (typeof getUser === 'function') {
      user = getUser();
    } else {
      const raw = localStorage.getItem('samachar_user');
      user = raw ? JSON.parse(raw) : null;
    }
  } catch (_) {}

  if (authContainer) {
    if (user) {
      authContainer.innerHTML = `
        <div class="flex items-center gap-2">
          <a href="profile.html" class="btn btn-secondary btn-sm flex items-center gap-2" style="padding: 5px 12px; border-radius: var(--radius-full); transition: all 0.2s var(--ease-spring);" title="My Profile & Settings">
            <div style="width:22px;height:22px;border-radius:50%;background:var(--accent);color:#08090C;font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center;box-shadow:0 0 8px var(--accent-glow)">
              ${(user.full_name || user.username || 'U')[0].toUpperCase()}
            </div>
            <span style="font-size: 13px; font-weight: 600;">${user.username || 'Profile'}</span>
          </a>
          <button onclick="logoutUser()" class="btn btn-ghost btn-sm btn-icon" title="Sign Out" style="color: var(--text-muted); padding: 7px; border-radius: 50%;">
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

  // 0. Auto-Flush Stale Service Worker Cache & Browser CacheStorage
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(regs => {
      for (let reg of regs) reg.unregister();
    });
  }
  if ('caches' in window) {
    caches.keys().then(keys => keys.forEach(k => caches.delete(k)));
  }

  // 5. Universal Search Command Palette & Modal
  let searchOverlay = document.getElementById('searchOverlay');
  
  if (!searchOverlay && !window.location.pathname.includes('login') && !window.location.pathname.includes('register')) {
    searchOverlay = document.createElement('div');
    searchOverlay.id = 'searchOverlay';
    searchOverlay.className = 'search-overlay';
    searchOverlay.style.cssText = "position:fixed;top:0;left:0;right:0;bottom:0;width:100vw;height:100vh;background:rgba(8,11,18,0.85);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);z-index:99999;display:none;align-items:flex-start;justify-content:center;padding-top:10vh;";
    searchOverlay.innerHTML = `
      <div class="search-modal" style="width:100%;max-width:640px;background:#101625;border:1px solid #222D42;border-radius:16px;box-shadow:0 25px 60px rgba(0,0,0,0.9),0 0 0 1px rgba(0,245,155,0.3);overflow:hidden;margin:0 16px;display:flex;flex-direction:column;box-sizing:border-box;">
        
        <div style="padding:14px 18px;background:#161E30;border-bottom:1px solid #222D42;display:flex;align-items:center;gap:12px;width:100%;box-sizing:border-box;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00F59B" stroke-width="2.5" style="flex-shrink:0;"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input type="text" id="globalSearch" placeholder="Search verified news, claims, topics (Press Enter to view all)..." style="flex:1;min-width:0;width:auto;background:transparent;border:none!important;outline:none!important;box-shadow:none!important;font-size:15px;font-weight:500;color:#F8FAFC;padding:4px 0;margin:0;" autocomplete="off" />
          <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
            <kbd class="hide-mobile" style="font-family:monospace;font-size:10px;padding:3px 7px;background:#202B40;border:1px solid #2E3E5C;border-radius:5px;color:#94A3B8;">ESC</kbd>
            <button id="closeSearchModalBtn" type="button" style="background:transparent;border:none;color:#94A3B8;font-size:16px;cursor:pointer;padding:4px 8px;line-height:1;border-radius:4px;" title="Close">✕</button>
          </div>
        </div>
        
        <div id="globalSearchResults" style="display:none;max-height:360px;overflow-y:auto;border-top:1px solid #222D42;"></div>
        
        <div id="searchDefaultTrending" style="padding:18px 20px;">
          <div style="font-size:11px;font-weight:700;color:#94A3B8;letter-spacing:0.5px;text-transform:uppercase;margin-bottom:10px;">🔥 Popular Trending Topics:</div>
          <div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px;">
            <a href="latest.html?q=AI" class="search-tag-pill" style="display:inline-flex;align-items:center;padding:6px 12px;border-radius:8px;background:#1B2436;border:1px solid #2A3854;color:#00F59B;font-size:12px;font-weight:600;text-decoration:none;">#ArtificialIntelligence</a>
            <a href="latest.html?q=technology" class="search-tag-pill" style="display:inline-flex;align-items:center;padding:6px 12px;border-radius:8px;background:#1B2436;border:1px solid #2A3854;color:#00F59B;font-size:12px;font-weight:600;text-decoration:none;">#Technology</a>
            <a href="latest.html?q=business" class="search-tag-pill" style="display:inline-flex;align-items:center;padding:6px 12px;border-radius:8px;background:#1B2436;border:1px solid #2A3854;color:#00F59B;font-size:12px;font-weight:600;text-decoration:none;">#Business</a>
            <a href="latest.html?q=science" class="search-tag-pill" style="display:inline-flex;align-items:center;padding:6px 12px;border-radius:8px;background:#1B2436;border:1px solid #2A3854;color:#00F59B;font-size:12px;font-weight:600;text-decoration:none;">#Science</a>
            <a href="latest.html?q=india" class="search-tag-pill" style="display:inline-flex;align-items:center;padding:6px 12px;border-radius:8px;background:#1B2436;border:1px solid #2A3854;color:#00F59B;font-size:12px;font-weight:600;text-decoration:none;">#India</a>
          </div>
        </div>

        <div style="padding:10px 18px;background:#161E30;border-top:1px solid #222D42;display:flex;align-items:center;justify-content:space-between;font-size:11px;color:#94A3B8;">
          <div style="display:flex;align-items:center;gap:12px;">
            <span><kbd style="padding:2px 5px;background:#202B40;border:1px solid #2E3E5C;border-radius:4px;color:#F8FAFC;">↵</kbd> View All</span>
            <span><kbd style="padding:2px 5px;background:#202B40;border:1px solid #2E3E5C;border-radius:4px;color:#F8FAFC;">ESC</kbd> Close</span>
          </div>
          <span style="color:#00F59B;font-weight:600;">Samachar Spotlight 2.0</span>
        </div>

      </div>
    `;
    document.body.appendChild(searchOverlay);

    document.getElementById('closeSearchModalBtn')?.addEventListener('click', () => {
      closeSearch();
    });
  }

  // 5. Header Live Search Bar Controller
  const headerSearchInput = document.getElementById('headerSearchInput');
  const headerSearchDropdown = document.getElementById('headerSearchDropdown');
  const headerSearchClearBtn = document.getElementById('headerSearchClearBtn');

  if (headerSearchInput && headerSearchDropdown) {
    let headerDebounce = null;

    headerSearchInput.addEventListener('input', (e) => {
      const q = e.target.value.trim();
      clearTimeout(headerDebounce);
      if (headerSearchClearBtn) headerSearchClearBtn.style.display = q ? 'block' : 'none';

      if (!q) {
        headerSearchDropdown.style.display = 'none';
        headerSearchDropdown.innerHTML = '';
        return;
      }

      headerDebounce = setTimeout(async () => {
        headerSearchDropdown.style.display = 'block';
        headerSearchDropdown.innerHTML = '<div style="padding:14px;text-align:center;font-size:12px;color:var(--text-muted);">Searching verified wire network...</div>';

        try {
          const res = await getArticles({ q, limit: 5 });
          const items = res?.articles || [];

          if (!items.length) {
            headerSearchDropdown.innerHTML = `
              <div style="padding:16px;text-align:center;">
                <div style="font-size:12.5px;color:var(--text-muted);margin-bottom:6px;">No matching articles found for "${q}"</div>
                <a href="latest.html?q=${encodeURIComponent(q)}" style="font-size:11.5px;color:var(--accent);font-weight:700;text-decoration:none;">Search entire archive &rarr;</a>
              </div>
            `;
            return;
          }

          headerSearchDropdown.innerHTML = items.map(a => `
            <a href="article.html?id=${a.id}" class="search-dropdown-item">
              <div class="search-dropdown-thumb">
                <img src="${a.image_url || 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=100&q=80'}" alt="${sanitize(a.title)}" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=100&q=80'" />
              </div>
              <div class="search-dropdown-info">
                <div class="search-dropdown-title">${sanitize(a.title)}</div>
                <div class="search-dropdown-meta">
                  <span style="color:var(--accent);font-weight:700;">🟢 ${a.credibility_score || 95}% Verified</span>
                  <span>·</span>
                  <span>${sanitize(a.source?.name || a.source_name || 'Wire')}</span>
                </div>
              </div>
            </a>
          `).join('') + `
            <div class="search-dropdown-footer">
              <a href="latest.html?q=${encodeURIComponent(q)}">View all results for "${q}" &rarr;</a>
            </div>
          `;
        } catch (err) {
          headerSearchDropdown.innerHTML = '<div style="padding:12px;text-align:center;font-size:12px;color:var(--danger);">Error searching database.</div>';
        }
      }, 180);
    });

    headerSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = headerSearchInput.value.trim();
        if (q) {
          window.location.href = `latest.html?q=${encodeURIComponent(q)}`;
        }
      }
      if (e.key === 'Escape') {
        headerSearchDropdown.style.display = 'none';
      }
    });

    headerSearchClearBtn?.addEventListener('click', () => {
      headerSearchInput.value = '';
      headerSearchClearBtn.style.display = 'none';
      headerSearchDropdown.style.display = 'none';
      headerSearchDropdown.innerHTML = '';
      headerSearchInput.focus();
    });

    document.addEventListener('click', (e) => {
      if (!headerSearchInput.contains(e.target) && !headerSearchDropdown.contains(e.target)) {
        headerSearchDropdown.style.display = 'none';
      }
    });
  }

  const searchToggle = document.getElementById('searchToggle');
  const globalSearchInput = document.getElementById('globalSearch');
  const globalSearchResults = document.getElementById('globalSearchResults');
  const searchDefaultTrending = document.getElementById('searchDefaultTrending');

  function openSearch() {
    if (searchOverlay) {
      searchOverlay.style.display = 'flex';
      setTimeout(() => {
        globalSearchInput?.focus();
      }, 50);
    }
  }

  function closeSearch() {
    if (searchOverlay) {
      searchOverlay.style.display = 'none';
      if (globalSearchInput) globalSearchInput.value = '';
      if (globalSearchResults) {
        globalSearchResults.innerHTML = '';
        globalSearchResults.style.display = 'none';
      }
      if (searchDefaultTrending) searchDefaultTrending.style.display = 'block';
    }
  }

  searchToggle?.addEventListener('click', (e) => {
    e.preventDefault();
    if (headerSearchInput) {
      headerSearchInput.focus();
    } else {
      openSearch();
    }
  });

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      if (headerSearchInput) {
        headerSearchInput.focus();
        headerSearchInput.select();
      } else {
        openSearch();
      }
    }
    if (e.key === 'Escape' && searchOverlay && searchOverlay.style.display === 'flex') {
      closeSearch();
    }
  });

  searchOverlay?.addEventListener('click', (e) => {
    if (e.target === searchOverlay) {
      closeSearch();
    }
  });

  // Global search typing listener
  let searchTimeout = null;
  if (globalSearchInput) {
    globalSearchInput.addEventListener('input', (e) => {
      const query = e.target.value.trim().toLowerCase();
      clearTimeout(searchTimeout);

      if (!query) {
        if (globalSearchResults) {
          globalSearchResults.innerHTML = '';
          globalSearchResults.style.display = 'none';
        }
        if (searchDefaultTrending) searchDefaultTrending.style.display = 'block';
        return;
      }

      if (searchDefaultTrending) searchDefaultTrending.style.display = 'none';

      searchTimeout = setTimeout(async () => {
        if (globalSearchResults) {
          globalSearchResults.style.display = 'block';
          globalSearchResults.innerHTML = '<div style="padding:16px;text-align:center;color:#94A3B8;font-size:13px;">Searching verified database...</div>';

          try {
            let res = null;
            if (typeof getArticles === 'function') {
              res = await getArticles({ q: query, limit: 5 });
            }
            const articles = res?.articles || [];

            if (articles.length === 0) {
              globalSearchResults.innerHTML = `
                <div style="padding:24px 16px;text-align:center;">
                  <div style="font-size:13px;color:#94A3B8;margin-bottom:8px;">No matching verified articles found for "${query}"</div>
                  <a href="latest.html?q=${encodeURIComponent(query)}" style="font-size:12px;color:#00F59B;font-weight:600;text-decoration:none;">Search entire archive &rarr;</a>
                </div>
              `;
              return;
            }

            globalSearchResults.innerHTML = articles.map(art => `
              <a href="article.html?id=${art.id}" style="display:flex;align-items:flex-start;gap:12px;padding:12px 16px;border-bottom:1px solid #1E293B;text-decoration:none;transition:background 0.15s;" onmouseover="this.style.background='#1A2438'" onmouseout="this.style.background='transparent'">
                <div style="width:40px;height:40px;border-radius:6px;background:#243046;overflow:hidden;flex-shrink:0;">
                  <img src="${art.image_url || 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=120&q=80'}" style="width:100%;height:100%;object-fit:cover;" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=120&q=80'" />
                </div>
                <div style="flex:1;min-width:0;">
                  <div style="font-size:13px;font-weight:600;color:#F8FAFC;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${art.title}</div>
                  <div style="font-size:11px;color:#94A3B8;display:flex;align-items:center;gap:8px;">
                    <span style="color:#00F59B;font-weight:600;">🟢 ${art.credibility_score || 95}% Verified</span>
                    <span>·</span>
                    <span>${art.source_name || art.source?.name || 'Wire'}</span>
                  </div>
                </div>
              </a>
            `).join('') + `
              <div style="padding:10px 16px;background:#131B2C;text-align:center;">
                <a href="latest.html?q=${encodeURIComponent(query)}" style="font-size:12px;color:#00F59B;font-weight:600;text-decoration:none;">View all results for "${query}" &rarr;</a>
              </div>
            `;
          } catch (err) {
            globalSearchResults.innerHTML = '<div style="padding:16px;text-align:center;color:#EF4444;font-size:12px;">Error retrieving results.</div>';
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
