'use strict';

const dialog = document.querySelector('#image-dialog');
const image = document.querySelector('#dialog-img');
const caption = document.querySelector('#image-caption');
let previousFocus;

document.querySelectorAll('[data-image]').forEach(button => {
  button.addEventListener('click', () => {
    previousFocus = button;
    image.src = button.dataset.image;
    image.alt = button.querySelector('img').alt;
    caption.textContent = image.alt;
    dialog.showModal();
  });
});
document.querySelector('#close-dialog').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  if (event.target === dialog) {
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  }
});
dialog.addEventListener('close', () => {
  image.removeAttribute('src');
  if (previousFocus) previousFocus.focus({ preventScroll: true });
});

const projectLinks = [...document.querySelectorAll('.project-nav a')];
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    projectLinks.forEach(link => {
      const active = link.hash === '#' + entry.target.id;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  });
}, { rootMargin: '-135px 0px -55% 0px', threshold: 0 });
document.querySelectorAll('.project-section').forEach(section => observer.observe(section));

// Reveal the target project if a case link is added in the future.
window.addEventListener('beforeprint', () => {
  document.querySelectorAll('.case').forEach(detail => {
    detail.dataset.wasOpen = String(detail.open);
    detail.open = true;
  });
});
window.addEventListener('afterprint', () => {
  document.querySelectorAll('.case').forEach(detail => {
    detail.open = detail.dataset.wasOpen === 'true';
    delete detail.dataset.wasOpen;
  });
});
