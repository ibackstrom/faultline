// Restrained scroll reveals. No dependencies, no tracking, no cookies.
// Adds one class; elements are only hidden when this script actually runs.
document.documentElement.classList.add('js');
const targets = Array.from(document.querySelectorAll('.reveal'));
if (!('IntersectionObserver' in window)) {
  targets.forEach(el => el.classList.add('revealed'));
} else {
  targets.forEach(el => {
    const group = el.parentElement
      ? Array.from(el.parentElement.children).filter(c => c.classList && c.classList.contains('reveal'))
      : [el];
    el.style.transitionDelay = (Math.max(0, group.indexOf(el)) % 6) * 70 + 'ms';
  });
  const io = new IntersectionObserver(entries => {
    for (const e of entries) {
      if (e.isIntersecting) {
        e.target.classList.add('revealed');
        io.unobserve(e.target);
      }
    }
  }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
  targets.forEach(el => io.observe(el));
}
