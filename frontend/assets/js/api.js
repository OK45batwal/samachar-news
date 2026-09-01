// Samachar API Client — Resilient Multi-Port (5173/8000)

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('samachar_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  // Primary URL (relative)
  const primaryUrl = endpoint;
  // Fallback URL (direct backend on 8000)
  const fallbackUrl = `http://localhost:8000${endpoint}`;

  try {
    const res = await fetch(primaryUrl, { ...options, headers });
    if (res.ok) {
      return await res.json();
    }
    // If not ok on relative, try direct 8000 fallback
    if (window.location.port === '5173') {
      const fallbackRes = await fetch(fallbackUrl, { ...options, headers });
      if (fallbackRes.ok) {
        return await fallbackRes.json();
      }
      const err = await fallbackRes.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || `HTTP ${fallbackRes.status}`);
    }
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  } catch (primaryErr) {
    if (window.location.port === '5173' && !primaryUrl.startsWith('http')) {
      try {
        const fallbackRes = await fetch(fallbackUrl, { ...options, headers });
        if (fallbackRes.ok) {
          return await fallbackRes.json();
        }
        const err = await fallbackRes.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || `HTTP ${fallbackRes.status}`);
      } catch (fallbackErr) {
        console.error(`API Error [${endpoint}]:`, fallbackErr);
        throw fallbackErr;
      }
    }
    console.error(`API Error [${endpoint}]:`, primaryErr);
    throw primaryErr;
  }
}

// News Endpoints
async function getArticles(params = {}) {
  const query = new URLSearchParams();
  if (params.category) query.set('category', params.category);
  if (params.q) query.set('q', params.q);
  if (params.verified_only) query.set('verified_only', 'true');
  if (params.sort) query.set('sort', params.sort);
  if (params.page) query.set('page', params.page);
  if (params.limit) query.set('limit', params.limit);

  return request(`/api/news/?${query.toString()}`);
}

async function getArticleById(id) {
  return request(`/api/news/${id}`);
}

async function getTrending(limit = 6) {
  return request(`/api/news/trending?limit=${limit}`);
}

async function getVerifiedArticles(limit = 6) {
  return request(`/api/news/verified?limit=${limit}`);
}

async function getCategories() {
  return request('/api/news/categories');
}

async function getSources() {
  return request('/api/news/sources');
}

async function getStats() {
  return request('/api/news/stats');
}

// Interactive Fact-Checking Tool Endpoints
async function verifyClaim(queryText, queryType = 'claim') {
  return request('/api/fact-check/verify', {
    method: 'POST',
    body: JSON.stringify({ query: queryText, query_type: queryType }),
  });
}

async function getRecentFactChecks() {
  return request('/api/fact-check/recent');
}

// Auth Endpoints
async function registerUser(email, password, fullName) {
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
}

async function loginUser(email, password) {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (data.access_token) {
    localStorage.setItem('samachar_token', data.access_token);
    localStorage.setItem('samachar_user', JSON.stringify(data.user));
  }
  return data;
}

async function logoutUser() {
  try {
    await request('/api/auth/logout', { method: 'POST' });
  } finally {
    localStorage.removeItem('samachar_token');
    localStorage.removeItem('samachar_user');
    window.location.href = 'home.html';
  }
}

async function getMe() {
  return request('/api/auth/me');
}

async function getWsToken() {
  return request('/api/auth/ws-token');
}

async function forgotPassword(email) {
  return request('/api/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

async function resetPassword(token, newPassword) {
  return request('/api/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

// Bookmarks Endpoints
async function getBookmarks(folder = null) {
  const query = folder ? `?folder=${encodeURIComponent(folder)}` : '';
  return request(`/api/bookmarks/${query}`);
}

async function createBookmark(articleId, folder = 'default', notes = null) {
  return request('/api/bookmarks/', {
    method: 'POST',
    body: JSON.stringify({ article_id: articleId, folder, notes }),
  });
}

async function deleteBookmark(bookmarkId) {
  return request(`/api/bookmarks/${bookmarkId}`, {
    method: 'DELETE',
  });
}

// Helper: Check Current Auth
function getUser() {
  const userStr = localStorage.getItem('samachar_user');
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

function isAuthenticated() {
  return !!localStorage.getItem('samachar_token');
}
