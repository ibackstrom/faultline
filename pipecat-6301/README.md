# Pipecat #6301: local tool-resumption verification

22 October 2026. Original report and reproduction:
https://github.com/pipecat-ai/pipecat/issues/6301. This is an independent
reproduction and proposed local fix, not discovery of the original bug.

Base: `3c9da9d83d038ef82c272bf234856d9543f68888` of pipecat-ai/pipecat.
Python 3.12.9, google-genai 2.32.0; full packages in `environment.txt`.
The reporter used Python 3.12.15 / google-genai 2.31.0; those exact versions
were not tested here. The reporter's script itself was run unchanged.

## Results

- Unchanged reporter script: resumed connection sends call-1 again with
  fallback name on base; sends only call-2 after patch.
- Frozen six-case matrix: base 4 failed / 2 passed; patched 6 passed.
- Broader Gemini Live suite including these cases: 57 passed, 5 skipped,
  21 warnings (SDK deprecation / serialization). Not the entire Pipecat suite.
- Tests use real Pipecat context-frame processing and reconnect/cleanup;
  connection establishment and SDK sessions are mocked. No model calls,
  external provider requests, audio or live telephony. Model/sampling
  configuration is not applicable: no inference was performed.
- These selected deterministic cases are not accuracy estimates, customer
  success rates, or evidence of commercial demand.

The fix preserves settled IDs and function names only when reconnecting
with a resumption handle. Normal disconnect and no-handle reconnect retain
their cleanup behavior. Preserving the actual bookkeeping avoids classifying
all context results as already sent merely because they exist at readiness.

Not verified: Gemini's reaction to duplicate results, failed/ambiguous network
sends, rejected resumption handles, or a context frame processed while
disconnected. The pending-result case adds a result during reconnect and
pushes the context after readiness; it does not cover disconnected processing.

`before.txt` is an invalid preliminary run: three async cases hit a misspelled
test helper, not a product defect. The helper was corrected before changing
production code (`before-valid.*`). Final evidence uses identical lint-clean
tests in `base-final.*` and `patched-final.*`; four genuine assertions fail
before the patch. Earlier outputs are preserved, not overwritten.

## Reproduce in a disposable checkout

Copy this evidence directory outside the checkout, then:

```sh
git clone https://github.com/pipecat-ai/pipecat.git pipecat-6301
cd pipecat-6301
git checkout 3c9da9d83d038ef82c272bf234856d9543f68888
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e '.[google]' pytest pytest-asyncio pytest-xdist
# EVIDENCE is the absolute path to this evidence directory.
cp "$EVIDENCE/test_gemini_live_tool_resumption.py" tests/
.venv/bin/python "$EVIDENCE/reporter_repro.py"
.venv/bin/pytest -n 0 tests/test_gemini_live_tool_resumption.py
# Expected: 4 failed / 2 passed.
git apply "$EVIDENCE/fix.patch"
.venv/bin/python "$EVIDENCE/reporter_repro.py"
.venv/bin/pytest -n 0 tests/test_gemini_live*.py
# Observed here: 57 passed / 5 skipped.
```

Dependency resolution may change; use `environment.txt` for the recorded
versions. The patch is proposed, not merged or deployed. No PR was opened.
