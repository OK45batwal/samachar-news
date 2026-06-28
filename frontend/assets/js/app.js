const CATEGORY_MAP = {
  general: { name: 'General', badge: 'badge-accent' },
  world: { name: 'World', badge: 'badge-accent' },
  technology: { name: 'Technology', badge: 'badge-secondary' },
  business: { name: 'Business', badge: 'badge-warning' },
  sports: { name: 'Sports', badge: 'badge-accent' },
  science: { name: 'Science', badge: 'badge-secondary' },
  health: { name: 'Health', badge: 'badge-danger' },
  entertainment: { name: 'Entertainment', badge: 'badge-accent' },
  politics: { name: 'Politics', badge: 'badge-warning' },
};

function getCategoryStyle(slug) {
  return CATEGORY_MAP[slug?.toLowerCase()] || { name: slug || 'General', badge: 'badge-accent' };
}

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const sec = Math.floor((Date.now() - d) / 1000);
  if (sec < 60) return 'just now';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

function renderNewsCard(article, index = 0) {
  const cat = getCategoryStyle(article.category?.slug);
  const imgHtml = article.image_url
    ? `<img src="${article.image_url}" alt="${article.title}" style="width:100%;height:100%;object-fit:cover" loading="lazy" />`
    : `<div class="skeleton" style="width:100%;height:100%"></div>`;
  return `
    <a href="article.html?id=${article.id}" class="news-card animate-fade-in" style="animation-delay:${index * 0.05}s">
      <div class="news-card-img">
        ${imgHtml}
        <span class="badge ${cat.badge}" style="position:absolute;top:12px;left:12px;font-size:9px">${cat.name}</span>
      </div>
      <div class="news-card-body">
        <div class="news-card-meta">
          <span class="text-xs text-muted">${article.source?.name || 'Unknown'}</span>
          <span class="text-xs text-muted">·</span>
          <span class="text-xs text-muted">${timeAgo(article.published_at)}</span>
        </div>
        <h3 class="line-clamp-2">${article.title}</h3>
        <p class="line-clamp-2 mt-1">${article.summary || ''}</p>
      </div>
      <div class="news-card-footer">
        <span class="text-xs text-muted">${(article.view_count || 0).toLocaleString()} views</span>
        <div class="news-card-actions">
          <button class="btn btn-icon btn-ghost" onclick="event.stopPropagation();toggleBookmark(${article.id})" title="Bookmark">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>
          </button>
          <button class="btn btn-icon btn-ghost" onclick="event.stopPropagation();shareArticle('${article.title}')" title="Share">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
          </button>
        </div>
      </div>
    </a>
  `;
}

function emptyState(msg, cta) {
  return `<div class="card p-8 text-center" style="grid-column:1/-1"><p class="text-muted">${msg}</p>${cta || ''}</div>`;
}

// ─── WebSocket ──────────────────────────────
let ws = null;
function connectWS() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${proto}//${window.location.host}/ws/news`;
  try {
    ws = new WebSocket(url);
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'news_alert') {
          showToast(`📰 ${msg.data.title || 'Breaking news update!'}`);
        }
        if (msg.type === 'pong') { /* keepalive ok */ }
      } catch {}
    };
    ws.onclose = () => { setTimeout(connectWS, 3000); };
    ws.onopen = () => { setInterval(() => ws?.send(JSON.stringify({type:'ping'})), 30000); };
  } catch {}
}
connectWS();

// ─── Live search dropdown ───────────────────
function setupLiveSearch() {
  const input = document.getElementById('globalSearch');
  const overlay = document.getElementById('searchOverlay');
  if (!input) return;
  let container = document.getElementById('searchResults');
  if (!container) {
    container = document.createElement('div');
    container.id = 'searchResults';
    container.style.cssText = 'margin-top:12px;max-height:300px;overflow-y:auto';
    document.querySelector('.search-modal')?.appendChild(container);
  }
  let timer;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) { container.innerHTML = ''; return; }
    timer = setTimeout(async () => {
      container.innerHTML = '<div class="text-xs text-muted p-2">Searching...</div>';
      try {
        const data = await getArticles({ q, limit: 6 });
        if (data.articles?.length) {
          container.innerHTML = data.articles.map(a =>
            `<a href="article.html?id=${a.id}" class="flex items-center gap-2 p-2" style="border-radius:var(--radius-sm);text-decoration:none;color:var(--text-primary);font-size:13px" onmouseover="this.style.background='var(--bg-hover)'" onmouseout="this.style.background='transparent'">
              <span class="text-xs text-muted">${getCategoryStyle(a.category?.slug).name}</span>
              <span class="flex-1 line-clamp-1">${a.title}</span>
              <span class="text-xs text-muted">${timeAgo(a.published_at)}</span>
            </a>`
          ).join('');
        } else {
          container.innerHTML = '<div class="text-xs text-muted p-2">No results found</div>';
        }
      } catch { container.innerHTML = '<div class="text-xs text-muted p-2">Search failed</div>'; }
    }, 300);
  });
  overlay?.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { container.innerHTML = ''; }
  });
}

// ─── Load More (infinite pagination) ───────
let loadMoreCtrl = null;

function setupLoadMore() {
  const pag = document.getElementById('pagination');
  const list = document.getElementById('newsList');
  const btn = document.getElementById('loadMoreBtn');
  if (!pag || !list || !btn) return;

  const state = { page: 1, limit: 12, total: 0, category: '', query: '', loading: false, allLoaded: false };

  async function fetch(reset = false) {
    if (state.loading || (!reset && state.allLoaded)) return;
    if (reset) { state.page = 1; state.allLoaded = false; }
    state.loading = true;
    btn.textContent = 'Loading...';
    btn.disabled = true;

    try {
      const opts = { page: state.page, limit: state.limit };
      if (state.category) opts.category = state.category;
      if (state.query) opts.q = state.query;
      const data = await getArticles(opts);
      state.total = data.total || 0;

      if (reset) {
        list.innerHTML = data.articles?.length
          ? data.articles.map((a, i) => renderNewsCard(a, i)).join('')
          : emptyState('No articles found');
      } else {
        const start = list.children.length;
        data.articles?.forEach((a, i) => list.insertAdjacentHTML('beforeend', renderNewsCard(a, start + i)));
      }

      state.allLoaded = state.page * state.limit >= state.total;
      state.page++;
      btn.textContent = state.allLoaded ? 'All loaded' : 'Load More';
      btn.disabled = state.allLoaded;
    } catch {
      btn.textContent = 'Error — Try Again';
      btn.disabled = false;
    }
    state.loading = false;
  }

  btn.addEventListener('click', () => fetch(false));

  loadMoreCtrl = {
    reset(category = '', query = '') {
      state.category = category;
      state.query = query;
      fetch(true);
    }
  };

  const params = new URLSearchParams(window.location.search);
  state.category = params.get('cat') || '';
  state.query = params.get('q') || '';
  fetch(true);
}

// ─── Initialize pages ──────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  const user = getUser();
  const signInBtn = document.querySelector('.header-right a[href="login.html"]');
  if (user && signInBtn) {
    signInBtn.innerHTML = `<span class="badge badge-accent" style="font-size:10px">${user.username}</span>`;
    signInBtn.href = 'profile.html';
    const gs = document.querySelector('.header-right a[href="register.html"]');
    if (gs) { gs.textContent = 'Sign Out'; gs.href = '#'; gs.onclick = (e) => { e.preventDefault(); logout(); }; }
  }

  // Hero stats
  const heroStats = document.querySelector('.hero-stats');
  if (heroStats) {
    try {
      const stats = await getStats();
      heroStats.innerHTML = `
        <div><strong class="text-accent">${(stats.articles_analyzed || 0).toLocaleString()}</strong><span class="text-muted text-xs">Articles Curated</span></div>
        <div><strong class="text-accent">${stats.sentiment_score || 0}%</strong><span class="text-muted text-xs">Sentiment Score</span></div>
        <div><strong class="text-accent">${150}</strong><span class="text-muted text-xs">Countries Covered</span></div>
      `;
    } catch {}
  }

  // AI stats
  const aiStats = document.getElementById('aiStats');
  if (aiStats) {
    try {
      const stats = await getStats();
      aiStats.innerHTML = `
        <div class="card insight-card"><div class="text-xs text-muted mb-1">Articles Analyzed</div><div class="insight-value text-accent">${(stats.articles_analyzed || 0).toLocaleString()}</div></div>
        <div class="card insight-card"><div class="text-xs text-muted mb-1">Sentiment Score</div><div class="insight-value" style="color:var(--accent)">${stats.sentiment_score >= 0 ? '+' : ''}${stats.sentiment_score || 0}</div></div>
        <div class="card insight-card"><div class="text-xs text-muted mb-1">Risk Index</div><div class="insight-value" style="color:var(--warning)">${stats.risk_index || 0}</div></div>
        <div class="card insight-card"><div class="text-xs text-muted mb-1">Confidence</div><div class="insight-value text-accent">${stats.confidence || 0}%</div></div>
      `;
    } catch {}
  }

  // News grid (index)
  const newsGrid = document.getElementById('newsGrid');
  if (newsGrid) {
    try {
      const data = await getArticles({ limit: 6 });
      newsGrid.innerHTML = data.articles?.length
        ? data.articles.map((a, i) => renderNewsCard(a, i)).join('')
        : emptyState('No articles yet. Run feed ingestion to populate.');
    } catch { newsGrid.innerHTML = emptyState('Failed to load articles. Is the backend running?'); }
  }

  // News list (latest) with Load More
  const newsList = document.getElementById('newsList');
  if (newsList) {
    document.querySelectorAll('.category-tabs button').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelector('.category-tabs .active')?.classList.remove('active');
        btn.classList.add('active');
        const cat = btn.textContent.trim() === 'All' ? '' : btn.textContent.trim().toLowerCase();
        showSkeleton(newsList, 6);
        loadMoreCtrl?.reset(cat, '');
      });
    });

    setupLoadMore();
  }

  // Article page
  const articleTitle = document.getElementById('articleTitle');
  if (articleTitle) {
    const id = parseInt(new URLSearchParams(window.location.search).get('id') || '0');
    if (!id) { articleTitle.textContent = 'Article not found'; return; }
    try {
      const article = await getArticle(id);
      const cat = getCategoryStyle(article.category?.slug);
      document.getElementById('articleTitle').textContent = article.title;
      document.getElementById('articleSource').textContent = article.source?.name || 'Unknown';
      document.getElementById('articleTime').textContent = timeAgo(article.published_at);
      document.getElementById('articleCategory').textContent = cat.name;
      document.getElementById('articleReadTime').textContent = `${Math.max(1, Math.ceil((article.content?.length || 0) / 1500))} min read`;
      document.getElementById('articleSummary').textContent = article.summary || '';
      document.getElementById('articleContent').innerHTML =
        (article.content || article.summary || 'No content available')
          .split('\n').filter(Boolean).map(p => `<p>${p}</p>`).join('');
      document.getElementById('articleAiSummary').textContent = article.summary
        ? `Sentiment: ${(article.sentiment_score || 0) > 0 ? 'positive' : (article.sentiment_score || 0) < 0 ? 'negative' : 'neutral'} (score: ${article.sentiment_score || 0}). Key topics include ${article.title?.toLowerCase()}.`
        : 'AI analysis not available.';
      const heroImg = document.querySelector('.article-hero .skeleton');
      if (heroImg && article.image_url) {
        heroImg.outerHTML = `<img src="${article.image_url}" alt="${article.title}" style="width:100%;height:100%;object-fit:cover" />`;
      }
      const related = document.getElementById('relatedArticles');
      if (related) {
        try {
          const rd = await getArticles({ category: article.category?.slug, limit: 4 });
          const filtered = (rd.articles || []).filter(a => a.id !== article.id).slice(0, 3);
          if (filtered.length) {
            related.innerHTML = filtered.map(a =>
              `<a href="article.html?id=${a.id}" class="card p-4 flex gap-3"><div class="min-w-0 flex-1"><h4 class="text-sm font-semibold line-clamp-2">${a.title}</h4><span class="text-xs text-muted">${timeAgo(a.published_at)}</span></div></a>`
            ).join('');
          }
        } catch {}
      }
    } catch (err) {
      articleTitle.textContent = 'Failed to load article';
      document.getElementById('articleContent').innerHTML = `<p class="text-muted">${err.message}</p>`;
    }
  }

  // Search
  setupLiveSearch();

  // Bookmarks page
  const bookmarksContainer = document.getElementById('bookmarksContainer');
  if (bookmarksContainer && getUser()) {
    try {
      const bms = await getBookmarks();
      if (bms.length === 0) {
        bookmarksContainer.innerHTML = emptyBookmarksHTML();
      } else {
        bookmarksContainer.innerHTML = bms.map(bm => renderNewsCard(bm.article)).join('');
      }
    } catch { bookmarksContainer.innerHTML = emptyBookmarksHTML(); }
  }
});

// ── Utilities ──────────────────────────────
function emptyBookmarksHTML() {
  return '<div class="card empty-state p-8" style="grid-column:1/-1">' +
    '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>' +
    '<h3 class="font-semibold mb-2">No bookmarks yet</h3>' +
    '<p class="text-sm text-muted">Save articles while reading to see them here</p>' +
    '<a href="latest.html" class="btn btn-primary btn-sm mt-4">Browse News</a></div>';
}

async function toggleBookmark(id) {
  try {
    const user = getUser();
    if (!user) { showToast('Sign in to bookmark articles'); return; }
    const bookmarks = await getBookmarks();
    const existing = bookmarks.find(b => b.article_id === id);
    if (existing) { await removeBookmark(id); showToast('Removed from bookmarks'); }
    else { await addBookmark(id); showToast('Saved to bookmarks'); }
  } catch (err) { showToast(err.message); }
}

function shareArticle(title) {
  if (navigator.share) navigator.share({ title }).catch(() => {});
  else { navigator.clipboard?.writeText(window.location.href); showToast('Link copied to clipboard'); }
}

function showToast(msg) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}
