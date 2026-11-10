(() => {
  const root = () => window.Shopify?.routes?.root || '/';
  let latestCountRequest = 0;
  function updateCount(cart) {
    if (!Number.isInteger(cart?.item_count)) return;
    const bag = document.querySelector('a.della-bag');
    if (!bag) return;
    const label = bag.querySelector('[data-della-cart-count]') || bag.querySelector(':scope > span:last-child');
    if (label) label.textContent = `Bag (${cart.item_count})`;
    bag.setAttribute('aria-label', `Bag, ${cart.item_count} items`);
  }
  async function refreshCount() {
    const request = ++latestCountRequest;
    try {
      const response = await fetch(`${root()}cart.js`, { headers: { Accept: 'application/json' } });
      if (!response.ok) return;
      const cart = await response.json();
      if (request === latestCountRequest) updateCount(cart);
    } catch (_) { /* The saved addition remains confirmed; the bag link still works. */ }
  }
  if (typeof subscribe === 'function' && typeof PUB_SUB_EVENTS !== 'undefined') {
    subscribe(PUB_SUB_EVENTS.cartUpdate, () => refreshCount());
  }

  if (!customElements.get('della-quick-buy')) {
    customElements.define('della-quick-buy', class extends HTMLElement {
      connectedCallback() {
        if (this.initialized) return;
        this.initialized = true;
        this.form = this.querySelector('form');
        this.button = this.querySelector('button[type="submit"]');
        this.status = this.querySelector('[data-quick-buy-status]');
        if (!this.form || !this.button || !this.status) return;
        this.form.addEventListener('submit', event => this.hasAttribute('data-native') ? this.nativeAdd(event) : this.add(event));
      }
      message(text, error = false) {
        this.status.replaceChildren();
        this.status.setAttribute('role', error ? 'alert' : 'status');
        this.status.setAttribute('aria-live', error ? 'assertive' : 'polite');
        this.status.append(document.createTextNode(`${text} `));
        const link = document.createElement('a');
        link.href = `${root()}cart`;
        link.textContent = 'View bag →';
        this.status.append(link);
      }
      async nativeAdd(event) {
        const items = document.querySelector('cart-items');
        items?.debouncedOnChange?.flush();
        if (typeof CartItems === 'undefined' || !CartItems.pendingQuantitySaves?.size) return;
        event.preventDefault();
        if (this.pending) return;
        this.pending = true;
        this.button.disabled = true;
        const failures = CartItems.failedQuantitySaves;
        let canProceed = true;
        try {
          while (CartItems.pendingQuantitySaves.size) {
            await Promise.all(CartItems.pendingQuantitySaves);
            items?.debouncedOnChange?.flush();
          }
        } catch (_) {
          canProceed = false;
        } finally {
          this.pending = false;
          this.button.disabled = false;
        }
        if (!canProceed || failures !== CartItems.failedQuantitySaves) {
          this.message('Check the quantity error in your bag before adding another item.', true);
          return;
        }
        this.form.requestSubmit(this.button);
      }
      async add(event) {
        event.preventDefault();
        if (this.pending) return;
        this.pending = true;
        const originalLabel = this.button.textContent;
        this.button.disabled = true;
        this.button.textContent = 'Adding…';
        this.form.setAttribute('aria-busy', 'true');
        this.status.replaceChildren();
        const data = new FormData(this.form);
        const quantity = Number(data.get('quantity')) || 1;
        try {
          const response = await fetch(`${root()}cart/add.js`, {
            method: 'POST', body: data, headers: { Accept: 'application/json' }
          });
          const result = await response.json();
          if (!response.ok || result.status) {
            this.message(typeof result.description === 'string' ? result.description : 'This item could not be added.', true);
            return;
          }
          this.message(`Added ${quantity} to your bag.`);
          await refreshCount();
        } catch (_) {
          this.message('We couldn’t confirm this update. Check your bag before trying again.', true);
        } finally {
          this.pending = false;
          this.button.disabled = false;
          this.button.textContent = originalLabel;
          this.form.removeAttribute('aria-busy');
        }
      }
    });
  }

  if (!customElements.get('della-cart-presets')) {
    customElements.define('della-cart-presets', class extends HTMLElement {
      connectedCallback() {
        this.hidden = false;
        if (this.initialized) return;
        this.initialized = true;
        this.addEventListener('click', event => {
          const button = event.target.closest('button[data-cart-quantity]');
          const input = this.closest('tr')?.querySelector('input[name="updates[]"]');
          if (!button || !input || button.disabled) return;
          const quantity = button.dataset.cartQuantity;
          if (input.value === quantity) return;
          input.value = quantity;
          input.dispatchEvent(new Event('change', { bubbles: true }));
        });
      }
    });
  }
})();
