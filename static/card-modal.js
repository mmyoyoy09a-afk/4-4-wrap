(function () {
  let modal, cardEl;
  let currentPages = [];
  let currentIndex = 0;
  let currentTo = '';
  let currentFrom = '';
  let currentColor = '#ffffff';

  function ensureModal() {
    if (modal) return;
    modal = document.createElement('div');
    modal.className = 'card-modal-overlay';
    modal.innerHTML =
      '<div class="card-modal-inner">' +
        '<button type="button" class="card-modal-close" aria-label="Close">&times;</button>' +
        '<div class="card-preview card-modal-card">' +
          '<div class="card-page-indicator"></div>' +
          '<div class="card-to"><span>To:</span> <span class="card-modal-to-text"></span></div>' +
          '<div class="card-message card-modal-msg"></div>' +
          '<div class="card-from"><span>From:</span> <span class="card-modal-from-text"></span></div>' +
        '</div>' +
        '<div class="card-modal-nav">' +
          '<button type="button" class="btn small card-modal-prev">&larr; Prev</button>' +
          '<button type="button" class="btn small card-modal-next">Next &rarr;</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(modal);
    cardEl = modal.querySelector('.card-modal-card');
    modal.querySelector('.card-modal-close').addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
    modal.querySelector('.card-modal-prev').addEventListener('click', () => go(-1));
    modal.querySelector('.card-modal-next').addEventListener('click', () => go(1));
    document.addEventListener('keydown', (e) => {
      if (!modal.classList.contains('open')) return;
      if (e.key === 'Escape') closeModal();
      if (e.key === 'ArrowLeft') go(-1);
      if (e.key === 'ArrowRight') go(1);
    });
  }

  function render() {
    cardEl.style.background = currentColor;
    modal.querySelector('.card-page-indicator').textContent = `(${currentIndex + 1}/${currentPages.length})`;

    const toWrap = modal.querySelector('.card-to');
    toWrap.style.display = currentIndex === 0 ? '' : 'none';
    modal.querySelector('.card-modal-to-text').textContent = currentTo || '';

    const msgEl = modal.querySelector('.card-modal-msg');
    msgEl.textContent = currentPages[currentIndex] || '';
    msgEl.classList.toggle('no-to', currentIndex !== 0);

    const isLast = currentIndex === currentPages.length - 1;
    const fromWrap = modal.querySelector('.card-from');
    fromWrap.style.display = (isLast && currentFrom) ? '' : 'none';
    modal.querySelector('.card-modal-from-text').textContent = currentFrom || '';

    modal.querySelector('.card-modal-prev').disabled = currentIndex === 0;
    modal.querySelector('.card-modal-next').disabled = currentIndex === currentPages.length - 1;
  }

  function go(delta) {
    const next = currentIndex + delta;
    if (next < 0 || next >= currentPages.length) return;
    currentIndex = next;
    render();
  }

  function closeModal() {
    modal.classList.remove('open');
  }

  window.openCardModal = function (toName, fromName, colorHex, pages) {
    ensureModal();
    currentTo = toName || '';
    currentFrom = fromName || '';
    currentColor = colorHex;
    currentPages = pages;
    currentIndex = 0;
    render();
    modal.classList.add('open');
  };
})();
