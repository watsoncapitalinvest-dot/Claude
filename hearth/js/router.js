// router.js — tiny hash router
const routes = {};
let notFound = null;
let current = null;

export function route(path, handler) { routes[path] = handler; }
export function setNotFound(fn) { notFound = fn; }
export function currentPath() { return (location.hash.replace(/^#/, '') || '/dashboard'); }

export function navigate(path) {
  if ('#' + path === location.hash) { render(); return; }
  location.hash = path;
}

export function render() {
  const path = currentPath();
  current = path;
  // exact match, else first segment match
  const handler = routes[path] || routes['/' + path.split('/')[1]] || notFound;
  const outlet = document.getElementById('view-outlet');
  if (!outlet) return;
  outlet.innerHTML = '';
  const node = handler ? handler(path) : null;
  if (node) outlet.append(node);
  outlet.scrollTop = 0;
  window.scrollTo(0, 0);
  document.dispatchEvent(new CustomEvent('route:changed', { detail: { path } }));
}

export function startRouter() {
  window.addEventListener('hashchange', render);
  if (!location.hash) location.hash = '/dashboard';
}
