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
