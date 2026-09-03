// Samachar Core Application Utilities & Components

function sanitize(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function timeAgo(dateString) {
  if (!dateString) return 'Just now';
  let dateStr = dateString;
  if (typeof dateStr === 'string' && !dateStr.endsWith('Z') && !dateStr.includes('+') && !dateStr.includes('GMT')) {
    dateStr += 'Z';
  }
  const now = new Date();
  const past = new Date(dateStr);
  const diffSec = Math.floor((now - past) / 1000);

  if (isNaN(diffSec) || diffSec <= 60) return 'Just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  const days = Math.floor(diffSec / 86400);
  return days === 1 ? 'Yesterday' : `${days}d ago`;
}

function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast';
  if (type === 'success') toast.style.borderLeft = '4px solid var(--accent)';
  if (type === 'error') toast.style.borderLeft = '4px solid var(--disputed)';
  toast.textContent = message;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

const CATEGORY_PHOTOS = {
  'technology': 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80',
  'tech': 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80',
  'world': 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=800&q=80',
  'india': 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80',
  'business': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80',
  'science': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80',
  'health': 'https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?auto=format&fit=crop&w=800&q=80',
  'sports': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=800&q=80',
  'entertainment': 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=800&q=80',
};

function getCategoryDefaultImage(catName) {
  const slug = (catName || '').toLowerCase().trim();
  return CATEGORY_PHOTOS[slug] || 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80';
}
window.getCategoryDefaultImage = getCategoryDefaultImage;

function getCategoryBadgeClass(catName) {
  const slug = (catName || '').toLowerCase().trim();
  if (slug.includes('tech')) return 'badge-chan-tech';
  if (slug.includes('world')) return 'badge-chan-world';
  if (slug.includes('india')) return 'badge-chan-india';
  if (slug.includes('business') || slug.includes('market')) return 'badge-chan-markets';
  if (slug.includes('science')) return 'badge-chan-science';
  if (slug.includes('health')) return 'badge-chan-health';
  if (slug.includes('sport')) return 'badge-chan-sports';
  return 'badge-verified';
}

// News Card Builder with precise alignment
function renderNewsCard(article) {
  const safeTitle = sanitize(article.title);
  const safeSummary = sanitize(article.summary || '');
  const safeSource = sanitize(article.source?.name || article.source_name || 'News Wire');
  const safeCat = sanitize(article.category?.name || article.category_name || 'Top News');
  const timeStr = timeAgo(article.published_at);
  const credScore = article.credibility_score || 88;
  const status = article.fact_check_status || 'verified';
  const imgUrl = article.image_url || getCategoryDefaultImage(safeCat);
  const catBadgeClass = getCategoryBadgeClass(safeCat);
  const wordCount = (article.content || article.summary || '').split(/\s+/).length;
  const readMins = Math.max(1, Math.ceil(wordCount / 180));

  let badgeClass = 'badge-verified';
  let badgeLabel = `🟢 ${credScore}% VERIFIED`;

  if (status === 'corroborated' || (credScore >= 75 && credScore < 85)) {
    badgeClass = 'badge-corroborated';
    badgeLabel = `🔵 ${credScore}% CORROBORATED`;
  } else if (status === 'developing' || (credScore >= 55 && credScore < 75)) {
    badgeClass = 'badge-developing';
    badgeLabel = `🟡 ${credScore}% DEVELOPING`;
  } else if (status === 'disputed' || credScore < 55) {
    badgeClass = 'badge-disputed';
    badgeLabel = `🔴 ${credScore}% UNVERIFIED`;
  }

  return `
    <article class="card animate-fade-in-up" id="article-${article.id}">
      <div class="card-img-wrapper">
        <img src="${imgUrl}" alt="${safeTitle}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80'" />
        <div style="position:absolute;top:10px;left:10px;display:flex;gap:6px">
          <span class="badge ${badgeClass}">${badgeLabel}</span>
        </div>
      </div>
      <div class="card-body">
        <div class="flex items-center justify-between text-xs text-muted mb-2">
          <span class="badge ${catBadgeClass}" style="font-size:10px;padding:2px 6px;">${safeCat}</span>
          <span class="flex items-center gap-1"><span>⏱️ ${readMins}m read</span> · <span>${timeStr}</span></span>
        </div>
        <h3 class="heading-sm mb-2 line-clamp-2">
          <a href="article.html?id=${article.id}" style="color:var(--text-primary)">${safeTitle}</a>
        </h3>
        <p class="text-xs text-secondary line-clamp-3">${safeSummary}</p>
      </div>
      <div class="card-footer">
        <span class="text-xs text-muted font-medium">${safeSource}</span>
        <div class="flex items-center gap-2">
          <button onclick="handleSaveBookmark(${article.id}, this)" class="btn btn-ghost btn-sm btn-icon bookmark-trigger-btn" title="Save Bookmark" style="border-radius:50%;transition:transform 0.2s var(--ease-spring);">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>
          </button>
          <a href="article.html?id=${article.id}" class="btn btn-secondary btn-sm" style="font-weight:600;">Read &rarr;</a>
        </div>
      </div>
    </article>
  `;
}

async function handleSaveBookmark(articleId, btnEl) {
  let user = null;
  try {
    if (typeof getUser === 'function') user = getUser();
    else {
      const raw = localStorage.getItem('samachar_user');
      user = raw ? JSON.parse(raw) : null;
    }
  } catch (_) {}

  if (!user && !localStorage.getItem('samachar_token')) {
    showToast('Please sign in to save bookmarks', 'error');
    setTimeout(() => { window.location.href = 'login.html'; }, 600);
    return;
  }

  if (btnEl) {
    btnEl.style.transform = 'scale(1.35)';
    btnEl.style.color = 'var(--accent)';
    setTimeout(() => { btnEl.style.transform = 'scale(1)'; }, 250);
  }

  try {
    if (typeof saveBookmark === 'function') {
      await saveBookmark(articleId);
    } else {
      let bms = JSON.parse(localStorage.getItem('samachar_local_bookmarks') || '[]');
      if (!bms.includes(articleId)) {
        bms.push(articleId);
        localStorage.setItem('samachar_local_bookmarks', JSON.stringify(bms));
      }
    }
    showToast('📌 Article saved to your research bookmarks!', 'success');
  } catch (err) {
    showToast(err.message || 'Bookmark updated.', 'info');
  }
}
