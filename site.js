(function () {
  const body = document.body;

  function lockScroll(on) {
    body.classList.toggle('is-locked', on);
  }

  function openOverlay(id) {
    const el = document.getElementById(id);
    if (!el) return;
    document.querySelectorAll('.overlay.is-open').forEach(o => {
      if (o !== el) closeOverlay(o);
    });
    el.classList.add('is-open');
    lockScroll(true);
    const focusable = el.querySelector('button, a, input');
    if (focusable) focusable.focus();
  }

  function closeOverlay(el) {
    if (!el) return;
    el.classList.remove('is-open');
    if (!document.querySelector('.overlay.is-open')) lockScroll(false);
  }

  document.querySelectorAll('[data-open]').forEach(trigger => {
    trigger.addEventListener('click', e => {
      e.preventDefault();
      openOverlay(trigger.dataset.open);
    });
  });

  document.querySelectorAll('[data-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      const overlay = btn.closest('.overlay');
      closeOverlay(overlay);
    });
  });

  document.querySelectorAll('.overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) closeOverlay(overlay);
    });
  });

  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    document.querySelectorAll('.overlay.is-open').forEach(closeOverlay);
  });

  /* Mouthwash copy */
  const toast = document.getElementById('toast');
  document.querySelectorAll('[data-copy]').forEach(el => {
    el.addEventListener('click', async e => {
      e.preventDefault();
      const text = el.dataset.copy;
      try {
        await navigator.clipboard.writeText(text);
        if (toast) {
          toast.textContent = 'Copied';
          toast.classList.add('is-visible');
          setTimeout(() => toast.classList.remove('is-visible'), 1600);
        }
      } catch {
        window.location.href = `mailto:${text}`;
      }
    });
  });

  /* Contact form */
  const contactForm = document.getElementById('contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', e => {
      e.preventDefault();
      const email = contactForm.querySelector('input[type="email"]');
      if (email && email.value) {
        window.location.href = `mailto:arkhipoovau@gmail.com?subject=Hello&body=From: ${encodeURIComponent(email.value)}`;
      }
      closeOverlay(contactForm.closest('.overlay'));
    });
  }

  document.querySelectorAll('[data-close-menu]').forEach(btn => {
    btn.addEventListener('click', () => {
      const overlay = btn.closest('.overlay');
      if (overlay) closeOverlay(overlay);
      if (btn.dataset.open) setTimeout(() => openOverlay(btn.dataset.open), 0);
      if (btn.dataset.goto && window.scrollToZone) window.scrollToZone(btn.dataset.goto);
    });
  });

  window.siteUI = { openOverlay, closeOverlay };

  /* Shared corner nav — one config for all pages */
  function getNavBase() {
    const src = document.querySelector('script[src*="site.js"]')?.getAttribute('src') || 'site.js';
    return src.startsWith('../') ? '../' : '';
  }

  function renderCornerNav() {
    const page = document.body.dataset.page;
    if (!page) return;

    const base = getNavBase();
    const home = base || './';

    const sections = [
      { id: 'work', label: 'Work', href: home },
      { id: 'index', label: 'Index', href: `${base}index/` },
      { id: 'research', label: 'Research', href: `${base}research/` },
      { id: 'playground', label: 'Playground', href: `${base}playground/` },
      { id: 'about', label: 'About', href: `${base}about/` },
      { id: 'cv', label: 'CV', href: `${base}cv/` },
    ];

    const neLinks = sections.map(s => {
      if (s.id === page) return `<span class="corner-nav__link corner-nav__link--active type-menu plain">${s.label}</span>`;
      return `<a href="${s.href}" class="corner-nav__link type-menu">${s.label}</a>`;
    }).join('');

    const tagline = page === 'about'
      ? `<span class="tagline type-serif plain">This is a celebration, not a tournament</span>`
      : `<a href="${base}about/" class="tagline type-serif">This is a celebration, not a tournament</a>`;

    const root = document.createElement('div');
    root.innerHTML = `
      <nav class="corner corner-nw" aria-label="Identity">
        <a href="${home}" class="corner-nav__brand type-menu">Julie Arkhipova</a>
        <a href="https://www.instagram.com/arkhipovau/" class="corner-nav__link type-menu" target="_blank" rel="noopener noreferrer">Instagram</a>
        <a href="https://www.linkedin.com/in/arkhipovau/" class="corner-nav__link type-menu" target="_blank" rel="noopener noreferrer">LinkedIn</a>
        <a href="https://www.behance.net/arkhipovau/" class="corner-nav__link type-menu" target="_blank" rel="noopener noreferrer">Behance</a>
      </nav>
      <nav class="corner corner-ne" aria-label="Sections">
        ${neLinks}
      </nav>
      <div class="corner corner-sw">
        <button type="button" class="corner-link type-menu" data-copy="arkhipoovau@gmail.com">arkhipoovau@gmail.com</button>
      </div>
      <div class="corner corner-se">
        ${tagline}
      </div>
    `;

    while (root.firstChild) body.insertBefore(root.firstChild, body.firstChild);

    document.querySelectorAll('[data-copy]').forEach(el => {
      if (el.dataset.copyBound) return;
      el.dataset.copyBound = '1';
      el.addEventListener('click', async e => {
        e.preventDefault();
        const text = el.dataset.copy;
        try {
          await navigator.clipboard.writeText(text);
          if (toast) {
            toast.textContent = 'Copied';
            toast.classList.add('is-visible');
            setTimeout(() => toast.classList.remove('is-visible'), 1600);
          }
        } catch {
          window.location.href = `mailto:${text}`;
        }
      });
    });
  }

  renderCornerNav();

  requestAnimationFrame(() => {
    document.body.classList.add('is-page-ready');
  });
})();
