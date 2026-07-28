const API_BASE = '';

function getCookie(name) {
  var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

async function api(path, options = {}) {
  const { body, method = 'GET', ...rest } = options;
  const headers = { 'Content-Type': 'application/json', ...rest.headers };

  if (method !== 'GET') {
    var csrf = getCookie('csrf_token');
    if (csrf) headers['X-CSRF-Token'] = csrf;
  }

  let res = await fetch(API_BASE + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
    ...rest,
  });

  if (!res.ok) {
    const err = await res.json().catch(function() { return { detail: res.statusText }; });
    throw new Error(err.detail || 'Request failed: ' + res.status);
  }

  return res.json();
}

// --- Auth ---
async function login(email, password) {
  const user = await api('/api/auth/login', {
    method: 'POST',
    body: { email, password },
  });
  localStorage.setItem('samachar_user', JSON.stringify(user));
  return user;
}

async function register(email, password, fullName) {
  const user = await api('/api/auth/register', {
    method: 'POST',
    body: { email, password, full_name: fullName || undefined },
  });
  localStorage.setItem('samachar_user', JSON.stringify(user));
  return user;
}

async function getMe() {
  const user = await api('/api/auth/me');
  localStorage.setItem('samachar_user', JSON.stringify(user));
  return user;
}

function logout() {
  fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).catch(() => {});
  localStorage.removeItem('samachar_user');
  window.location.href = 'login.html';
}

async function updateProfile(data) {
  const user = await api('/api/auth/me', {
    method: 'PUT',
    body: data,
  });
  localStorage.setItem('samachar_user', JSON.stringify(user));
  return user;
}

async function forgotPassword(email) {
  return api('/api/auth/forgot-password', {
    method: 'POST',
    body: { email },
  });
}

async function resetPassword(token, newPassword) {
  return api('/api/auth/reset-password', {
    method: 'POST',
    body: { token, new_password: newPassword },
  });
}

function getUser() {
  const raw = localStorage.getItem('samachar_user');
  return raw ? JSON.parse(raw) : null;
}

// --- News ---
async function getArticles(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return api(`/api/news/?${qs}`, { method: 'GET' });
}

async function getArticle(id) {
  return api(`/api/news/${id}`, { method: 'GET' });
}

// --- Bookmarks ---
async function getBookmarks() {
  return api('/api/bookmarks/');
}

async function addBookmark(articleId, folder = 'default') {
  return api('/api/bookmarks/', { method: 'POST', body: { article_id: articleId, folder } });
}

async function removeBookmark(articleId) {
  return api(`/api/bookmarks/${articleId}`, { method: 'DELETE' });
}

// --- Stats ---
async function getStats() {
  return api('/api/stats', { method: 'GET' });
}

// --- Search ---
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
