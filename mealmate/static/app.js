const toggle = document.querySelector('.nav-toggle');
const links = document.querySelector('.nav-links');
if (toggle) toggle.addEventListener('click', () => {
  const open = toggle.getAttribute('aria-expanded') === 'true';
  toggle.setAttribute('aria-expanded', String(!open));
  links.classList.toggle('open');
});
document.querySelectorAll('[data-confirm]').forEach(form => form.addEventListener('submit', event => {
  if (!window.confirm(form.dataset.confirm)) event.preventDefault();
}));
document.querySelectorAll('.alert-close').forEach(button => button.addEventListener('click', () => {
  button.closest('.alert').remove();
}));
document.querySelectorAll('.discovery-form, .search-bar').forEach(form => form.addEventListener('submit', () => {
  const button = form.querySelector('button[type="submit"]');
  if (!button) return;
  button.disabled = true;
  button.setAttribute('aria-busy', 'true');
  button.textContent = 'Loading…';
}));
document.querySelectorAll('[data-print-recipe]').forEach(button => {
  button.addEventListener('click', () => window.print());
});
document.querySelectorAll('[data-share-recipe]').forEach(button => {
  button.addEventListener('click', async () => {
    const fallback = button.parentElement.querySelector('[data-share-fallback]');
    if (navigator.share) {
      try {
        await navigator.share({ title: button.dataset.shareTitle, text: `${button.dataset.shareTitle} on Savorly`, url: button.dataset.shareUrl });
        return;
      } catch (error) {
        if (error.name === 'AbortError') return;
      }
    }
    fallback.hidden = !fallback.hidden;
    button.setAttribute('aria-expanded', String(!fallback.hidden));
  });
});
document.querySelectorAll('[data-copy-recipe-url]').forEach(button => {
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(button.dataset.copyRecipeUrl);
      button.textContent = 'Link copied';
    } catch (_error) {
      button.textContent = 'Copy unavailable';
    }
  });
});
