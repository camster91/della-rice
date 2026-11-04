(() => {
  function init(root = document) {
    root.querySelectorAll('[data-della-slideshow]').forEach(slideshow => {
      if (slideshow.dataset.initialized) return;
      slideshow.dataset.initialized = 'true';
      const buttons = [...slideshow.querySelectorAll('[data-della-slide]')];
      const panels = [...slideshow.querySelectorAll('[data-slide-panel]')];
      buttons.forEach(button => button.addEventListener('click', () => {
        buttons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
        panels.forEach(panel => { panel.hidden = panel.dataset.slidePanel !== button.dataset.dellaSlide; });
      }));
    });
  }
  document.addEventListener('DOMContentLoaded', () => init());
  document.addEventListener('shopify:section:load', event => init(event.target));
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    document.querySelectorAll('.della-header details[open]').forEach(details => {
      details.open = false;
      details.querySelector('summary').focus();
    });
  });
  document.addEventListener('click', event => {
    document.querySelectorAll('.della-dropdown[open]').forEach(details => {
      if (!details.contains(event.target)) details.open = false;
    });
  });
})();
