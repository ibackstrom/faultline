// No analytics or lead submission. Opening mail is not a recorded conversion.
// Click-to-reveal deters simple HTML scrapers, not bots that execute JavaScript.
const reveal = document.getElementById('show-email');
reveal.hidden = false;
reveal.addEventListener('click', () => {
  const address = ['lapland', 'dream'].join('') + '@' + ['gmail', 'com'].join('.');
  const link = document.getElementById('email-cta');
  const campaign = document.body.dataset.campaign;
  const subject = 'AI agent testing' + (campaign ? ' [' + campaign + ']' : '');
  const body = 'Stack:\nTask to test:\nExpected result:\nWhat happens now:\nDeadline:\n\nPlease do not include credentials or customer data.';
  link.href = 'mailto:' + address + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
  document.getElementById('email-address').textContent = address;
  document.getElementById('email-options').hidden = false;
  reveal.setAttribute('aria-expanded', 'true');
  reveal.hidden = true;
  link.focus();
  document.getElementById('copy-email').addEventListener('click', async () => {
    const status = document.getElementById('copy-status');
    try {
      await navigator.clipboard.writeText(address);
      status.textContent = campaign ? 'Address copied. Add ' + campaign + ' to the subject if you came from the ad.' : 'Address copied. Tell us what needs testing.';
    } catch {
      status.textContent = 'Clipboard blocked. Select and copy the address shown above.';
    }
  });
}, { once: true });
