const API_BASE = '';

function getToken() {
  return localStorage.getItem('samachar_token');
}

function setToken(token, refreshToken) {
  localStorage.setItem('samachar_token', token);
  if (refreshToken) localStorage.setItem('samachar_refresh', refreshToken);
}

function clearTokens() {
  localStorage.removeItem('samachar_token');
  localStorage.removeItem('samachar_refresh');
  localStorage.removeItem('samachar_user');
}

async function refreshAccessToken() {
  const refresh = localStorage.getItem('samachar_refresh');
  if (!refresh) return null;
  try {
    const res = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) { clearTokens(); return null; }
    const data = await res.json();
    setToken(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

async function api(path, options = {}) {
  const { body, method = 'GET', auth = true, ...rest } = options;
  const headers = { 'Content-Type': 'application/json', ...rest.headers };

  if (auth) {
    let token = getToken();
    if (!token) {
      token = await refreshAccessToken();
      if (!token) throw new Error('Not authenticated');
    }
    headers['Authorization'] = `Bearer ${token}`;
  }

  let res = await fetch(`${API_BASE}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined, ...rest });

  if (res.status === 401 && auth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`;
      res = await fetch(`${API_BASE}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined, ...rest });
    } else {
      throw new Error('Session expired. Please sign in again.');
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

// ─── Auth ──────────────────────────────────────
async function login(username, password) {
  const data = await api('/api/auth/login', { method: 'POST', body: { username, password }, auth: false });
  setToken(data.access_token, data.refresh_token);
  localStorage.setItem('samachar_user', JSON.stringify(data.user));
  return data;
}

async function register(email, username, password, fullName) {
  const data = await api('/api/auth/register', { method: 'POST', body: { email, username, password, full_name: fullName }, auth: false });
  setToken(data.access_token, data.refresh_token);
  localStorage.setItem('samachar_user', JSON.stringify(data.user));
  return data;
}

async function getMe() {
  return api('/api/auth/me');
}

function logout() {
  clearTokens();
  window.location.href = 'login.html';
}

function getUser() {
  const raw = localStorage.getItem('samachar_user');
  return raw ? JSON.parse(raw) : null;
}

// ─── News ──────────────────────────────────────
async function getArticles(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return api(`/api/news/?${qs}`, { auth: false });
}

async function getArticle(id) {
  return api(`/api/news/${id}`, { auth: false });
}

// ─── Bookmarks ─────────────────────────────────
async function getBookmarks() {
  return api('/api/bookmarks/');
}

async function addBookmark(articleId, folder = 'default') {
  return api('/api/bookmarks/', { method: 'POST', body: { article_id: articleId, folder } });
}

async function removeBookmark(articleId) {
  return api(`/api/bookmarks/${articleId}`, { method: 'DELETE' });
}

// ─── Stats ─────────────────────────────────────
async function getStats() {
  return api('/api/stats', { auth: false });
}

// ─── Search ────────────────────────────────────
window.searchNews = async function(query) {
  const results = await getArticles({ q: query, limit: 10 });
  return results.articles || [];
}
