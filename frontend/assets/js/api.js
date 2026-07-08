const API_BASE = '';

async function api(path, options = {}) {
  const { body, method = 'GET', ...rest } = options;
  const headers = { 'Content-Type': 'application/json', ...rest.headers };

  let res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
    ...rest,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

// ─── Auth ──────────────────────────────────────
async function login(email, password) {
  const data = await api('/auth/signin', {
    method: 'POST',
    body: { formFields: [{ id: 'email', value: email }, { id: 'password', value: password }] },
  });
  if (data.status !== 'OK') {
    throw new Error(data.status === 'WRONG_CREDENTIALS_ERROR' ? 'Invalid email or password' : 'Login failed');
  }
  // Fetch local user profile — create it if missing
  try {
    const user = await api('/api/auth/me');
    localStorage.setItem('samachar_user', JSON.stringify(user));
  } catch {
    const username = email.split('@')[0];
    await api('/api/auth/profile', { method: 'POST', body: { email, username } });
    const user = await api('/api/auth/me');
    localStorage.setItem('samachar_user', JSON.stringify(user));
  }
  return data;
}

async function register(email, password) {
  const data = await api('/auth/signup', {
    method: 'POST',
    body: { formFields: [{ id: 'email', value: email }, { id: 'password', value: password }] },
  });
  if (data.status !== 'OK') {
    throw new Error(data.status === 'FIELD_ERROR' ? data.formFields?.[0]?.error || 'Registration failed' : 'Registration failed');
  }
  // Auto-generate username from email
  const username = email.split('@')[0];
  // Create local profile
  await api('/api/auth/profile', {
    method: 'POST',
    body: { email, username },
  });
  const user = await api('/api/auth/me');
  localStorage.setItem('samachar_user', JSON.stringify(user));
  return data;
}

async function getMe() {
  const user = await api('/api/auth/me');
  localStorage.setItem('samachar_user', JSON.stringify(user));
  return user;
}

function logout() {
  fetch('/auth/signout', { method: 'POST', credentials: 'include' }).catch(() => {});
  localStorage.removeItem('samachar_user');
  window.location.href = 'login.html';
}

function getUser() {
  const raw = localStorage.getItem('samachar_user');
  return raw ? JSON.parse(raw) : null;
}

// ─── News ──────────────────────────────────────
async function getArticles(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return api(`/api/news/?${qs}`, { method: 'GET' });
}

async function getArticle(id) {
  return api(`/api/news/${id}`, { method: 'GET' });
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
  return api('/api/stats', { method: 'GET' });
}

// ─── Search ────────────────────────────────────
async function searchNews(query) {
  const results = await getArticles({ q: query, limit: 10 });
  return results.articles || [];
}

async function getWsToken() {
  return api('/api/auth/ws-token');
}

// Make all exports available globally (for inline scripts in HTML pages)
window.getWsToken = getWsToken;
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
