const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
const directory = document.querySelector('#site-directory');
const hiddenClass = 'sidebar-hidden';
const searchInput = document.querySelector('[data-search-input]');
const searchResults = document.querySelector('[data-search-results]');
const themeToggle = document.querySelector('[data-theme-toggle]');
const subscribeForm = document.querySelector('[data-subscribe-form]');
const subscribeStatus = document.querySelector('[data-subscribe-status]');
const siteScript = document.currentScript || document.querySelector('script[src$="site.js"]');
const siteRoot = siteScript ? new URL('..', siteScript.src) : new URL('/', window.location.href);
let searchIndex = [];
let swipeStartX = 0;
let swipeStartY = 0;
let swipeStartTime = 0;

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('theme', theme);
  if (themeToggle) {
    themeToggle.checked = theme === 'dark';
  }
}

function preferredTheme() {
  const saved = localStorage.getItem('theme');
  if (saved === 'light' || saved === 'dark') return saved;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

setTheme(preferredTheme());

themeToggle?.addEventListener('change', () => {
  setTheme(themeToggle.checked ? 'dark' : 'light');
});

subscribeForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const emailInput = subscribeForm.querySelector('input[type="email"]');
  const submitButton = subscribeForm.querySelector('button[type="submit"]');
  const email = emailInput?.value.trim();

  if (!email || !subscribeForm.checkValidity()) {
    subscribeForm.reportValidity();
    return;
  }

  if (subscribeStatus) {
    subscribeStatus.hidden = false;
    subscribeStatus.textContent = 'Subscribing...';
    subscribeStatus.dataset.state = 'pending';
  }
  if (submitButton) submitButton.disabled = true;

  try {
    await fetch(subscribeForm.action, {
      method: 'POST',
      body: new FormData(subscribeForm),
      mode: 'no-cors',
    });

    subscribeForm.reset();
    if (subscribeStatus) {
      subscribeStatus.textContent = 'Subscribed. Your email was saved.';
      subscribeStatus.dataset.state = 'success';
    }
  } catch (error) {
    if (subscribeStatus) {
      const fallback = subscribeForm.dataset.fallbackUrl || subscribeForm.action;
      subscribeStatus.innerHTML = `Could not save that here. <a href="${fallback}">Open the Google form</a>.`;
      subscribeStatus.dataset.state = 'error';
    }
  } finally {
    if (submitButton) submitButton.disabled = false;
  }
});

function setSidebarHidden(hidden) {
  document.body.classList.toggle(hiddenClass, hidden);
  if (directory) {
    directory.setAttribute('aria-hidden', hidden ? 'true' : 'false');
  }
  if (sidebarToggle) {
    sidebarToggle.setAttribute('aria-expanded', hidden ? 'false' : 'true');
    sidebarToggle.querySelector('span:last-child').textContent = hidden ? 'Show directory' : 'Directory';
  }
  localStorage.setItem('sidebar-hidden', hidden ? 'true' : 'false');
}

if (localStorage.getItem('sidebar-hidden') === 'true') {
  setSidebarHidden(true);
}

sidebarToggle?.addEventListener('click', () => {
  setSidebarHidden(!document.body.classList.contains(hiddenClass));
});

document.querySelectorAll('.directory-section').forEach((section) => {
  section.addEventListener('toggle', () => {
    const key = `directory-section:${section.querySelector('summary')?.textContent || ''}`;
    localStorage.setItem(key, section.open ? 'open' : 'closed');
  });

  const key = `directory-section:${section.querySelector('summary')?.textContent || ''}`;
  const saved = localStorage.getItem(key);
  if (saved === 'open') section.open = true;
  if (saved === 'closed' && !section.querySelector('[aria-current="page"]')) section.open = false;
});

async function loadSearchIndex() {
  if (searchIndex.length) return searchIndex;
  const searchUrl = new URL('search.json', siteRoot);
  searchUrl.searchParams.set('v', siteScript ? new URL(siteScript.src).searchParams.get('v') || Date.now() : Date.now());
  const response = await fetch(searchUrl, { cache: 'no-store' });
  searchIndex = await response.json();
  return searchIndex;
}

function siteHref(path) {
  return new URL(path.replace(/^\//, ''), siteRoot).pathname;
}

function scorePage(page, query) {
  const title = page.title.toLowerCase();
  const description = page.description.toLowerCase();
  const text = page.text.toLowerCase();
  const haystack = `${title} ${description} ${text}`;
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.every((term) => haystack.includes(term))) return 0;

  return terms.reduce((score, term) => {
    if (title.includes(term)) return score + 8;
    if (description.includes(term)) return score + 5;
    const matches = text.match(new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'));
    return score + Math.min(matches?.length || 1, 4);
  }, 0);
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[char]);
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function highlightTerms(value, terms) {
  const escaped = escapeHtml(value);
  const uniqueTerms = [...new Set(terms.filter(Boolean))].sort((a, b) => b.length - a.length);
  if (!uniqueTerms.length) return escaped;

  const pattern = new RegExp(`(${uniqueTerms.map(escapeRegExp).join('|')})`, 'gi');
  return escaped.replace(pattern, '<mark>$1</mark>');
}

function searchSnippet(page, query) {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const lines = page.lines || [];
  const exactLines = lines.filter((line) => {
    const lower = line.toLowerCase();
    return terms.some((term) => lower.includes(term));
  });
  const snippet = exactLines.slice(0, 2).join(' / ') || page.description || page.excerpt || page.url;
  return highlightTerms(snippet, terms);
}

function renderSearchResults(results) {
  if (!searchResults) return;

  if (!results.length) {
    searchResults.innerHTML = '<p class="search-empty">no results</p>';
    searchResults.hidden = false;
    return;
  }

  searchResults.innerHTML = results
    .slice(0, 8)
    .map((page) => `
      <a class="search-result" href="${siteHref(page.url)}">
        <span>${escapeHtml(page.title)}</span>
        <small>${searchSnippet(page, searchInput.value.trim())}</small>
      </a>
    `)
    .join('');
  searchResults.hidden = false;
}

searchInput?.addEventListener('input', async () => {
  const query = searchInput.value.trim();
  if (!query) {
    if (searchResults) searchResults.hidden = true;
    return;
  }

  const pages = await loadSearchIndex();
  const results = pages
    .map((page) => ({ ...page, score: scorePage(page, query) }))
    .filter((page) => page.score > 0)
    .sort((a, b) => b.score - a.score || a.title.localeCompare(b.title));
  renderSearchResults(results);
});

document.addEventListener('keydown', (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    searchInput?.focus();
  }

  if (event.key === 'Escape' && searchResults) {
    searchResults.hidden = true;
    searchInput?.blur();
  }
});

document.addEventListener('click', (event) => {
  if (!event.target.closest('.site-search') && searchResults) {
    searchResults.hidden = true;
  }
});

function canStartSwipe(event) {
  if (event.touches.length !== 1) return false;
  const target = event.target;
  if (!(target instanceof Element)) return false;
  return !target.closest('a, button, input, textarea, select, label, summary, .search-results');
}

document.addEventListener('touchstart', (event) => {
  if (!canStartSwipe(event)) return;

  const touch = event.touches[0];
  swipeStartX = touch.clientX;
  swipeStartY = touch.clientY;
  swipeStartTime = Date.now();
}, { passive: true });

document.addEventListener('touchend', (event) => {
  if (!swipeStartTime || event.changedTouches.length !== 1) return;

  const touch = event.changedTouches[0];
  const deltaX = touch.clientX - swipeStartX;
  const deltaY = touch.clientY - swipeStartY;
  const elapsed = Date.now() - swipeStartTime;
  swipeStartTime = 0;

  const isHorizontal = Math.abs(deltaX) > 72 && Math.abs(deltaX) > Math.abs(deltaY) * 1.6;
  if (!isHorizontal || elapsed > 900) return;

  const targetUrl = deltaX < 0 ? document.body.dataset.swipeNext : document.body.dataset.swipePrevious;
  if (targetUrl) {
    window.location.href = targetUrl;
  }
}, { passive: true });
