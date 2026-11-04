(() => {
  function init(root = document) {
    root.querySelectorAll('[data-della-slideshow]').forEach(slideshow => {
      if (slideshow.dataset.initialized) return;
      slideshow.dataset.initialized = 'true';
      const buttons = [...slideshow.querySelectorAll('[data-della-slide]')];
      const panels = [...slideshow.querySelectorAll('[data-slide-panel]')];
      buttons.forEach(button => button.addEventListener('click', () => {
        if (button.getAttribute('aria-pressed') === 'true') return;
        buttons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
        panels.forEach(panel => { panel.hidden = panel.dataset.slidePanel !== button.dataset.dellaSlide; });
        const panel = panels.find(item => item.dataset.slidePanel === button.dataset.dellaSlide);
        slideshow.dispatchEvent(new CustomEvent('della:slide-change', { bubbles: true, detail: { panel } }));
      }));
    });
  }
  document.addEventListener('DOMContentLoaded', () => init());
  document.addEventListener('shopify:section:load', event => init(event.target));
  document.addEventListener('shopify:block:select', event => {
    const panel = event.target.closest('[data-slide-panel]');
    const slideshow = panel?.closest('[data-della-slideshow]');
    const button = slideshow?.querySelector(`[data-della-slide="${panel.dataset.slidePanel}"]`);
    if (button) button.click();
  });
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
