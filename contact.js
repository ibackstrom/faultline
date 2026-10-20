// Hide the address from simple HTML/email crawlers, not determined scrapers.
document.getElementById('reveal-contact').addEventListener('click', () => {
  const address = [108, 97, 112, 108, 97, 110, 100, 100, 114, 101, 97, 109, 64, 103, 109, 97, 105, 108, 46, 99, 111, 109]
    .map(code => String.fromCharCode(code)).join('');
  const link = document.createElement('a');
  link.className = 'contact-email';
  link.href = 'mailto:' + address + '?subject=One%20workflow%20to%20check';
  link.textContent = address + ' ↗';
  document.getElementById('contact-address').replaceChildren(link);
  link.focus();
});
