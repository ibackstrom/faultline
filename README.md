# FAULTLINE

Independent AI-agent failure reproduction and patch verification.

[Website](https://ibackstrom.github.io/faultline/) ·
[About](https://ibackstrom.github.io/faultline/about.html)

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

The site serves Manrope locally, with system sans-serif fallbacks and
`font-display: swap`. The Latin variable WOFF2 (weights 200–800, 24 KiB) is
an unmodified Google Fonts asset from
https://fonts.gstatic.com/s/manrope/v20/xn7gYHE41ni1AdIRggexSvfedN4.woff2.
Its SIL Open Font License is included in [fonts/OFL.txt](fonts/OFL.txt),
from https://github.com/google/fonts/blob/main/ofl/manrope/OFL.txt.
Visitors make no requests to Google Fonts. Other scripts use system fallbacks;
technical labels retain the system monospace stack. No font build step is needed.
