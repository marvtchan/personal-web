const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
const directory = document.querySelector('#site-directory');
const hiddenClass = 'sidebar-hidden';
const searchInput = document.querySelector('[data-search-input]');
const searchResults = document.querySelector('[data-search-results]');
const siteScript = document.currentScript || document.querySelector('script[src$="site.js"]');
const siteRoot = siteScript ? new URL('..', siteScript.src) : new URL('/', window.location.href);
let searchIndex = [];

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
  const response = await fetch(new URL('search.json', siteRoot));
  searchIndex = await response.json();
  return searchIndex;
}

function siteHref(path) {
  return new URL(path.replace(/^\//, ''), siteRoot).pathname;
}

function scorePage(page, query) {
  const haystack = `${page.title} ${page.description} ${page.text}`.toLowerCase();
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.every((term) => haystack.includes(term))) return 0;

  return terms.reduce((score, term) => {
    if (page.title.toLowerCase().includes(term)) return score + 5;
    if (page.description.toLowerCase().includes(term)) return score + 3;
    return score + 1;
  }, 0);
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
        <span>${page.title}</span>
        <small>${page.description || page.text || page.url}</small>
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
