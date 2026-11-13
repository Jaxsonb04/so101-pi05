#!/usr/bin/env python
"""Score policy trials: A = start trial, B = pass, C = fail (then 0-3: tools in the box),
D = go home now (saved as stopped), M = mark a moment for the review.

Runs the official lerobot-rollout (episodic strategy) with your usual flags and swaps only
its keyboard and timed reset for a page at http://127.0.0.1:8101 that also shows the
cameras. No LeRobot file is changed. Run it in the lerobot environment, WITHOUT --teleop.*:
LeRobot then sends the follower back to the pose it had when the command started after
every trial, and holds it there while you reset the scene.

- Every trial is saved in the rollout dataset; its result goes in trial_labels.csv there.
- --dataset.num_episodes is the number of judged trials (pass or fail); stopped ones are extra.
- If a trial reaches --dataset.episode_time_s, the arm goes home and the page asks 0-4 (4 = pass).
- --continue: after a crash or restart, count the judged trials already saved by earlier runs of the
  same --dataset.repo_id (each run gets its own _<date>_<time> folder); --dataset.num_episodes is then
  the total over all those runs, and the page shows the next layout number.

    python tools/eval_ui.py <the lerobot-rollout flags, without --teleop.*> [--continue]
    python tools/eval_ui.py --demo       # try the page without the robot
    python tools/eval_ui.py --selftest   # automated check, no robot
"""

import json
import os
import sys
import tempfile
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from types import SimpleNamespace

import record_ui as ui  # the recording page's server, camera feed and helpers

ui.PAGE = Path(__file__).with_name("eval_ui.html").read_bytes()
LABELS = "trial_labels.csv"
HEADER = "episode_index,result,tools_in_box,marks"
RESULT = {"b": "pass", "c": "fail", "d": "stopped"}
state, events = ui.state, ui.events
state.update(stopped=0, trial=0, count=None, marks=[], tools=0)
ui.KEYS.update("01234m")  # tools-in-box count and the mark key


def earlier_runs(repo_id, home=None):
    """Judged rows ([index, result, tools, marks]) saved by earlier runs of this --dataset.repo_id."""
    # shortcut: ignores --dataset.root; the eval commands never set it
    home = Path(home or os.getenv("HF_LEROBOT_HOME", Path.home() / ".cache/huggingface/lerobot")).expanduser()
    user, name = repo_id.split("/", 1)
    rows = []
    for run in sorted((home / user).glob(f"{name}_2*")):  # <name>_<date>_<time>, one folder per run
        labels, info = run / LABELS, run / "meta" / "info.json"
        if labels.exists() and info.exists():
            saved = json.loads(info.read_text())["total_episodes"]  # same rule as the upload: saved trials only
            rows += [(r.split(",") + ["", ""])[:4] for r in labels.read_text().splitlines()[1:]
                     if int(r.split(",")[0]) < saved]
    return [r for r in rows if r[1] in ("pass", "fail")]


def press(key):
    """Apply a key. One that doesn't fit the current phase is ignored.

    A start · B pass (4 in the box) · C fail, then 0-3 for tools in the box · D go home (stopped) ·
    M mark this moment for the review. At the time limit the page asks 0-4 (4 = pass)."""
    with ui.lock:
        phase, decided = state["phase"], state["decided"]
        if key == "a" and phase in ("ready", "reset"):
            state["phase"] = "starting"
        elif key in "bcd" and phase == "running" and not decided:
            state.update(decided=key, count=4 if key == "b" else None)
            events["exit_early"] = True  # ends the trial; LeRobot then sends the arm home
        elif key == "m" and phase == "running":
            state["marks"].append(round(time.monotonic() - state["started"], 1))
        elif key.isdigit() and phase == "count" and state["count"] is None and int(key) <= (3 if decided else 4):
            state.update(count=int(key), decided=decided or ("b" if key == "4" else "c"))


ui.press = press  # the shared page server calls this


def wait(ctx, until):
    while not until() and not ctx.runtime.shutdown_event.is_set():  # Ctrl+C still ends the session
        time.sleep(0.05)


def hooks(orig_run, orig_policy_loop):
    """Replacements for EpisodicStrategy.run, ._policy_loop and ._reset_loop."""

    def run(self, ctx):
        ui.match_cameras(ctx.hardware.robot_wrapper.inner.cameras)  # before the arm moves
        ui.cameras.update(ctx.hardware.robot_wrapper.inner.cameras)
        cfg = ctx.runtime.cfg.dataset
        state.update(phase="ready", task=cfg.single_task or "", limit=cfg.episode_time_s, cameras=list(ui.cameras))
        dataset, push = ctx.data.dataset, ctx.data.dataset.push_to_hub

        def push_saved(*a, **k):  # upload only labels of saved trials (a save can be cut off)
            labels = Path(dataset.root) / LABELS
            if labels.exists():
                rows = [r for r in labels.read_text().splitlines()[1:] if int(r.split(",")[0]) < dataset.num_episodes]
                labels.write_text("\n".join([HEADER, *rows]) + "\n")
            return push(*a, **k)
        dataset.push_to_hub = push_saved
        wait(ctx, lambda: state["phase"] != "ready")  # the first trial also waits for A
        orig_run(self, ctx)

    def policy_loop(self, **kw):
        with ui.lock:
            events["exit_early"] = False
            state.update(phase="running", decided=None, count=None, marks=[], started=time.monotonic(),
                         trial=kw["dataset"].num_episodes + 1)
        orig_policy_loop(self, **kw)  # the policy drives the arm until B, C, D or the time limit
        with ui.lock:  # C and the time limit ask how many tools ended in the box
            state.update(phase="home" if state["decided"] in ("b", "d") else "count", started=None)

    def reset_loop(self, ctx, **_):
        """Runs after LeRobot has sent the arm home: record the result, then wait for A."""
        self._require_engine().pause()  # no inference while the scene is reset
        wait(ctx, lambda: state["decided"] == "d" or state["count"] is not None)
        if not state["decided"]:
            return  # Ctrl+C: LeRobot saves the trial; it stays unlabelled
        dataset = ctx.data.dataset
        result, count = RESULT[state["decided"]], state["count"]
        with (Path(dataset.root) / LABELS).open("a") as f:
            if f.tell() == 0:
                f.write(HEADER + "\n")
            marks = ";".join(str(m) for m in state["marks"])
            f.write(f"{dataset.num_episodes},{result},{'' if count is None else count},{marks}\n")  # saved right after
        with ui.lock:
            state[{"pass": "passed", "fail": "failed", "stopped": "stopped"}[result]] += 1
            state["tools"] += count or 0
            state["last"] = state["decided"]
            if state["target"] and state["passed"] + state["failed"] >= state["target"]:
                events["stop_recording"] = True  # enough judged trials: save, upload, finish
                state["phase"] = "finishing"
                return
            state["phase"] = "reset"
        wait(ctx, lambda: state["phase"] != "reset")

    return run, policy_loop, reset_loop


def install(cls):
    cls.run, cls._policy_loop, cls._reset_loop = hooks(cls.run, cls._policy_loop)


def run(main):
    try:
        main()
        state["phase"] = "done"
    except Exception as e:
        state.update(phase="error", error=f"{type(e).__name__}: {e}")
        raise
    finally:  # also on Ctrl+C
        judged = state["passed"] + state["failed"]
        tools = f"; {state['tools']} tools in the box over {judged} judged trials" if judged else ""
        print(f"\n{state['passed']} passed, {state['failed']} failed, {state['stopped']} stopped{tools}. "
              f"Results are in {LABELS} in the rollout dataset folder.")
        time.sleep(3)  # let the page show the final state before the server closes


class FakeStrategy:
    """The episode loop of EpisodicStrategy.run (no teleop), without a robot."""

    def __init__(self, root, limit):
        self.dataset = SimpleNamespace(num_episodes=0, root=root, frames=0, push_to_hub=lambda: None)
        cams = {"wrist": ui.FakeCamera(), "top": ui.FakeCamera(140)}
        cfg = SimpleNamespace(dataset=SimpleNamespace(single_task="Put the tools on the table into the toolbox",
                                                      episode_time_s=limit))
        self.ctx = SimpleNamespace(runtime=SimpleNamespace(cfg=cfg, shutdown_event=threading.Event()),
                                   hardware=SimpleNamespace(robot_wrapper=SimpleNamespace(inner=SimpleNamespace(cameras=cams))),
                                   data=SimpleNamespace(dataset=self.dataset))

    def _require_engine(self):
        return SimpleNamespace(pause=lambda: None)

    def run(self, ctx):
        while not events["stop_recording"]:
            self._policy_loop(ctx=ctx, events=events, dataset=self.dataset,
                              control_time_s=ctx.runtime.cfg.dataset.episode_time_s)
            self._reset_loop(ctx=ctx)  # LeRobot returns the arm home just before this
            self.dataset.num_episodes += 1  # save_episode
            self.dataset.frames = 0

    def _policy_loop(self, ctx, events, dataset, control_time_s):
        ui.fake_record_loop(events, control_time_s, dataset)

    def _reset_loop(self, ctx, **_):
        pass


def selftest():
    install(FakeStrategy)
    base = ui.serve(0)
    state["target"] = 3
    tmp = Path(tempfile.mkdtemp())
    fake = FakeStrategy(tmp, 0.5)
    threading.Thread(target=run, args=(lambda: fake.run(fake.ctx),), daemon=True).start()

    def until(phase):
        for _ in range(300):
            if state["phase"] == phase:
                return
            time.sleep(0.01)
        raise AssertionError(f"expected {phase}, got {state['phase']}")

    assert urllib.request.urlopen(base).read().startswith(b"<!doctype html>")
    until("ready")
    with urllib.request.urlopen(f"{base}/cam/top") as video:
        assert b"\xff\xd8" in video.read(4096)  # a JPEG frame arrives
    for key in "bdm2":
        press(key)
    assert state["phase"] == "ready" and state["count"] is None  # nothing counts before a trial
    press("a"); until("running"); press("m"); press("b"); until("reset")  # trial 0: pass, one mark
    press("a"); until("running"); press("d"); until("reset")  # trial 1: stopped, no count asked
    press("a"); until("running"); press("c"); until("count")  # trial 2: fail, then how many in the box
    press("4"); assert state["count"] is None  # a fail can't have all 4 in the box
    press("2"); until("reset")
    press("a"); until("running"); until("count")  # trial 3 reaches the 0.5 s limit
    press("d"); assert not state["decided"]  # D does nothing once the trial is over
    press("4"); until("done")  # 4 at the time limit is a pass; third judged trial ends the session
    assert (state["passed"], state["failed"], state["stopped"], state["tools"]) == (2, 1, 1, 10)
    rows = (tmp / LABELS).read_text().splitlines()
    assert rows[0] == HEADER and rows[2:] == ["1,stopped,,", "2,fail,2,", "3,pass,4,"]
    assert rows[1].startswith("0,pass,4,0.") and rows[1].count(";") == 0  # the mark, in seconds into the trial

    def cam(wall):  # top fifth at `wall` brightness, the rest dark
        frame = ui.np.full((480, 640, 3), 30, ui.np.uint8)
        frame[:96] = wall
        return SimpleNamespace(read_latest=lambda max_age_ms=0: frame)
    wrist, top = cam(45), cam(120)
    cams = {"wrist": wrist, "top": top}
    assert not ui.match_cameras(cams) and cams == {"wrist": wrist, "top": top}  # as in the demos: kept
    cams = {"wrist": top, "top": wrist}  # as in the swapped 20:19 run
    assert ui.match_cameras(cams) and cams == {"wrist": wrist, "top": top}  # put back in the right slots
    try:
        ui.match_cameras({"wrist": cam(60), "top": cam(70)})  # too close to call
        raise AssertionError("an unclear case must stop, not guess")
    except RuntimeError as e:
        assert "apart" in str(e)

    home = Path(tempfile.mkdtemp())  # --continue: earlier runs of one repo_id, each in its own folder
    for name, labels, saved in [("rollout_x_20261112_205541", ["0,fail,2,", "1,pass,4,1.5"], 2),
                                ("rollout_x_20261112_215951", ["0,fail,1,", "1,stopped,,", "2,fail,3,"], 2),  # 2 never saved
                                ("rollout_x_extra_20261112_220000", ["0,pass,4,"], 1)]:  # another name
        (home / "me" / name / "meta").mkdir(parents=True)
        (home / "me" / name / "meta" / "info.json").write_text(json.dumps({"total_episodes": saved}))
        (home / "me" / name / LABELS).write_text("\n".join([HEADER, *labels]) + "\n")
    assert [r[1:3] for r in earlier_runs("me/rollout_x", home)] == [["fail", "2"], ["pass", "4"], ["fail", "1"]]
    print("selftest OK")


def main():
    args = sys.argv[1:]
    if args == ["--selftest"]:
        return selftest()
    if any(a.startswith("--teleop.") for a in args):
        sys.exit("Leave out the --teleop.* flags: without a leader the arm returns home after every trial.")
    flag = next((a.split("=", 1)[1] for a in args if a.startswith("--dataset.num_episodes=")), None)
    state["target"] = int(flag) if flag else None
    repo = next((a.split("=", 1)[1] for a in args if a.startswith("--dataset.repo_id=")), None)
    if "--continue" in args:
        sys.argv.remove("--continue")  # the page's own flag; LeRobot would reject it
        if not repo:
            sys.exit("--continue needs --dataset.repo_id, to find the earlier runs.")
        rows = earlier_runs(repo)
        state.update(passed=sum(r[1] == "pass" for r in rows), failed=sum(r[1] == "fail" for r in rows),
                     tools=sum(int(r[2] or 0) for r in rows))
        if state["target"] and len(rows) >= state["target"]:
            sys.exit(f"All {len(rows)} judged trials of {repo} are already saved. Nothing left to run.")
        print(f"Continuing {repo}: {len(rows)} judged trials saved by earlier runs; next is layout {len(rows) + 1}.")
    if args == ["--demo"]:
        install(FakeStrategy)
        state["target"] = 3
        url = ui.serve()
        print(f"Eval page: {url}")
        webbrowser.open(url)
        with tempfile.TemporaryDirectory() as tmp:
            fake = FakeStrategy(Path(tmp), 30)
            return run(lambda: fake.run(fake.ctx))

    from lerobot.rollout.strategies import episodic
    from lerobot.scripts import lerobot_rollout

    install(episodic.EpisodicStrategy)
    episodic.init_keyboard_listener = lambda: (None, events)  # the page is the keyboard
    sys.argv.append("--dataset.num_episodes=1000000")  # LeRobot skips the reset (labels, going home) after its last episode; the page stops itself
    sys.argv.append("--play_sounds=false")  # LeRobot's spoken cues would be out of step with the page
    url = ui.serve()
    print(f"Eval page: {url}  (keys work while that window is in front)")
    webbrowser.open(url)
    run(lerobot_rollout.main)


if __name__ == "__main__":
    main()
