# Della motion and visual polish

GSAP 3.15.1 and ScrollTrigger are bundled as local Shopify assets. Their copyright/licence headers are preserved; licence: https://gsap.com/standard-license.

- Short, staggered hero and page-heading entrances.
- Scroll reveals for product cards, benefits, stories and buying paths.
- Gentle product-image lift/tilt on pointer hover and keyboard focus on suitable desktop devices.
- Image transitions on the existing manual hero controls.
- Packaging-inspired decorative rice seal, button highlights and restrained navigation details.

Motion can be switched off in Theme settings → Della motion. Reduced-motion preferences bypass the GSAP effects. No scroll hijacking, autoplay carousel, loading screen or continuous animation is introduced. Plain content and links remain present without JavaScript. Keyboard focus reveals an animated element immediately. Shopify section reloads and media-query changes revert effects and remove listeners.

Validation: JavaScript syntax and Shopify Theme Check passed locally. Browser/animation verification is pending restoration of the browser connection; this change must be reviewed before merging to the connected theme branch.

Official implementation references:

- https://gsap.com/docs/v3/GSAP/gsap.matchMedia()/
- https://gsap.com/docs/v3/Plugins/ScrollTrigger/
