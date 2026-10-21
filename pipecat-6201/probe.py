"""Independent #6201 verification using Pipecat's real local pipeline.

Topology and reported input sequence adapted from shehroze-1122's issue
#6201 and Cross2pro's PR #6232. Pipecat: Copyright (c) 2024-2026, Daily,
BSD-2-Clause; see PIPECAT-LICENSE.txt. Additional measurements by FAULTLINE.
No STT, TTS, telephone network, real LLM or production trace is used.
"""

import argparse
import asyncio
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


async def trial(case, timing):
    # Fail any accidental IP connection, including provider or telemetry calls.
    original_connect = socket.socket.connect

    def no_network(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise RuntimeError("Network use is forbidden in this local probe")
        return original_connect(sock, address)

    socket.socket.connect = no_network
    from pipecat.frames.frames import (
        DataFrame, ErrorFrame, FunctionCallFromLLM, LLMContextFrame,
        LLMFullResponseEndFrame, LLMFullResponseStartFrame, LLMTextFrame,
        TranscriptionFrame, VADUserStartedSpeakingFrame, VADUserStoppedSpeakingFrame,
    )
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.processors.aggregators.llm_context import LLMContext
    from pipecat.processors.aggregators.llm_response_universal import (
        LLMContextAggregatorPair, LLMUserAggregatorParams,
    )
    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
    from pipecat.services.llm_service import LLMService
    from pipecat.tests.utils import SleepFrame, run_test
    from pipecat.turns.user_mute import FunctionCallUserMuteStrategy
    from pipecat.turns.user_start import VADUserTurnStartStrategy
    from pipecat.turns.user_stop import SpeechTimeoutUserTurnStopStrategy
    from pipecat.turns.user_turn_strategies import FilterIncompleteUserTurnStrategies

    events = []
    start = time.monotonic()
    snapshot = {}
    answer = "I couldn't check availability. Please try again." if case["tool_error"] else "Tuesday at ten works."

    def record(kind, **fields):
        events.append({"t": round(time.monotonic() - start, 6), "kind": kind, **fields})

    @dataclass
    class SnapshotFrame(DataFrame):
        pass

    class Tap(FrameProcessor):
        def __init__(self, label):
            super().__init__()
            self.label = label

        async def process_frame(self, frame, direction):
            await super().process_frame(frame, direction)
            if isinstance(frame, ErrorFrame):
                record("framework_error", error=frame.error, tap=self.label)
            if direction == FrameDirection.DOWNSTREAM:
                if self.label == "input" and isinstance(frame, (VADUserStartedSpeakingFrame, VADUserStoppedSpeakingFrame)):
                    record("speech_start" if isinstance(frame, VADUserStartedSpeakingFrame) else "speech_stop")
                if self.label == "output" and isinstance(frame, LLMTextFrame):
                    record("output_text", text=frame.text)
                if self.label == "input" and isinstance(frame, SnapshotFrame):
                    controller = aggs.user()._user_turn_controller
                    snapshot.update({
                        "inferences": llm.inferences, "tool_calls": llm.tool_calls,
                        "user_turn_open": controller._user_turn,
                        "controller_speaking": controller._user_speaking,
                        "assistant_speaking_state": aggs.assistant()._user_speaking,
                        "context": context.get_messages(),
                    })
                    record("snapshot")
            await self.push_frame(frame, direction)

    class ScriptedLLM(LLMService):
        def __init__(self):
            # Scripted output has no provider sampling settings. Initialize
            # unsupported fields explicitly, as the service contract requires.
            from pipecat.services.settings import LLMSettings
            super().__init__(settings=LLMSettings(
                model=None, system_instruction=None, temperature=None,
                max_tokens=None, top_p=None, top_k=None, frequency_penalty=None,
                presence_penalty=None, seed=None, filter_incomplete_user_turns=None,
                user_turn_completion_config=None, use_provider_thinking_default=False,
            ))
            self.inferences = 0
            self.tool_calls = 0

        async def process_frame(self, frame, direction):
            await super().process_frame(frame, direction)
            if isinstance(frame, LLMContextFrame):
                self.inferences += 1
                record("inference", number=self.inferences)
                await self.push_frame(LLMFullResponseStartFrame())
                if self.inferences == 1:
                    await asyncio.sleep(timing["model_delay"])
                    record("tool_commit")
                    await self.run_function_calls([FunctionCallFromLLM(
                        function_name="check_availability", tool_call_id="call_1",
                        arguments={}, context=frame.context,
                    )])
                else:
                    await self._push_llm_text("● " + answer)
                await self.push_frame(LLMFullResponseEndFrame())
            else:
                await self.push_frame(frame, direction)

    async def check_availability(params):
        llm.tool_calls += 1
        record("tool_started")
        await asyncio.sleep(case["tool_delay"])
        record("tool_result")
        await params.result_callback(
            {"error": "availability service unavailable"} if case["tool_error"]
            else {"available": ["Tuesday 10:00"]}
        )

    llm = ScriptedLLM()
    llm.register_function("check_availability", check_availability)
    context = LLMContext()
    aggs = LLMContextAggregatorPair(context, user_params=LLMUserAggregatorParams(
        user_turn_strategies=FilterIncompleteUserTurnStrategies(
            start=[VADUserTurnStartStrategy()],
            stop=[SpeechTimeoutUserTurnStopStrategy(user_speech_timeout=timing["speech_timeout"])],
        ),
        user_mute_strategies=[FunctionCallUserMuteStrategy()] if case["mute"] else [],
        user_turn_stop_timeout=timing["watchdog"],
    ))

    @aggs.user().event_handler("on_user_turn_stop_timeout")
    async def on_timeout(_):
        record("watchdog")

    frames = [VADUserStartedSpeakingFrame(), TranscriptionFrame(
        "can I book an appointment", user_id="synthetic-caller", timestamp="2026-10-21T00:00:00Z"
    ), SleepFrame(timing["initial_speech_stop"]), VADUserStoppedSpeakingFrame()]
    last = timing["initial_speech_stop"]
    for when, edge in case["speech"]:
        frames.extend([SleepFrame(when - last), VADUserStartedSpeakingFrame() if edge == "start" else VADUserStoppedSpeakingFrame()])
        last = when
    frames.extend([SleepFrame(timing["observation_end"] - last), SnapshotFrame(), SleepFrame(0.05)])
    # Observe the pre-TTS output. The final assistant aggregator consumes text;
    # a tap after it cannot distinguish a good answer from missing output.
    await run_test(Pipeline([Tap("input"), aggs.user(), llm, Tap("output"), aggs.assistant()]),
                   frames_to_send=frames, start_timeout=15)
    output = "".join(e["text"] for e in events if e["kind"] == "output_text")
    times = lambda kind: [e["t"] for e in events if e["kind"] == kind]
    starts, stops, commits, results = (times(k) for k in ("speech_start", "speech_stop", "tool_commit", "tool_result"))
    order_ok = len(commits) == len(results) == 1 and bool(snapshot)
    if case["speech"] and order_ok:
        order_ok = times("inference")[0] < starts[1] < commits[0]
        if case["order"] == "during_tool":
            order_ok &= commits[0] < stops[1] < results[0]
        elif case["order"] == "before_tool":
            order_ok &= stops[1] < commits[0]
        elif case["order"] == "after_result":
            order_ok &= results[0] < stops[1]
        if len(case["speech"]) > 2:
            order_ok &= commits[0] < starts[2] < stops[2] < results[0]
    errors = [e for e in events if e["kind"] == "framework_error"]
    passed = (output.strip() == answer and snapshot.get("inferences") == 2
              and snapshot.get("tool_calls") == 1 and not snapshot.get("user_turn_open"))
    return {
        "case": case["id"], "status": "error" if errors or not order_ok else "pass" if passed else "fail",
        "event_order_valid": order_ok, "expected_answer": answer, "output_text": output,
        "snapshot_before_teardown": snapshot, "events": events,
        "pending_tasks_after_cleanup": len([t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]),
        "answer_after_result_ms": round((times("output_text")[0] - results[0]) * 1000, 2) if times("output_text") and results else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path)
    parser.add_argument("--patch", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case")
    args = parser.parse_args()
    plan = json.loads((HERE / "cases.json").read_text())
    if args.case:
        case = next(c for c in plan["cases"] if c["id"] == args.case)
        print(json.dumps(asyncio.run(trial(case, plan["timing"])))); return
    if not all((args.base, args.patch, args.output)):
        parser.error("--base, --patch and --output required")
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    sources = {}
    for label, repo in (("base", args.base.resolve()), ("patch", args.patch.resolve())):
        commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        if commit != plan["revisions"][label]:
            raise RuntimeError("Revision mismatch: " + label)
        sources[label] = {"commit": commit, "files": {
            str(p.relative_to(repo)): sha(p) for p in sorted((repo / "src/pipecat").rglob("*.py"))
        }}
        for case in plan["cases"]:
            for repeat in range(1, plan["repeats"] + 1):
                name = f"{label}-{case['id']}-{repeat}"
                env = {"PATH": os.environ["PATH"], "HOME": str(args.output.resolve()),
                       "PYTHONPATH": str(repo / "src"), "PYTHONUNBUFFERED": "1",
                       "HF_HUB_OFFLINE": "1", "DO_NOT_TRACK": "1"}
                try:
                    proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--case", case["id"]],
                                          cwd=args.output, env=env, text=True, capture_output=True, timeout=40)
                    (args.output / (name + ".stdout")).write_text(proc.stdout)
                    (args.output / (name + ".stderr")).write_text(proc.stderr)
                    record = json.loads(proc.stdout) if proc.returncode == 0 else {"case": case["id"], "status": "error", "returncode": proc.returncode}
                except subprocess.TimeoutExpired:
                    record = {"case": case["id"], "status": "error", "reason": "process timeout"}
                record.update(revision=label, repeat=repeat)
                records.append(record)
                print(name, record["status"], record.get("output_text", ""), flush=True)
    (args.output / "results.json").write_text(json.dumps(records, indent=2) + "\n")
    (args.output / "source-checksums.json").write_text(json.dumps(sources, indent=2) + "\n")
    manifest = {"stage": plan["stage"], "platform": platform.platform(), "python": platform.python_version(),
                "model": "scripted; no inference", "model_calls": 0, "revisions": plan["revisions"],
                "frozen_inputs": {p.name: sha(p) for p in (HERE / "cases.json", Path(__file__).resolve())},
                "totals": {s: sum(r["status"] == s for r in records) for s in ("pass", "fail", "error")},
                "files": {p.name: sha(p) for p in sorted(args.output.iterdir()) if p.is_file()}}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
