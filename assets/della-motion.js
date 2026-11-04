/* Della motion — GSAP 3.15.1. All content remains readable without JavaScript. */
(() => {
  'use strict';
  if (!window.gsap || !window.ScrollTrigger) return;
  const { gsap, ScrollTrigger } = window;
  gsap.registerPlugin(ScrollTrigger);
  const instances = new Map();

  function mount(scope) {
    if (instances.has(scope)) return;
    const mm = gsap.matchMedia();
    instances.set(scope, mm);
    try { mm.add({
      motion: '(prefers-reduced-motion: no-preference)',
      desktop: '(min-width: 990px) and (hover: hover) and (pointer: fine)'
    }, context => {
      if (!context.conditions.motion) return;
      const cleanup = [];
      const select = selector => [...scope.querySelectorAll(selector)];
      const reveal = (targets, trigger, options = {}) => {
        if (!targets.length) return;
        targets.forEach(target => { target.dataset.dellaMotion = 'reveal'; });
        gsap.fromTo(targets,
          { opacity: 0, y: 26 },
          { opacity: 1, y: 0, duration: 0.78, ease: 'power3.out', stagger: 0.075,
            clearProps: 'transform,opacity,visibility',
            scrollTrigger: { trigger, start: 'top 90%', once: true }, ...options }
        );
      };

      // A short editorial entrance; no loading screen or scroll lock.
      select('.della-hero-copy').forEach(copy => reveal([...copy.children], copy));
      select('.della-page-hero').forEach(heading => reveal([...heading.children], heading));
      select('.della-benefit-grid, .della-product-grid, .della-buying-paths, .della-wholesale').forEach(grid => {
        [...grid.children].forEach((card, index) => reveal([card], card, { delay: (index % 4) * 0.055 }));
      });
      select('.della-section-heading, .della-story-copy, .della-cta, .della-retail > div, .della-contact > div').forEach(section => {
        reveal([...section.children], section);
      });
      select('.della-collection-fan').forEach(fan => reveal([...fan.children], fan, { stagger: 0.13 }));
      select('.della-hero-seal').forEach(seal => {
        gsap.fromTo(seal, { scale: 0.7, rotation: -24, opacity: 0 }, {
          scale: 1, rotation: -8, opacity: 1, duration: 0.9, delay: 0.2,
          ease: 'back.out(1.2)', clearProps: 'opacity,scale',
          scrollTrigger: { trigger: seal, start: 'top 95%', once: true }
        });
      });

      if (context.conditions.desktop) {
        // Animate only the image, preserving link and card geometry.
        select('.della-product-image, .della-collection-fan a').forEach(card => {
          const image = card.querySelector('img');
          if (!image) return;
          const enter = () => gsap.to(image, { y: -10, rotation: -1.5, scale: 1.035, duration: 0.45, ease: 'power2.out', overwrite: 'auto' });
          const leave = () => gsap.to(image, { y: 0, rotation: 0, scale: 1, duration: 0.45, ease: 'power2.out', overwrite: 'auto', clearProps: 'transform' });
          card.addEventListener('pointerenter', enter);
          card.addEventListener('pointerleave', leave);
          card.addEventListener('focusin', enter);
          card.addEventListener('focusout', leave);
          cleanup.push(() => {
            card.removeEventListener('pointerenter', enter);
            card.removeEventListener('pointerleave', leave);
            card.removeEventListener('focusin', enter);
            card.removeEventListener('focusout', leave);
          });
        });
      }

      context.add('focusReveal', event => {
        const target = event.target.closest('[data-della-motion="reveal"]');
        if (target) {
          gsap.killTweensOf(target);
          gsap.set(target, { clearProps: 'transform,opacity,visibility' });
        }
      });
      scope.addEventListener('focusin', context.focusReveal);
      const refresh = () => ScrollTrigger.refresh();
      scope.addEventListener('load', refresh, true);
      return () => {
        cleanup.forEach(remove => remove());
        scope.removeEventListener('focusin', context.focusReveal);
        scope.removeEventListener('load', refresh, true);
        select('[data-della-motion]').forEach(target => { delete target.dataset.dellaMotion; });
      };
    }, scope); } catch (error) {
      // Failure must restore readable, interactive content rather than leave faded sections.
      mm.revert();
      instances.delete(scope);
      if (window.Shopify?.designMode) console.warn('Della motion was disabled for this section.', error);
    }
  }

  function unmount(scope) {
    const mm = instances.get(scope);
    if (mm) { mm.revert(); instances.delete(scope); }
  }
  function start() {
    // A section owns its animations, so Shopify editor reloads can cleanly revert them.
    document.querySelectorAll('.shopify-section').forEach(mount);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
  document.addEventListener('shopify:section:unload', event => unmount(event.target));
  document.addEventListener('shopify:section:load', event => mount(event.target));
  window.addEventListener('pagehide', () => [...instances.keys()].forEach(unmount));
  window.addEventListener('pageshow', event => { if (event.persisted) start(); });
})();
