# FAULTLINE

Independent AI-agent failure reproduction and patch verification.

[Website](https://ibackstrom.github.io/faultline/) ·
[About](https://ibackstrom.github.io/faultline/about.html)

## Service pages

The homepage and [Search landing](ai-agent-testing.html) cover independent
AI agent testing for tools, chat, workflows and voice. About remains in the
top navigation. Both use `campaign-styles.css`, `landing.js` and the two
`assets/optical-*.jpg` images. The images are AI-generated metaphors, not
test evidence. About and existing case pages retain their original stylesheet.

Contact details appear only after a click. This deters simple HTML scrapers,
not bots that execute JavaScript. Only the dedicated ad landing pre-fills
the `FLSEARCH01` email marker; the homepage does not label organic inquiries
as ad leads. No campaign, tracking tag or contact-form backend is installed.
The private campaign workbook and lead log are not in this public repository.

## Keeping tool results correct across reconnects

[Pipecat #6301 report](https://ibackstrom.github.io/faultline/pipecat-6301/report.html):
independent reproduction, proposed resumption-bookkeeping patch and
[runnable tests](pipecat-6301/README.md). Six local checks: base 4 failed / 2
passed, patched 6 passed. Real service with mocked SDK connections, not live
Gemini or voice calls. Original discovery credited to the issue reporter.
The patch and tests are posted upstream; not merged or deployed. Published
logs redact absolute workspace paths; their checksums cover the public copies.

## The tool returned. The agent stayed silent.

We independently replayed a reported Pipecat turn-taking failure using its
real local pipeline with synthetic speech and scripted responses. Eight
selected sequences, three repeats each: original 6/24 checks passed,
proposed upstream patch 24/24. No live calls or real model inference.

[Read the article](https://ibackstrom.github.io/faultline/pipecat-silence.html),
[run the evidence package](pipecat-6201/README.md), or
[download the two-page PDF](https://ibackstrom.github.io/faultline/faultline-voice-verification.pdf).

The original report belongs to Shehroze Talat; the proposed fix belongs to
Cross2pro. Our contribution is independent verification, not their discovery
or patch. These selected checks are not production reliability estimates.

## Typography

About and existing case pages serve Manrope locally. The simplified service
pages use system sans-serif, a cool near-white/charcoal palette, and blue CTAs.
The centered composition takes inspiration from Apple's marketing hierarchy;
no Apple font files or brand assets are distributed. Manrope has system sans-serif fallbacks and
`font-display: swap`. The Latin variable WOFF2 (weights 200–800, 24 KiB) is
an unmodified Google Fonts asset from
https://fonts.gstatic.com/s/manrope/v20/xn7gYHE41ni1AdIRggexSvfedN4.woff2.
Its SIL Open Font License is included in [fonts/OFL.txt](fonts/OFL.txt),
from https://github.com/google/fonts/blob/main/ofl/manrope/OFL.txt.
Visitors make no requests to Google Fonts. Other scripts use system fallbacks;
technical labels retain the system monospace stack. No font build step is needed.
