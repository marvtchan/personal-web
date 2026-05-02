const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
const directory = document.querySelector('#site-directory');
const hiddenClass = 'sidebar-hidden';

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
