# The tool returned. The agent stayed silent.

[Read the FAULTLINE article](https://ibackstrom.github.io/faultline/pipecat-silence.html)
or [download the two-page service overview](https://ibackstrom.github.io/faultline/faultline-voice-verification.pdf).

Independent local verification of [Shehroze Talat's issue #6201](https://github.com/pipecat-ai/pipecat/issues/6201)
and [Cross2pro's proposed patch #6232](https://github.com/pipecat-ai/pipecat/pull/6232).
We didn't discover the original failure or write the patch.

## What ran

Eight frozen cases, three fresh-process repeats, two pinned revisions.
The original passed 6/24 checks; the proposed patch passed 24/24. The
original's 18 failures emitted no answer in the five-second observation.
These are selected consistency checks, not independent production samples
or a general accuracy estimate.

The pipeline, aggregators, turn controller and function dispatch are real
Pipecat. Speech events, model decisions and tool data are synthetic. No
model inference, STT, TTS, telephone transport or customer data is involved.
Temperature, sampling seed, token budgets and thinking are not applicable.
Trials deny outbound IP socket connections; dependency installation needs
network access. No provider credentials are needed.

A pass requires expected text at the pre-TTS output, two inference requests,
one tool execution and a closed user turn. Framework ErrorFrames, invalid
event ordering and process failures are errors, not silence findings.
All 48 final trials have valid event order and zero pending asyncio tasks
after cleanup. Scripted application errors are distinct test inputs.

## Reproduce

Requires Git and uv. Recorded on macOS arm64, Python 3.12.9. The commands
below use a new directory and do not modify a project checkout. Allow
roughly five minutes for the matrix after installing dependencies.

```sh
mkdir pipecat-replay
cd pipecat-replay
git clone https://github.com/ibackstrom/faultline.git evidence
git clone https://github.com/pipecat-ai/pipecat.git patch
git -C patch fetch origin pull/6232/head
git -C patch checkout --detach 24c3053c4fe5c02822371394acd6450ebe4de8c9
git -C patch worktree add --detach ../base 844dad94866ce589f1e4862eff09dc4f38c3d844
uv sync --directory patch --python 3.12.9 --frozen --group dev
patch/.venv/bin/python evidence/pipecat-6201/probe.py \
  --base base --patch patch --output new-run
```

The output directory must not exist. Reuse of a completed directory is
refused. Compare `new-run/results.json`; the script records failures rather
than returning a nonzero process status just because the original fails.
Expected per-revision totals: base 6 pass/18 fail/0 error, patch 24/0/0.
Exact elapsed times will vary. A loaded machine can invalidate the intended
order; inspect error trials instead of counting them as failures.

The environment installs the patch as an editable package. Each child
imports the requested revision through an explicit PYTHONPATH. Package
metadata can show the patch's version on both sides, so use the recorded
commit and source checksums, not the startup version banner, for attribution.

The four upstream suites we also executed:

```sh
PYTHONPATH="$PWD/patch/src" patch/.venv/bin/python -m pytest \
  patch/tests/test_context_aggregators_universal.py \
  patch/tests/test_user_turn_controller.py \
  patch/tests/test_user_mute_strategy.py \
  patch/tests/test_user_turn_completion_mixin.py
# For the base, use base/src and the same four files under base/tests/.
```

Observed: base 191 passed, patch 194 passed, 44 warnings each.

## Evidence and caveats

`cases.json` and `probe.py` were hashed before execution. `run/` contains
all final stdout/stderr, results, source checksums and the original run
manifest. `manifest.json` covers the public package's files and provenance.
`environment.txt` records installed dependency versions. `PIPECAT-LICENSE.txt`
retains Pipecat's BSD-2-Clause notice; the probe adapts topology and timing
from the issue/PR. The accompanying probe is offered under the same terms,
with additional measurements copyright 2026 FAULTLINE contributors.

An initial v1 recorder sat after an aggregator that consumes text, so even
passing controls looked silent. Its classifications were discarded. v2
moved the recorder before that aggregator; its 6/24 versus 24/24 result
matched this final v3. v3 explicitly initialized unsupported mock settings
to remove an ERROR-level startup diagnostic. Cases and timing stayed
unchanged. Only final v3 traces are included here; prior local artifacts
remain preserved separately. The synthetic VAD stop_secs warning remains:
we aren't measuring audio/STT latency.

Upstream test logs are copies with the local workspace prefix replaced by
`[LOCAL_WORKSPACE]`; their checksums are for those public copies. Final
trial logs, result JSON and source hashes are unchanged copies. The public
manifest distinguishes package checksums from the original run manifest.

The patch can wait for the watchdog before producing an answer. This does
not demonstrate recovery of muted transcripts, cancellation of stale
inference, a released fix, or safety across other configurations. The PR
was open when checked on 21 October 2026. No customer outcome is claimed.
