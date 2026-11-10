(() => {
  const root = document.querySelector('[data-della-recipe]');
  if (!root || root.dataset.organized) return;
  const nodes = Array.from(root.childNodes);
  const label = node => node.textContent.trim();
  const heading = node => /^H[2-6]$/.test(node.tagName);
  const ingredients = nodes.findIndex(node => (heading(node) && /^(?:ingredients|ngredients)\b/i.test(label(node))) || (node.nodeType === 1 && node.tagName === 'P' && /^(?:ingredients|ngredients)$/i.test(label(node))));
  const method = nodes.findIndex((node, index) => index > ingredients && heading(node) && /^(step|phase)\s*1\b/i.test(label(node)));
  // Leave unfamiliar article structures intact rather than guessing their sections.
  if (ingredients < 0 || method < 0) return;
  root.dataset.organized = 'true';
  const intro = document.createElement('div'); intro.className = 'della-recipe-intro';
  const gallery = document.createElement('div'); gallery.className = 'della-recipe-gallery'; gallery.setAttribute('aria-label', 'Recipe photos');
  const layout = document.createElement('div'); layout.className = 'della-recipe-layout';
  const ingredientSection = document.createElement('section'); ingredientSection.className = 'della-recipe-ingredients'; ingredientSection.id = 'recipe-ingredients';
  ingredientSection.setAttribute('aria-labelledby', 'recipe-ingredients-heading');
  const directions = document.createElement('section'); directions.className = 'della-recipe-directions'; directions.id = 'recipe-directions';
  directions.setAttribute('aria-labelledby', 'recipe-directions-heading');
  const directionsHeading = document.createElement('h2'); directionsHeading.id = 'recipe-directions-heading'; directionsHeading.textContent = 'Directions'; directions.append(directionsHeading);
  const ingredientsHeading = document.createElement('h2'); ingredientsHeading.id = 'recipe-ingredients-heading'; ingredientsHeading.textContent = 'Ingredients'; ingredientSection.append(ingredientsHeading);
  const nav = document.createElement('nav'); nav.className = 'della-recipe-jumps'; nav.setAttribute('aria-label', 'On this recipe');
  [['Ingredients', '#recipe-ingredients'], ['Directions', '#recipe-directions']].forEach(([text, href]) => {const a = document.createElement('a'); a.textContent = text; a.href = href; nav.append(a);});
  let currentStep = null;
  nodes.forEach((node, index) => {
    if (node.nodeType === 1 && node.matches('figure') && node.querySelector('img')) gallery.append(node);
    else if (index < ingredients) intro.append(node);
    else if (index === ingredients) {
      if (/^(?:ingredients|ngredients)$/i.test(label(node))) node.remove();
      else ingredientSection.append(node);
    }
    else if (index < method) ingredientSection.append(node);
    else {
      if (heading(node) && /^(step|phase)\s*\d+\b/i.test(label(node))) {
        currentStep = document.createElement('div'); currentStep.className = 'della-recipe-step';
        const h = document.createElement('h3'); h.textContent = label(node); currentStep.append(h); directions.append(currentStep); node.remove();
      } else (currentStep || directions).append(node);
    }
  });
  layout.append(ingredientSection, directions);
  root.append(nav, intro);
  if (gallery.childElementCount) root.append(gallery);
  root.append(layout);
})();
