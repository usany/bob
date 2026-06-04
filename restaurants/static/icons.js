/**
 * Lucide-style icons without a bundle. Add SVG markup keyed by data-lucide name.
 */
(function () {
  const icons = {
    building:
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 21V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5m-4 0h4"/></svg>',
  };

  function initIcons(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-lucide]').forEach((el) => {
      const name = el.getAttribute('data-lucide');
      const markup = icons[name];
      if (!markup) return;

      const wrap = document.createElement('div');
      wrap.innerHTML = markup.trim();
      const svg = wrap.firstElementChild;
      if (!svg) return;

      if (el.className) svg.setAttribute('class', el.className);
      el.replaceWith(svg);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initIcons());
  } else {
    initIcons();
  }

  window.initLucideIcons = initIcons;
})();
