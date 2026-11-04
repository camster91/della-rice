(() => {
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
