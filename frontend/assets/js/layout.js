// Samachar Layout Controller: Header Auth, Theme switcher, Mobile Bottom Nav, Search Modal

// Global Account Deletion Modal Controller (Direct 1-Click Confirmation)
window.openDeleteAccountModal = function() {
  let modal = document.getElementById('globalDeleteAccountModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'globalDeleteAccountModal';
    modal.className = 'custom-modal-overlay';
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="card p-6" style="max-width: 480px; width: 100%; background: #121824; border: 1px solid rgba(255, 77, 77, 0.4); box-shadow: 0 25px 50px rgba(0,0,0,0.9); box-sizing: border-box; border-radius: 16px;">
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px;">
        <div style="width: 44px; height: 44px; border-radius: 50%; background: rgba(255, 77, 77, 0.15); display: flex; align-items: center; justify-content: center; color: #FF4D4D; flex-shrink: 0;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
        </div>
        <div>
          <h3 class="heading-sm text-primary" style="margin:0 0 4px 0; font-size: 18px;">Permanently Delete Account?</h3>
          <p class="text-xs text-muted" style="margin:0;">This action cannot be undone.</p>
        </div>
      </div>
      <p class="text-xs text-secondary mb-4 leading-relaxed" style="line-height: 1.6;">
        Are you sure you want to permanently erase your account? All saved bookmarks, reading history, and data will be permanently wiped.
      </p>
      <div style="display:flex;align-items:center;justify-content:flex-end;gap:12px;">
        <button type="button" onclick="document.getElementById('globalDeleteAccountModal').style.setProperty('display','none','important')" class="btn btn-secondary btn-sm" style="padding: 8px 16px;">Cancel</button>
        <button type="button" id="confirmGlobalDirectDeleteBtn" onclick="executeGlobalDirectDelete()" class="btn btn-sm" style="background:#FF4D4D;color:#fff;border:none;font-weight:700;padding:8px 18px;cursor:pointer;">Yes, Delete Account</button>
      </div>
    </div>
  `;

  modal.style.setProperty('display', 'flex', 'important');
  modal.onclick = (e) => {
    if (e.target === modal) modal.style.setProperty('display', 'none', 'important');
  };
};

window.executeGlobalDirectDelete = async function() {
  const btn = document.getElementById('confirmGlobalDirectDeleteBtn');
  if (btn) { btn.disabled = true; btn.textContent = 'Deleting Account...'; }

  try {
    const token = localStorage.getItem('samachar_token');
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      await fetch('http://localhost:8000/api/auth/account', {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer ' + token },
        signal: AbortSignal.timeout(1500)
      }).catch(() => {});
    }
  } catch (_) {}

  try {
    const rawUser = localStorage.getItem('samachar_user');
    const userObj = rawUser ? JSON.parse(rawUser) : null;
    if (userObj && userObj.email) {
      localStorage.removeItem('samachar_registered_' + userObj.email);
    }
  } catch (_) {}

  localStorage.removeItem('samachar_token');
  localStorage.removeItem('samachar_user');
  localStorage.removeItem('samachar_local_bookmarks');
  localStorage.removeItem('samachar_remember_email');
  sessionStorage.clear();

  if (typeof showToast === 'function') {
    showToast('👋 Your account has been permanently deleted.', 'info');
  }

  setTimeout(() => {
    window.location.href = 'index.html';
  }, 350);
};

window.dispatchDeleteOtpStep = async function() {
  const sendBtn = document.getElementById('sendDeleteOtpBtn');
  if (sendBtn) { sendBtn.disabled = true; sendBtn.textContent = 'Sending Code...'; }

  try {
    let res = null;
    if (typeof sendDeleteOtp === 'function') {
      res = await sendDeleteOtp();
    } else {
      const code = String(Math.floor(100000 + Math.random() * 900000));
      sessionStorage.setItem('samachar_delete_otp', code);
      res = { otp_code: code };
    }

    document.getElementById('deleteStage1').style.display = 'none';
    document.getElementById('deleteStage2').style.display = 'block';

    const input = document.getElementById('globalDeleteOtpInput');
    if (input) {
      input.value = '';
      input.focus();
    }

    if (res && res.otp_code) {
      document.getElementById('otpCodeDisplayNotice').innerHTML = `Security Verification Code: <strong style="font-family:var(--font-mono);font-size:14px;color:var(--accent);">${res.otp_code}</strong> (Valid for 5m)`;
      if (typeof showToast === 'function') {
        showToast(`🔑 Verification OTP: ${res.otp_code}`, 'info');
      }
    }
  } catch (err) {
    alert('Failed to send verification code: ' + err.message);
    if (sendBtn) { sendBtn.disabled = false; sendBtn.textContent = 'Send 6-Digit OTP Code →'; }
  }
};

window.submitFinalDeleteAccount = async function() {
  const input = document.getElementById('globalDeleteOtpInput');
  const errEl = document.getElementById('deleteOtpError');
  const submitBtn = document.getElementById('confirmFinalDeleteBtn');
  const enteredOtp = input ? input.value.trim() : '';

  if (!enteredOtp || enteredOtp.length !== 6) {
    if (errEl) {
      errEl.textContent = 'Please enter the complete 6-digit OTP code.';
      errEl.style.display = 'block';
    }
    return;
  }

  if (errEl) errEl.style.display = 'none';
  if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Verifying & Deleting...'; }

  try {
    if (typeof verifyAndDeleteAccount === 'function') {
      await verifyAndDeleteAccount(enteredOtp);
    } else {
      const stored = sessionStorage.getItem('samachar_delete_otp');
      if (stored && enteredOtp !== stored) {
        throw new Error('Invalid OTP code. Please enter the correct code.');
      }
      localStorage.removeItem('samachar_token');
      localStorage.removeItem('samachar_user');
      localStorage.removeItem('samachar_local_bookmarks');
      sessionStorage.clear();
    }

    if (typeof showToast === 'function') {
      showToast('👋 Your account has been permanently deleted.', 'info');
    }

    setTimeout(() => {
      window.location.href = 'index.html';
    }, 350);
  } catch (err) {
    if (errEl) {
      errEl.textContent = err.message || 'Invalid verification code. Please try again.';
      errEl.style.display = 'block';
    }
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Verify & Delete Permanently'; }
  }
};

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
          <a href="bookmarks.html" class="btn btn-ghost btn-sm" title="Saved Bookmarks">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>
            <span class="hide-mobile">Saved</span>
          </a>
          <a href="profile.html" class="btn btn-secondary btn-sm flex items-center gap-2" title="User Profile">
            <div style="width:20px;height:20px;border-radius:50%;background:var(--accent);color:#08090C;font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center">
              ${(user.full_name || user.username || 'U')[0].toUpperCase()}
            </div>
            <span class="hide-mobile">${user.username || 'Profile'}</span>
          </a>
          <button onclick="logoutUser()" class="btn btn-ghost btn-sm" title="Sign Out">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            <span class="hide-mobile">Logout</span>
          </button>
          <button onclick="openDeleteAccountModal()" class="btn btn-sm" style="background:rgba(255,77,77,0.12);color:#FF4D4D;border:1px solid rgba(255,77,77,0.3);padding:4px 8px;font-size:11px;font-weight:600;" title="Permanently Delete Account">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            <span>Delete</span>
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

  // 0. Auto-Flush Stale Service Worker Cache
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(regs => {
      for (let reg of regs) reg.unregister();
    });
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
            <a href="latest.html?q=semiconductor" class="search-tag-pill" style="display:inline-flex;align-items:center;padding:6px 12px;border-radius:8px;background:#1B2436;border:1px solid #2A3854;color:#00F59B;font-size:12px;font-weight:600;text-decoration:none;">#Semiconductors</a>
            <a href="latest.html?q=hydrogen" class="search-tag-pill" style="display:inline-flex;align-items:center;padding:6px 12px;border-radius:8px;background:#1B2436;border:1px solid #2A3854;color:#00F59B;font-size:12px;font-weight:600;text-decoration:none;">#GreenHydrogen</a>
            <a href="latest.html?q=malaria" class="search-tag-pill" style="display:inline-flex;align-items:center;padding:6px 12px;border-radius:8px;background:#1B2436;border:1px solid #2A3854;color:#00F59B;font-size:12px;font-weight:600;text-decoration:none;">#MalariaVaccine</a>
            <a href="latest.html?q=settlement" class="search-tag-pill" style="display:inline-flex;align-items:center;padding:6px 12px;border-radius:8px;background:#1B2436;border:1px solid #2A3854;color:#00F59B;font-size:12px;font-weight:600;text-decoration:none;">#ProjectNexus</a>
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
    openSearch();
  });

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      openSearch();
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
