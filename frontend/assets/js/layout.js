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
            <span class="header-user-name" style="font-size: 13px; font-weight: 600;">${user.username || 'Profile'}</span>
          </a>
          <button onclick="logoutUser()" class="btn btn-ghost btn-sm btn-icon header-logout-btn" title="Sign Out" style="color: var(--text-muted); padding: 7px; border-radius: 50%;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        </div>
      `;
    } else {
      authContainer.innerHTML = `
        <a href="login.html" class="btn btn-ghost btn-sm">Sign In</a>
        <a href="register.html" class="btn btn-primary btn-sm hide-mobile-sm">Get Started</a>
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
    searchOverlay.style.cssText = "position:fixed;top:0;left:0;right:0;bottom:0;width:100%;height:100%;background:rgba(8,11,18,0.88);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);z-index:3000;display:none;align-items:flex-start;justify-content:center;padding-top:10vh;";
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

  // 6. Universal Mobile Sidebar Drawer (Ensures hamburger menu functions across all pages)
  (function initUniversalSidebar() {
    let sidebar = document.getElementById('sidebar');
    let sidebarOverlay = document.getElementById('sidebarOverlay');

    if (!sidebar) {
      sidebarOverlay = document.createElement('div');
      sidebarOverlay.id = 'sidebarOverlay';
      sidebarOverlay.className = 'sidebar-overlay';
      document.body.appendChild(sidebarOverlay);

      sidebar = document.createElement('aside');
      sidebar.id = 'sidebar';
      sidebar.className = 'sidebar';

      const rawPath = window.location.pathname.split('/').pop() || 'home.html';
      const curPage = (rawPath === '' || rawPath === 'index.html') ? 'home.html' : rawPath;
      const urlParams = new URLSearchParams(window.location.search);
      const curCat = urlParams.get('cat') || '';

      const userRaw = localStorage.getItem('samachar_user');
      let curUser = null;
      try { curUser = userRaw ? JSON.parse(userRaw) : null; } catch(_) {}

      sidebar.innerHTML = `
        <div class="flex items-center justify-between mb-4 pb-3" style="border-bottom: 1px solid var(--border);">
          <a href="home.html" class="logo" style="text-decoration:none;">
            <span>SAMACHAR</span><span class="logo-dot"></span>
          </a>
          <button id="closeSidebarBtn" class="btn btn-icon btn-ghost" style="padding:6px;border-radius:50%;" title="Close Menu">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M18 6 6 18M6 6l12 12"/></svg>
          </button>
        </div>

        ${curUser ? `
          <div class="card p-3 mb-4 flex items-center gap-3" style="background:var(--bg-surface-2);border-color:var(--border);">
            <div style="width:34px;height:34px;border-radius:50%;background:var(--accent);color:#08090C;font-size:14px;font-weight:800;display:flex;align-items:center;justify-content:center;box-shadow:0 0 10px var(--accent-glow);flex-shrink:0;">
              ${(curUser.full_name || curUser.username || 'U')[0].toUpperCase()}
            </div>
            <div style="flex:1;min-width:0;">
              <div style="font-size:13px;font-weight:700;color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${curUser.username || 'Reader'}</div>
              <a href="profile.html" style="font-size:11px;color:var(--accent);text-decoration:none;font-weight:600;">View Profile & Settings &rarr;</a>
            </div>
          </div>
        ` : `
          <div class="card p-3 mb-4" style="background:var(--bg-surface-2);border-color:var(--border);">
            <div style="font-size:12px;font-weight:700;color:var(--text-primary);margin-bottom:4px;">Truth-First Journalism</div>
            <p style="font-size:11px;color:var(--text-secondary);margin-bottom:8px;line-height:1.5;">Sign in to save bookmarks and unlock customized wire feeds.</p>
            <div class="flex items-center gap-2">
              <a href="login.html" class="btn btn-primary btn-sm" style="flex:1;text-align:center;justify-content:center;padding:5px 8px;font-size:12px;">Sign In</a>
              <a href="register.html" class="btn btn-secondary btn-sm" style="flex:1;text-align:center;justify-content:center;padding:5px 8px;font-size:12px;">Register</a>
            </div>
          </div>
        `}

        <div style="font-size:10px;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:var(--text-muted);margin-bottom:6px;padding:0 4px;">Main Feeds</div>
        <div class="flex flex-col gap-1 mb-4" id="sidebarLinks">
          <a href="home.html" class="sidebar-nav-item ${(curPage === 'home.html' && !curCat) ? 'active' : ''}">
            <span>🏠</span>
            <span>Top Stories</span>
          </a>
          <a href="latest.html" class="sidebar-nav-item ${(curPage === 'latest.html' && !curCat) ? 'active' : ''}">
            <span>⚡</span>
            <span>All News & Wire Feed</span>
          </a>
          <a href="factcheck.html" class="sidebar-nav-item ${curPage === 'factcheck.html' ? 'active' : ''}">
            <span>🛡️</span>
            <span>Fact Check Workbench</span>
          </a>
          <a href="trending.html" class="sidebar-nav-item ${curPage === 'trending.html' ? 'active' : ''}">
            <span>🔥</span>
            <span>Trending Wire Stories</span>
          </a>
          <a href="bookmarks.html" class="sidebar-nav-item ${curPage === 'bookmarks.html' ? 'active' : ''}">
            <span>📌</span>
            <span>Saved Bookmarks</span>
          </a>
        </div>

        <div style="font-size:10px;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:var(--text-muted);margin-bottom:6px;padding:0 4px;">News Desks & Channels</div>
        <div class="flex flex-col gap-1 mb-4">
          <a href="latest.html?cat=world" class="sidebar-nav-item ${curCat === 'world' ? 'active' : ''}">
            <span>🌍</span>
            <span>World Affairs</span>
          </a>
          <a href="latest.html?cat=technology" class="sidebar-nav-item ${curCat === 'technology' ? 'active' : ''}">
            <span>⚡</span>
            <span>Tech & AI</span>
          </a>
          <a href="latest.html?cat=india" class="sidebar-nav-item ${curCat === 'india' ? 'active' : ''}">
            <span>🇮🇳</span>
            <span>India & Regional</span>
          </a>
          <a href="latest.html?cat=business" class="sidebar-nav-item ${curCat === 'business' ? 'active' : ''}">
            <span>📈</span>
            <span>Markets & Economy</span>
          </a>
          <a href="latest.html?cat=science" class="sidebar-nav-item ${curCat === 'science' ? 'active' : ''}">
            <span>🔬</span>
            <span>Science & Space</span>
          </a>
          <a href="latest.html?cat=health" class="sidebar-nav-item ${curCat === 'health' ? 'active' : ''}">
            <span>🩺</span>
            <span>Health & Medicine</span>
          </a>
          <a href="latest.html?cat=sports" class="sidebar-nav-item ${curCat === 'sports' ? 'active' : ''}">
            <span>🏆</span>
            <span>Sports</span>
          </a>
          <a href="latest.html?cat=entertainment" class="sidebar-nav-item ${curCat === 'entertainment' ? 'active' : ''}">
            <span>🎬</span>
            <span>Entertainment</span>
          </a>
        </div>

        <div style="margin-top:auto;padding-top:16px;border-top:1px solid var(--border);">
          <div class="flex items-center justify-between text-xs text-secondary mb-3">
            <a href="about.html" class="hover-accent" style="color:var(--text-secondary);text-decoration:none;">About</a>
            <span>·</span>
            <a href="privacy.html" class="hover-accent" style="color:var(--text-secondary);text-decoration:none;">Privacy</a>
            <span>·</span>
            <a href="terms.html" class="hover-accent" style="color:var(--text-secondary);text-decoration:none;">Terms</a>
          </div>
          ${curUser ? `
            <button onclick="logoutUser()" class="btn btn-secondary btn-sm w-full" style="justify-content:center;gap:6px;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
              Sign Out
            </button>
          ` : ''}
        </div>
      `;
      document.body.appendChild(sidebar);
    }

    const openSidebar = (e) => {
      if (e) e.preventDefault();
      sidebar.classList.add('active');
      sidebarOverlay.classList.add('active');
      document.body.style.overflow = 'hidden';
    };

    const closeSidebar = () => {
      sidebar.classList.remove('active');
      sidebarOverlay.classList.remove('active');
      document.body.style.overflow = '';
    };

    document.querySelectorAll('#sidebarToggle').forEach(btn => {
      btn.addEventListener('click', openSidebar);
    });

    sidebarOverlay?.addEventListener('click', closeSidebar);
    document.getElementById('closeSidebarBtn')?.addEventListener('click', closeSidebar);
    sidebar.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', closeSidebar);
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && sidebar.classList.contains('active')) {
        closeSidebar();
      }
    });
  })();

  // 7. Universal Active Navigation & Category Highlight
  try {
    const rawPath = window.location.pathname.split('/').pop() || 'home.html';
    const activePage = (rawPath === '' || rawPath === 'index.html') ? 'home.html' : rawPath;
    document.querySelectorAll('.header nav a, .header-main nav a').forEach(link => {
      const href = link.getAttribute('href') || '';
      if (href === activePage) {
        link.classList.add('text-accent');
        link.classList.remove('text-secondary');
        link.style.color = 'var(--accent)';
      }
    });

    const urlParams = new URLSearchParams(window.location.search);
    const curCat = urlParams.get('cat') || '';
    document.querySelectorAll('#mainChannelBar .category-link').forEach(link => {
      const dataCat = link.getAttribute('data-cat');
      if (dataCat !== null) {
        if (dataCat === curCat) {
          link.classList.add('active');
        } else {
          link.classList.remove('active');
        }
      }
    });
  } catch (_) {}

  // 8. Mobile Header Search Trigger Injection
  const headerActions = document.querySelector('.header-main > .flex:last-child');
  if (headerActions && !document.getElementById('mobileSearchTrigger')) {
    const mobSearch = document.createElement('button');
    mobSearch.id = 'mobileSearchTrigger';
    mobSearch.className = 'btn btn-icon btn-ghost hide-desktop';
    mobSearch.setAttribute('aria-label', 'Search verified news');
    mobSearch.setAttribute('title', 'Search (⌘K)');
    mobSearch.style.cssText = 'padding: 8px; border-radius: 50%; color: var(--text-secondary);';
    mobSearch.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <path d="m21 21-4.35-4.35"/>
      </svg>
    `;
    mobSearch.addEventListener('click', openSearch);
    headerActions.insertBefore(mobSearch, headerActions.firstChild);
  }

  // 9. Mobile Bottom Tab Bar (Native Editorial Standard)
  (function injectMobileBottomNav() {
    const path = window.location.pathname;
    if (path.includes('login') || path.includes('register')) return;
    if (document.querySelector('.mobile-bottom-nav')) return;

    const rawPath = path.split('/').pop() || 'home.html';
    const activePage = (rawPath === '' || rawPath === 'index.html') ? 'home.html' : rawPath;

    const nav = document.createElement('nav');
    nav.className = 'mobile-bottom-nav';
    nav.setAttribute('aria-label', 'Mobile Navigation');
    nav.innerHTML = `
      <a href="home.html" class="mobile-nav-item ${activePage === 'home.html' ? 'active' : ''}">
        <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>
          <path d="M6 6h10M6 10h10M6 14h6"/>
        </svg>
        <span>Stories</span>
        <div class="nav-indicator"></div>
      </a>
      <a href="latest.html" class="mobile-nav-item ${(activePage === 'latest.html' || activePage === 'trending.html') ? 'active' : ''}">
        <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
        <span>Wire</span>
        <div class="nav-indicator"></div>
      </a>
      <a href="factcheck.html" class="mobile-nav-item ${activePage === 'factcheck.html' ? 'active' : ''}">
        <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="m9 12 2 2 4-4"/>
        </svg>
        <span>Truth</span>
        <div class="nav-indicator"></div>
      </a>
      <a href="bookmarks.html" class="mobile-nav-item ${activePage === 'bookmarks.html' ? 'active' : ''}">
        <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>
        </svg>
        <span>Saved</span>
        <div class="nav-indicator"></div>
      </a>
      <a href="profile.html" class="mobile-nav-item ${activePage === 'profile.html' ? 'active' : ''}">
        <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
        <span>Profile</span>
        <div class="nav-indicator"></div>
      </a>
    `;
    document.body.appendChild(nav);
  })();
});
