#!/usr/bin/env python
"""Record LeRobot demos: A = start, B = pass, C = fail (both saved), D = cancel (not saved).

Runs the official lerobot-record with your usual flags and swaps only its keyboard
controls for a page at http://127.0.0.1:8101 that also shows the cameras. No LeRobot
file is changed. Run it in the lerobot environment.

- Passed and failed episodes are saved; a cancelled one is thrown away and recorded again.
  Each saved result goes in episode_labels.csv inside the dataset folder,
  which is uploaded with the dataset. Train on passes only with
  --dataset.exclude_episodes="[<failed numbers>]" (printed at the end).
- --dataset.num_episodes is the TOTAL number of passes wanted in the dataset; failed ones are extra.
- Running the same command again continues the same dataset; earlier passes count toward the total.

    python tools/record_ui.py <the usual lerobot-record flags>
    python tools/record_ui.py --demo       # try the page without the robot
    python tools/record_ui.py --selftest   # automated check, no robot
"""

import json
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

PORT = 8101
HOSTS = set()  # set by serve()
PAGE = Path(__file__).with_name("record_ui.html").read_bytes()
LABELS = "episode_labels.csv"

# The same flags LeRobot's own key listener sets; record() and record_loop() read them every tick.
events = {"exit_early": False, "rerecord_episode": False, "stop_recording": False}
state = {"phase": "connecting", "passed": 0, "failed": 0, "failed_episodes": [], "target": None,
         "repo": None, "task": "", "cameras": [], "started": None, "limit": None, "decided": None,
         "last": None, "error": None}
cameras = {}  # LeRobot's own camera objects, read for the page's video
current = {}  # the dataset being recorded
lock = threading.Lock()
orig_record_loop = None  # LeRobot's record_loop, or a fake one for --demo / --selftest


def press(key):
    """Apply A/B/C/D. A key that doesn't fit the current phase is ignored."""
    with lock:
        if key == "a" and state["phase"] == "ready":
            state.update(phase="recording", started=time.monotonic())
            events["exit_early"] = True  # ends the waiting loop
        elif key in ("b", "c", "d") and state["phase"] == "recording" and not state["decided"]:
            state["decided"] = key
            events["rerecord_episode"] = key == "d"  # LeRobot's own re-record: discards the frames and video
            events["exit_early"] = True  # ends the episode; LeRobot then saves it, unless cancelled


def saved_labels(labels, saved):
    """Drop rows for episodes that were never saved (e.g. Ctrl+C during a save); return (passed, failed numbers)."""
    if not labels.exists():
        return 0, []
    rows = [r for r in labels.read_text().splitlines()[1:] if int(r.split(",")[0]) < saved]
    labels.write_text("\n".join(["episode_index,result", *rows]) + "\n")
    failed = [int(r.split(",")[0]) for r in rows if r.endswith(",fail")]
    return len(rows) - len(failed), failed


def record_loop(**kw):
    """Stands in for lerobot_record.record_loop: wait for A, then record until B, C or D."""
    dataset = kw.get("dataset")
    if dataset is None:
        return  # LeRobot's timed reset phase: skipped, because A starts the next episode
    index = dataset.num_episodes  # the number LeRobot gives this episode when it saves it
    labels = Path(dataset.root) / LABELS
    if current.get("dataset") is not dataset:
        current.update(dataset=dataset, labels=labels)
        push = dataset.push_to_hub  # LeRobot uploads before run() finishes, so fix the labels first

        def push_saved(*a, **k):
            saved_labels(labels, dataset.num_episodes)
            return push(*a, **k)
        dataset.push_to_hub = push_saved
    passed, failed = saved_labels(labels, index)  # every session of this dataset
    state.update(passed=passed, failed=len(failed), failed_episodes=failed)
    if state["target"] and passed >= state["target"]:  # already enough passes: record nothing, just finish
        events.update(stop_recording=True, rerecord_episode=True)
        return
    cameras.update(kw["robot"].cameras)
    state.update(phase="ready", task=kw.get("single_task") or "", limit=kw["control_time_s"],
                 decided=None, started=None, cameras=list(cameras))
    while state["phase"] == "ready":  # arms follow the leader, nothing is recorded
        orig_record_loop(**{**kw, "dataset": None, "timer": None, "control_time_s": 60})
    with lock:
        events["exit_early"] = bool(state["decided"])  # A's signal is used up; a B/C/D pressed right after A still ends the episode
    orig_record_loop(**kw)  # records until B, C or D, or the episode time limit
    with lock:
        if state["decided"] in ("b", "c") and not dataset.has_pending_frames():
            state["decided"] = "d"  # B/C before any frame was recorded: LeRobot can't save that, so discard it
            events["rerecord_episode"] = True
        if state["decided"] == "d":  # cancelled: not saved, not labelled, not counted
            state.update(phase="cancelled", last="d", started=None)
            return
        passed = state["decided"] == "b"  # C, or the time limit with no B or C, is a fail
        if passed:
            state["passed"] += 1
        else:
            state["failed"] += 1
            state["failed_episodes"].append(index)
        state.update(phase="passed" if passed else "failed", last=state["decided"] or "timeout", started=None)
        if passed and state["target"] and state["passed"] >= state["target"]:
            events["stop_recording"] = True  # enough passes: LeRobot saves this one, then uploads
    with labels.open("a") as f:
        if f.tell() == 0:
            f.write("episode_index,result\n")
        f.write(f"{index},{'pass' if passed else 'fail'}\n")


def prepare_dataset_folder(root):
    """Return the extra flag that makes a rerun of the same command work."""
    info = Path(root) / "meta" / "info.json"
    if not info.exists():
        return []
    if json.loads(info.read_text())["total_episodes"] == 0:
        shutil.rmtree(root)  # left by a run stopped before its first save; it holds no episodes
        return []
    return ["--resume=true", f"--dataset.root={root}"]  # continue the same dataset (resume needs the folder)


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body=b"{}", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def snapshot(self):
        started = state["started"]
        s = dict(state, elapsed=time.monotonic() - started if started else 0)
        del s["started"]
        return json.dumps(s).encode()

    def do_GET(self):
        if self.headers.get("Host") not in HOSTS:
            return self.send(403)
        if self.path == "/":
            self.send(200, PAGE, "text/html; charset=utf-8")
        elif self.path == "/state":
            self.send(200, self.snapshot())
        elif self.path.removeprefix("/cam/") in cameras:
            self.stream(cameras[self.path.removeprefix("/cam/")])
        else:
            self.send(404)

    def stream(self, camera):
        """MJPEG video of one camera, using the frames LeRobot already captures."""
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        while state["phase"] not in ("done", "error"):
            try:
                frame = camera.read_latest(max_age_ms=1000)
            except Exception:  # camera starting, stalled or closed: keep showing the last picture
                time.sleep(0.2)
                continue
            jpg = cv2.imencode(".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 70])[1]
            try:
                self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(jpg))
                self.wfile.write(jpg.tobytes() + b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                return  # page closed
            time.sleep(1 / 15)  # preview rate; recording still runs at 30 fps

    def do_POST(self):
        # Only this page may press keys: blocks other websites and DNS-rebinding tricks.
        origin = self.headers.get("Origin")
        if (self.path != "/key" or self.headers.get("Host") not in HOSTS
                or (origin and origin.removeprefix("http://") not in HOSTS)):
            return self.send(403)
        try:
            key = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 100)))["key"]
        except (ValueError, KeyError, TypeError):
            return self.send(400)
        if key not in ("a", "b", "c", "d"):
            return self.send(400)
        press(key)
        self.send(200, self.snapshot())

    def log_message(self, *args):
        pass


def serve(port=PORT):
    """Start the page server; port 0 picks a free port (self-test). Returns the page URL."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    port = server.server_address[1]
    HOSTS.update({f"127.0.0.1:{port}", f"localhost:{port}"})
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}"


def run(record):
    try:
        record()
        state["phase"] = "done"
    except Exception as e:
        state.update(phase="error", error=f"{type(e).__name__}: {e}")
        raise
    finally:  # also on Ctrl+C
        if current:
            saved = current["dataset"].num_episodes  # an episode cut off mid-save isn't counted
            passed, failed = saved_labels(current["labels"], saved)
            print(f"\nThe dataset has {saved} episodes: {passed} passed, {len(failed)} failed. "
                  f"Results are in {LABELS} in its folder.")
            if failed:
                print(f'To train on passes only, add: --dataset.exclude_episodes="{failed}"')
        time.sleep(3)  # let the page show the final state before the server closes


class FakeDataset:
    """Enough of LeRobotDataset for record_loop(): a frame counter, a save counter and an upload hook."""
    def __init__(self, root, saved=0, push_to_hub=lambda: None):
        self.num_episodes, self.root, self.frames, self.push_to_hub = saved, root, 0, push_to_hub

    def has_pending_frames(self):
        return self.frames > 0


class FakeCamera:
    def read_latest(self, max_age_ms=500):
        frame = np.full((480, 640, 3), 40, np.uint8)
        cv2.putText(frame, time.strftime("%H:%M:%S"), (190, 255), cv2.FONT_HERSHEY_SIMPLEX, 2, (200, 200, 200), 3)
        return frame


def fake_record_loop(events, control_time_s, dataset=None, **_):
    end = time.monotonic() + control_time_s
    while time.monotonic() < end:
        if events["exit_early"]:  # checked before the frame, as in LeRobot
            events["exit_early"] = False
            return
        if dataset:
            dataset.frames += 1
        time.sleep(0.01)


def fake_record(root, limit, saved=0):
    """The episode loop of lerobot_record.record() (lines 500-553), without a robot."""
    robot = SimpleNamespace(cameras={"wrist": FakeCamera(), "top": FakeCamera()})
    dataset = FakeDataset(root, saved)
    while not events["stop_recording"]:
        record_loop(robot=robot, dataset=dataset, events=events, control_time_s=limit,
                    single_task="Put the tools on the table into the toolbox")
        record_loop(robot=robot, dataset=None, events=events, control_time_s=0)  # reset phase
        if events["rerecord_episode"]:  # clear_episode_buffer, then record the same episode again
            events.update(rerecord_episode=False, exit_early=False)
            dataset.frames = 0
            continue
        dataset.num_episodes += 1  # save_episode
        dataset.frames = 0


def selftest():
    global orig_record_loop
    orig_record_loop = fake_record_loop
    base = serve(0)
    state["target"] = 3
    tmp = Path(tempfile.mkdtemp())
    threading.Thread(target=run, args=(lambda: fake_record(tmp, 0.5),), daemon=True).start()

    def post(key, origin=base):
        req = urllib.request.Request(f"{base}/key", json.dumps({"key": key}).encode(),
                                     {"Origin": origin, "Content-Type": "application/json"})
        try:
            return urllib.request.urlopen(req).status
        except urllib.error.HTTPError as e:
            return e.code

    def until(phase):
        for _ in range(300):
            if state["phase"] == phase:
                return
            time.sleep(0.01)
        raise AssertionError(f"expected {phase}, got {state['phase']}")

    def start():  # A, then wait until a frame exists, so B/C is a real result
        post("a"); until("recording")
        while not current["dataset"].has_pending_frames():
            time.sleep(0.01)

    assert urllib.request.urlopen(base).status == 200
    until("ready")
    with urllib.request.urlopen(f"{base}/cam/wrist") as video:
        assert video.headers["Content-Type"].startswith("multipart/x-mixed-replace")
        assert b"\xff\xd8" in video.read(4096)  # a JPEG frame arrives
    try:
        urllib.request.urlopen(f"{base}/cam/nope")
        raise AssertionError("unknown camera should be 404")
    except urllib.error.HTTPError as e:
        assert e.code == 404
    assert post("b") == 200 and state["phase"] == "ready"  # B before A is ignored
    assert post("a", origin="http://evil.example") == 403 and state["phase"] == "ready"
    assert post("x") == 400
    start()
    post("c"); until("ready")  # episode 0: failed, and kept
    assert (state["passed"], state["failed"], state["last"]) == (0, 1, "c")
    start()
    post("d"); until("ready")  # cancelled: nothing saved, episode 1 is recorded again
    assert (state["passed"], state["failed"], state["last"]) == (0, 1, "d")
    assert post("d") == 200 and state["phase"] == "ready"  # D outside recording is ignored
    for key in "dbc" * 7:  # a key right after A, before the waiting loop has noticed A or any frame exists
        t = time.monotonic(); press("a"); press(key); until("ready")
        assert time.monotonic() - t < 0.3  # not left recording until the 0.5 s limit
        assert (state["passed"], state["failed"], state["last"]) == (0, 1, "d")  # discarded, not saved or counted
    start()
    post("b"); until("ready")  # episode 1: passed
    assert (state["passed"], state["failed"], state["last"]) == (1, 1, "b")
    start(); until("ready")  # episode 2: no B or C before the 0.5 s limit
    assert (state["passed"], state["failed"], state["last"]) == (1, 2, "timeout")
    for _ in range(2):  # episodes 3 and 4: passes; the third pass ends the session
        until("ready"); start(); post("b")
    until("done")
    assert (state["passed"], state["failed"], state["failed_episodes"]) == (3, 2, [0, 2])
    assert (tmp / LABELS).read_text() == "episode_index,result\n0,fail\n1,pass\n2,fail\n3,pass\n4,pass\n"

    # Rerunning the same command: an empty folder is removed, a folder with episodes is continued.
    for total, kept in ((0, False), (2, True)):
        root = tmp / f"ds{total}"
        (root / "meta").mkdir(parents=True)
        (root / "meta" / "info.json").write_text(json.dumps({"total_episodes": total}))
        extra = ["--resume=true", f"--dataset.root={root}"] if total else []
        assert prepare_dataset_folder(root) == extra and root.exists() == kept
    assert prepare_dataset_folder(tmp / "missing") == []

    # A resumed session counts earlier passes: 3 of 4 already done, so one more pass finishes it.
    def session(target, saved):
        events.update(exit_early=False, rerecord_episode=False, stop_recording=False)
        state.update(phase="connecting", passed=0, failed=0, failed_episodes=[], target=target, decided=None, last=None)
        current.clear()
        threading.Thread(target=run, args=(lambda: fake_record(tmp, 0.5, saved),), daemon=True).start()
    session(4, 5)
    until("ready")
    assert (state["passed"], state["failed"], state["failed_episodes"]) == (3, 2, [0, 2])
    start(); post("b"); until("done")
    assert (state["passed"], state["failed"]) == (4, 2) and (tmp / LABELS).read_text().endswith("4,pass\n5,pass\n")
    # Already at the target: it finishes without recording anything.
    session(4, 6)
    until("done")
    assert (tmp / LABELS).read_text().count("\n") == 7  # header + 6 rows, nothing added

    # A label written for an episode whose save was cut off is dropped when the next session starts.
    labels = tmp / "stale.csv"
    labels.write_text("episode_index,result\n0,pass\n1,fail\n2,fail\n")
    assert saved_labels(labels, 2) == (1, [1])
    assert labels.read_text() == "episode_index,result\n0,pass\n1,fail\n"
    # An upload after a cut-off save must not carry the label of the unsaved episode.
    sent = []
    (tmp / LABELS).write_text("episode_index,result\n0,pass\n")
    cut = FakeDataset(tmp, 2, lambda: sent.append((tmp / LABELS).read_text()))
    current.clear()
    state.update(target=1)  # one pass already saved, so record_loop returns right after installing the upload fix
    record_loop(robot=SimpleNamespace(cameras={}), dataset=cut, events=events, control_time_s=1)
    with (tmp / LABELS).open("a") as f:
        f.write("1,fail\n2,pass\n")  # episode 2 is written, but its save was cut off
    cut.push_to_hub()
    assert sent == ["episode_index,result\n0,pass\n1,fail\n"]
    shutil.rmtree(tmp)
    print("selftest OK")


def main():
    global orig_record_loop
    args = sys.argv[1:]
    if args == ["--selftest"]:
        return selftest()

    def flag(name):
        return next((a.split("=", 1)[1] for a in args if a.startswith(f"--dataset.{name}=")), None)

    state.update(target=int(flag("num_episodes") or 0) or None, repo=flag("repo_id"))
    if args == ["--demo"]:
        orig_record_loop = fake_record_loop
        state.update(target=3, repo="demo, nothing is recorded")
        url = serve()
        print(f"Recorder page: {url}")
        webbrowser.open(url)
        with tempfile.TemporaryDirectory() as tmp:
            return run(lambda: fake_record(tmp, 30))

    from lerobot.scripts import lerobot_record
    from lerobot.utils.constants import HF_LEROBOT_HOME

    if not any(a.startswith("--resume") for a in args) and flag("repo_id"):
        sys.argv += prepare_dataset_folder(Path(flag("root") or HF_LEROBOT_HOME / flag("repo_id")))
    if state["target"]:
        sys.argv.append("--dataset.num_episodes=1000000")  # LeRobot's cap; the page stops after `target` passes
    sys.argv.append("--play_sounds=false")  # LeRobot's spoken cues would be out of step with A/B/C
    orig_record_loop = lerobot_record.record_loop
    lerobot_record.record_loop = record_loop
    lerobot_record.init_keyboard_listener = lambda: (None, events)
    url = serve()
    print(f"Recorder page: {url}  (keys work while that window is in front)")
    webbrowser.open(url)
    run(lerobot_record.main)


if __name__ == "__main__":
    main()
