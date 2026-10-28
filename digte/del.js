(() => {
  'use strict';
  let dialog, opener, current;
  const create = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
  };
  function makeDialog() {
    dialog = create('dialog', 'share-dialog');
    dialog.setAttribute('aria-labelledby', 'share-heading');
    const close = create('button', 'share-close', '×');
    close.type = 'button'; close.setAttribute('aria-label', 'Luk deling');
    close.addEventListener('click', () => dialog.close());
    const heading = create('h2', '', 'Del digtet.'); heading.id = 'share-heading';
    const label = create('p', 'share-poem-label'); label.id = 'share-poem-label';
    dialog.append(close, heading, label);
    if (typeof navigator.share === 'function') {
      const apps = create('button', 'button share-apps', 'Del via dine apps ↗');
      apps.type = 'button';
      apps.addEventListener('click', async () => {
        try { await navigator.share(current); }
        catch (error) {
          if (error.name !== 'AbortError') document.getElementById('share-status').textContent = 'Delingsmenuen kunne ikke åbnes. Vælg en mulighed nedenfor.';
        }
      });
      dialog.append(apps);
    }
    const links = create('div', 'share-platforms');
    const platforms = ['Facebook', 'WhatsApp', 'Telegram', 'X', 'LinkedIn', 'E-mail'];
    for (const name of platforms) {
      const link = create('a', 'share-platform', name);
      link.dataset.platform = name;
      if (name !== 'E-mail') { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
      links.append(link);
    }
    dialog.append(links);
    const hint = create('p', 'hint', 'Du kan også kopiere linket til Messenger, Instagram eller en anden app.');
    const row = create('div', 'share-copy-row');
    const input = create('input'); input.id = 'share-url'; input.type = 'text'; input.readOnly = true; input.setAttribute('aria-label', 'Link til digtet');
    input.addEventListener('click', () => input.select());
    const copy = create('button', 'button', 'Kopiér link'); copy.type = 'button';
    copy.addEventListener('click', async () => {
      const status = document.getElementById('share-status');
      try {
        if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(current.url);
        status.textContent = 'Linket er kopieret. Klar til at sende videre.';
      } catch {
        input.focus(); input.select(); input.setSelectionRange(0, input.value.length);
        status.textContent = 'Linket er markeret. Kopiér det med Ctrl+C, ⌘C eller din telefons kopifunktion.';
      }
    });
    row.append(input, copy);
    const status = create('p', 'status'); status.id = 'share-status'; status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
    dialog.append(hint, row, status);
    dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
    dialog.addEventListener('close', () => opener?.focus());
    document.body.append(dialog);
  }
  document.addEventListener('click', event => {
    const button = event.target.closest?.('[data-share-poem]');
    if (!button) return;
    const url = new URL(button.dataset.sharePoem, 'https://solstorm.org');
    if (url.origin !== 'https://solstorm.org' || !url.pathname.startsWith('/digte/')) return;
    current = { title: button.dataset.shareTitle || 'Et digt af Solstorm', text: 'Et digt af Solstorm', url: url.href };
    opener = button;
    if (!dialog) makeDialog();
    document.getElementById('share-poem-label').textContent = button.dataset.shareLabel || 'Et digt af Solstorm';
    document.getElementById('share-url').value = current.url;
    document.getElementById('share-status').textContent = '';
    const u = encodeURIComponent(current.url), t = encodeURIComponent(current.title), message = encodeURIComponent(current.title + '\n' + current.url);
    const destinations = {
      Facebook: 'https://www.facebook.com/sharer/sharer.php?u=' + u,
      WhatsApp: 'https://wa.me/?text=' + message,
      Telegram: 'https://t.me/share/url?url=' + u + '&text=' + t,
      X: 'https://twitter.com/intent/tweet?url=' + u + '&text=' + t,
      LinkedIn: 'https://www.linkedin.com/sharing/share-offsite/?url=' + u,
      'E-mail': 'mailto:?subject=' + t + '&body=' + message
    };
    for (const link of dialog.querySelectorAll('[data-platform]')) link.href = destinations[link.dataset.platform];
    dialog.showModal();
  });
})();
