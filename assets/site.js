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

// Match the reference portfolio's active tabs and reading progress without dependencies.
const navLinks = Array.from(document.querySelectorAll('.site-header nav a[href^="#"]'));
const projects = navLinks.map(link => document.querySelector(link.getAttribute('href')));
const progressBar = document.querySelector('.scroll-progress span');
const header = document.querySelector('.site-header');
let scrollFrame = 0;

function updateNavigation() {
  scrollFrame = 0;
  const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
  const maxScroll = scrollHeight - clientHeight;
  const progress = maxScroll > 0 ? Math.min(1, Math.max(0, scrollTop / maxScroll)) : 0;
  progressBar.style.transform = `scaleX(${progress})`;
  const threshold = header.offsetHeight + window.innerHeight * 0.35;
  let activeIndex = -1;
  projects.forEach((project, index) => {
    if (project && project.getBoundingClientRect().top <= threshold) activeIndex = index;
  });
  if (maxScroll > 0 && scrollTop >= maxScroll - 2) activeIndex = projects.length - 1;
  navLinks.forEach((link, index) => {
    if (index === activeIndex) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
}

function scheduleNavigation() {
  if (!scrollFrame) scrollFrame = requestAnimationFrame(updateNavigation);
}
window.addEventListener('scroll', scheduleNavigation, { passive: true });
window.addEventListener('resize', scheduleNavigation);
new ResizeObserver(scheduleNavigation).observe(document.body);
updateNavigation();
