function sanitize(str) {
  if (!str) return '';
  var el = document.createElement('div');
  el.textContent = str;
  return el.innerHTML;
}

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
  var safeTitle = sanitize(article.title);
  var safeSummary = sanitize(article.summary);
  var safeSource = sanitize(article.source?.name || 'Unknown');
  var safeImgUrl = article.image_url && article.image_url.startsWith('http') ? article.image_url : '';
  var imgHtml = safeImgUrl
    ? '<img src="' + safeImgUrl + '" alt="' + safeTitle + '" style="width:100%;height:100%;object-fit:cover" loading="lazy" />'
    : '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:var(--bg-elevated)"><svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></div>';
  var parts = [];
  parts.push('<a href="article.html?id=' + article.id + '" class="news-card animate-fade-in" style="animation-delay:' + (index * 0.05) + 's">');
  parts.push('<div class="news-card-img">' + imgHtml);
  parts.push('<span class="badge ' + cat.badge + '" style="position:absolute;top:12px;left:12px;font-size:9px">' + cat.name + '</span></div>');
  parts.push('<div class="news-card-body">');
  parts.push('<div class="news-card-meta"><span class="text-xs text-muted">' + safeSource + '</span><span class="text-xs text-muted">·</span><span class="text-xs text-muted">' + timeAgo(article.published_at) + '</span></div>');
  parts.push('<h3 class="line-clamp-2">' + safeTitle + '</h3>');
  parts.push('<p class="line-clamp-2 mt-1">' + safeSummary + '</p></div>');
  parts.push('<div class="news-card-footer"><span class="text-xs text-muted">' + (article.view_count || 0).toLocaleString() + ' views</span>');
  parts.push('<div class="news-card-actions">');
  parts.push('<button class="btn btn-icon btn-ghost" onclick="event.stopPropagation();toggleBookmark(' + article.id + ')" title="Bookmark"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg></button>');
  parts.push('<button class="btn btn-icon btn-ghost" onclick="event.stopPropagation();shareArticle(\'' + safeTitle + '\')" title="Share"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg></button>');
  parts.push('</div></div>');
  parts.push('</a>');
  return parts.join('');
}

function emptyState(msg, cta) {
  var safeMsg = sanitize(msg);
  return '<div class="card p-8 text-center" style="grid-column:1/-1"><p class="text-muted">' + safeMsg + '</p>' + (cta || '') + '</div>';
}

// ─── WebSocket ──────────────────────────────
let ws = null;
let wsPingInterval = null;
function connectWS() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${proto}//${window.location.host}/api/ws`;
  try {
    ws = new WebSocket(url);
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'auth_ok') {
          wsPingInterval = setInterval(() => ws?.send(JSON.stringify({type:'ping'})), 30000);
        }
        if (msg.type === 'auth_error') {
          console.warn('WS auth:', msg.message);
          ws?.close();
        }
        if (msg.type === 'news_alert') {
          showToast(`📰 ${msg.data.title || 'Breaking news update!'}`);
        }
      } catch (e) { console.warn('WS parse error:', e); }
    };
    ws.onclose = () => {
      if (wsPingInterval) clearInterval(wsPingInterval);
      wsPingInterval = null;
      setTimeout(connectWS, 3000);
    };
    ws.onopen = async () => {
      try {
        const { token } = await getWsToken();
        ws.send(JSON.stringify({type:'auth', token}));
      } catch (e) {
        console.warn('WS auth failed:', e);
        ws.close();
      }
    };
  } catch (e) { console.warn('WS connect failed:', e); }
}
if (getUser()) connectWS();

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
    } catch { heroStats.innerHTML = '<div class="text-muted text-sm">Failed to load stats</div>'; }
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
    } catch { aiStats.innerHTML = '<div class="card insight-card p-6 text-center text-muted">Failed to load AI stats</div>'; }
  }

  // Home page — featured grid
  const featuredGrid = document.getElementById('featuredGrid');
  if (featuredGrid) {
    try {
      const data = await getArticles({ limit: 5 });
      const articles = data.articles || [];
      if (articles.length) {
        const main = articles[0];
        const side = articles.slice(1, 4);
        const catMain = getCategoryStyle(main.category?.slug);
        featuredGrid.innerHTML = `
          <a href="article.html?id=${main.id}" class="featured-main card card-glow">
            <div class="featured-img">
              ${main.image_url?.startsWith('http') ? `<img src="${main.image_url}" alt="${main.title}" style="width:100%;height:100%;object-fit:cover" />` : '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:var(--bg-elevated)"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></div>'}
              <span class="badge ${catMain.badge}" style="position:absolute;top:16px;left:16px;font-size:9px">${catMain.name}</span>
            </div>
            <div class="featured-body">
              <div class="flex items-center gap-2 text-xs text-muted mb-2">
                <span>${main.source?.name || 'News'}</span>
                <span>·</span>
                <span>${timeAgo(main.published_at)}</span>
              </div>
              <h3 class="heading-md mb-2 line-clamp-2">${main.title}</h3>
              <p class="text-muted text-sm line-clamp-2">${main.summary || ''}</p>
            </div>
          </a>
          <div class="featured-side">
            ${side.map(a => {
              const cat = getCategoryStyle(a.category?.slug);
              return `<a href="article.html?id=${a.id}" class="card card-glow p-4">
                <div class="flex gap-3">
                  ${a.image_url?.startsWith('http') ? `<img src="${a.image_url}" alt="" style="width:100px;height:70px;object-fit:cover;border-radius:8px;flex-shrink:0" />` : '<div style="width:100px;height:70px;border-radius:8px;flex-shrink:0;display:flex;align-items:center;justify-content:center;background:var(--bg-elevated)"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></div>'}
                  <div class="flex-1 min-w-0">
                    <h4 class="font-semibold text-sm line-clamp-2">${a.title}</h4>
                    <span class="text-xs text-muted mt-1">${cat.name} · ${timeAgo(a.published_at)}</span>
                  </div>
                </div>
              </a>`;
            }).join('')}
          </div>`;
      } else {
        featuredGrid.innerHTML = '<div style="grid-column:1/-1;padding:48px;text-align:center;color:var(--text-secondary)">No stories yet. Run feed ingestion.</div>';
      }
    } catch {
      featuredGrid.innerHTML = '<div style="grid-column:1/-1;padding:48px;text-align:center;color:var(--text-secondary)">Failed to load stories</div>';
    }
  }

  // Ticker — live from recent articles
  const tickerTrack = document.getElementById('tickerTrack');
  if (tickerTrack) {
    try {
      const data = await getArticles({ limit: 10 });
      const titles = (data.articles || []).map(a => a.title).filter(Boolean);
      if (titles.length) {
        const items = titles.map(t => `<span>${t}</span><span>&middot;</span>`).join(' ');
        tickerTrack.innerHTML = items + ' ' + items;
      } else {
        tickerTrack.innerHTML = '<span>No breaking news at the moment</span>';
      }
    } catch {
      tickerTrack.innerHTML = '<span>Failed to load headlines</span>';
    }
  }

  // News list (latest) with Load More
  const newsList = document.getElementById('newsList');
  if (newsList) {
    document.querySelectorAll('.category-tabs button').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelector('.category-tabs .active')?.classList.remove('active');
        btn.classList.add('active');
        const cat = btn.dataset.cat || '';
        showSkeleton(newsList, 6);
        loadMoreCtrl?.reset(cat, '');
        const url = new URL(window.location);
        if (cat) url.searchParams.set('cat', cat);
        else url.searchParams.delete('cat');
        window.history.replaceState({}, '', url);
      });
    });

    const params = new URLSearchParams(window.location.search);
    const catParam = params.get('cat');
    if (catParam) {
      document.querySelectorAll('.category-tabs button').forEach(btn => {
        if (btn.dataset.cat === catParam) {
          document.querySelector('.category-tabs .active')?.classList.remove('active');
          btn.classList.add('active');
        }
      });
    }

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
      document.getElementById('articleReadTime').textContent = Math.max(1, Math.ceil((article.content?.length || 0) / 1500)) + ' min read';
      document.getElementById('articleViewCount').textContent = (article.view_count || 0).toLocaleString() + ' views';

      var initial = (article.source?.name || 'U')[0].toUpperCase();
      document.getElementById('articleAvatar').textContent = initial;

      // Hero image with fallback gradient
      var heroEl = document.getElementById('articleHero');
      var heroSkeleton = heroEl.querySelector('.skeleton');
      if (article.image_url && article.image_url.startsWith('http')) {
        var imgUrl = article.image_url.replace(/"/g, '');
        heroSkeleton.outerHTML = '<img src="' + imgUrl + '" alt="' + sanitize(article.title) + '" class="article-hero-img" loading="lazy" srcset="' + imgUrl + ' 480w, ' + imgUrl + ' 768w, ' + imgUrl + ' 1200w" sizes="(max-width: 480px) 480px, (max-width: 768px) 768px, 1200px" onerror="this.style.display=\'none\';this.parentElement.querySelector(\'.article-hero-fallback\').style.display=\'flex\'" />';
        var fallback = document.createElement('div');
        fallback.className = 'article-hero-fallback';
        fallback.style.display = 'none';
        fallback.innerHTML = '<svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>';
        heroEl.insertBefore(fallback, heroEl.querySelector('.article-hero-gradient'));
      } else {
        heroSkeleton.outerHTML = '<div class="article-hero-fallback"><svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></div>';
      }

      // Content rendering
      var skeleton = document.getElementById('articleSkeleton');
      if (skeleton) skeleton.remove();
      var bodyContainer = document.getElementById('articleBody');
      var rawContent = article.content || article.summary || 'No content available.';

      // Try parsing as HTML, fallback to plain text
      bodyContainer.innerHTML = renderArticleContent(rawContent);

      // AI Summary
      var aiEl = document.getElementById('articleAiSummary');
      aiEl.textContent = article.summary
        ? article.summary.length > 200
          ? article.summary.slice(0, 200) + '...'
          : article.summary
        : 'AI analysis not available for this article.';

      // Bookmark
      var bookmarkBtn = document.getElementById('bookmarkBtn');
      if (bookmarkBtn) bookmarkBtn.onclick = function() { toggleBookmark(article.id); };

      // Reading progress
      var progressBar = document.getElementById('progressBar');
      if (progressBar) {
        window.addEventListener('scroll', function() {
          var scrollTop = window.scrollY;
          var docHeight = document.documentElement.scrollHeight - window.innerHeight;
          progressBar.style.width = (docHeight > 0 ? Math.min(scrollTop / docHeight * 100, 100) : 0) + '%';
        });
      }

      // Related articles with images
      var related = document.getElementById('relatedArticles');
      if (related) {
        try {
          var rd = await getArticles({ category: article.category?.slug, limit: 5 });
          var filtered = (rd.articles || []).filter(function(a) { return a.id !== article.id; }).slice(0, 3);
          related.innerHTML = '';
          if (filtered.length) {
            filtered.forEach(function(a) {
              var imgUrl = a.image_url && a.image_url.startsWith('http') ? a.image_url : '';
              var thumbHtml = imgUrl
                ? '<img src="' + imgUrl + '" alt="" style="width:80px;height:60px;object-fit:cover;border-radius:6px;flex-shrink:0" loading="lazy" />'
                : '<div style="width:80px;height:60px;border-radius:6px;background:var(--bg-elevated);flex-shrink:0;display:flex;align-items:center;justify-content:center"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></div>';
              var link = document.createElement('a');
              link.href = 'article.html?id=' + a.id;
              link.className = 'card p-3 flex gap-3 items-center';
              link.innerHTML = thumbHtml + '<div class="min-w-0 flex-1"><h4 class="text-sm font-semibold line-clamp-2" style="color:var(--text-primary)">' + sanitize(a.title) + '</h4><span class="text-xs text-muted">' + timeAgo(a.published_at) + '</span></div>';
              related.appendChild(link);
            });
          } else {
            related.innerHTML = '<p class="text-xs text-muted">No related articles found</p>';
          }
        } catch (_) {
          related.innerHTML = '<p class="text-xs text-muted">Failed to load related articles</p>';
        }
      }
    } catch (err) {
      articleTitle.textContent = 'Failed to load article';
      var skeleton = document.getElementById('articleSkeleton');
      if (skeleton) skeleton.remove();
      document.getElementById('articleBody').innerHTML = '<div class="card p-6 text-center"><p class="text-muted">' + sanitize(err.message) + '</p></div>';
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

// ── HTML content renderer (safe, limited tags) ──
function renderArticleContent(raw) {
  if (!raw) return '<p class="text-muted">No content available.</p>';
  var el = document.createElement('div');
  el.innerHTML = raw;
  var allowed = { p:1, h1:1, h2:1, h3:1, h4:1, h5:1, h6:1, ul:1, ol:1, li:1, blockquote:1, pre:1, code:1, img:1, a:1, br:1, strong:1, em:1, b:1, i:1, u:1, s:1, sub:1, sup:1, hr:1, div:1, span:1, table:1, thead:1, tbody:1, tr:1, th:1, td:1, figure:1, figcaption:1 };

  function walk(node) {
    if (node.nodeType === 3) return node; // text nodes pass through
    if (node.nodeType !== 1) return null; // skip comments etc

    var tag = node.tagName.toLowerCase();
    if (!allowed[tag]) {
      // unwrap — keep children, discard wrapper
      var fragment = document.createDocumentFragment();
      while (node.firstChild) {
        var child = walk(node.firstChild);
        if (child) fragment.appendChild(child);
      }
      return fragment;
    }

    var clone = document.createElement(tag);
    // Copy safe attributes
    if (tag === 'a' && node.getAttribute('href')) {
      var href = node.getAttribute('href');
      if (href.startsWith('http') || href.startsWith('/')) {
        clone.setAttribute('href', href);
        clone.setAttribute('rel', 'noopener noreferrer');
        clone.setAttribute('target', '_blank');
      }
    }
    if (tag === 'img') {
      var src = node.getAttribute('src');
      if (src && src.startsWith('http')) {
        clone.setAttribute('src', src);
        clone.setAttribute('alt', node.getAttribute('alt') || '');
        clone.setAttribute('loading', 'lazy');
        clone.style.maxWidth = '100%';
        clone.style.borderRadius = 'var(--radius-md)';
      } else {
        return null; // skip invalid images
      }
    }
    if (tag === 'td' || tag === 'th') {
      var colspan = node.getAttribute('colspan');
      if (colspan) clone.setAttribute('colspan', colspan);
    }

    // Copy classes for <pre> styling etc
    if (tag === 'pre' || tag === 'code') {
      var cls = node.getAttribute('class');
      if (cls) clone.setAttribute('class', cls);
    }

    while (node.firstChild) {
      var child = walk(node.firstChild);
      if (child) clone.appendChild(child);
    }
    return clone;
  }

  var result = walk(el);
  return result ? result.innerHTML : '<p class="text-muted">No content available.</p>';
}

// ── Utilities ──────────────────────────────
function emptyBookmarksHTML() {
  return '<div class="card empty-state p-8" style="grid-column:1/-1">' +
    '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="2"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>' +
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

window.CATEGORY_MAP = CATEGORY_MAP;
window.getCategoryStyle = getCategoryStyle;
window.timeAgo = timeAgo;
window.renderNewsCard = renderNewsCard;
window.emptyState = emptyState;
window.emptyBookmarksHTML = emptyBookmarksHTML;
window.toggleBookmark = toggleBookmark;
window.shareArticle = shareArticle;
window.showToast = showToast;
