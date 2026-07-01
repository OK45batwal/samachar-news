const API_BASE = '';

export function getToken() {
  return localStorage.getItem('samachar_token');
}

export function setToken(token, refreshToken) {
  localStorage.setItem('samachar_token', token);
  if (refreshToken) localStorage.setItem('samachar_refresh', refreshToken);
}

export function clearTokens() {
  localStorage.removeItem('samachar_token');
  localStorage.removeItem('samachar_refresh');
  localStorage.removeItem('samachar_user');
}

export async function refreshAccessToken() {
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

export async function api(path, options = {}) {
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
export async function login(username, password) {
  const data = await api('/api/auth/login', { method: 'POST', body: { username, password }, auth: false });
  setToken(data.access_token, data.refresh_token);
  localStorage.setItem('samachar_user', JSON.stringify(data.user));
  return data;
}

export async function register(email, username, password, fullName) {
  const data = await api('/api/auth/register', { method: 'POST', body: { email, username, password, full_name: fullName }, auth: false });
  setToken(data.access_token, data.refresh_token);
  localStorage.setItem('samachar_user', JSON.stringify(data.user));
  return data;
}

export async function getMe() {
  return api('/api/auth/me');
}

export function logout() {
  clearTokens();
  window.location.href = 'login.html';
}

export function getUser() {
  const raw = localStorage.getItem('samachar_user');
  return raw ? JSON.parse(raw) : null;
}

// ─── News ──────────────────────────────────────
export async function getArticles(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return api(`/api/news/?${qs}`, { auth: false });
}

export async function getArticle(id) {
  return api(`/api/news/${id}`, { auth: false });
}

// ─── Bookmarks ─────────────────────────────────
export async function getBookmarks() {
  return api('/api/bookmarks/');
}

export async function addBookmark(articleId, folder = 'default') {
  return api('/api/bookmarks/', { method: 'POST', body: { article_id: articleId, folder } });
}

export async function removeBookmark(articleId) {
  return api(`/api/bookmarks/${articleId}`, { method: 'DELETE' });
}

// ─── Stats ─────────────────────────────────────
export async function getStats() {
  return api('/api/stats', { auth: false });
}

// ─── Search ────────────────────────────────────
export async function searchNews(query) {
  const results = await getArticles({ q: query, limit: 10 });
  return results.articles || [];
}

// Make all exports available globally (for inline scripts in HTML pages)
window.getToken = getToken;
window.setToken = setToken;
window.clearTokens = clearTokens;
window.refreshAccessToken = refreshAccessToken;
window.api = api;
window.login = login;
window.register = register;
window.getMe = getMe;
window.logout = logout;
window.getUser = getUser;
window.getArticles = getArticles;
window.getArticle = getArticle;
window.getBookmarks = getBookmarks;
window.addBookmark = addBookmark;
window.removeBookmark = removeBookmark;
window.getStats = getStats;
window.searchNews = searchNews;
