#!/usr/bin/env python
"""Annotated review of recorded trials: key moments drawn onto the camera frames.

For each trial it finds, from the joint data:
  PICK     the gripper was told to close but a tool held it open (green)
  RELEASE  the gripper let go of that tool (blue)
  STUCK    6 s or more with no pick while the arm stayed in a small region (red)
  MARK     moments the operator marked with M on the eval page (yellow)
and saves one image per trial (overhead | wrist at each moment, labelled) plus review.md
with the numbers and a "Notes" line per trial, in media/private/reviews/<run>/.
The drawings are for people: never write them back into a training dataset.

    python tools/review_trials.py <repo_id>            # e.g. $HF_USER/rollout_so101_tools_toolbox_<timestamp>
    python tools/review_trials.py --selftest
"""

import csv
import sys
from pathlib import Path

import cv2
import numpy as np

FPS = 30
COLORS = {"START": (150, 150, 150), "PICK": (60, 200, 90), "RELEASE": (70, 140, 255), "STUCK": (230, 60, 50),
          "MARK": (250, 210, 40), "END": (150, 150, 150)}  # RGB


def find_events(action, state, marks=()):
    """Events (frame, kind, detail) from one trial's action and state arrays (frames x 6, degrees; gripper 0-100)."""
    held = (action[:, 5] < 8) & (state[:, 5] - action[:, 5] > 4)  # a tool keeps the jaws apart
    events, start = [(0, "START", "")], None
    for i, h in enumerate(np.append(held, False)):
        if h and start is None:
            start = i
        elif not h and start is not None:
            if i - start >= 15:  # held for at least 0.5 s
                events += [(start, "PICK", ""), (i - 1, "RELEASE", f"held {(i - start) / FPS:.1f} s")]
            start = None
    events.append((len(state) - 1, "END", ""))
    # Stuck: 12 s or more empty-handed (from the start or a release to the next pick or the end).
    # In the 50 demos 95% of such stretches were 8 s or less and 7 of 259 reached 12 s.
    edges = [f for f, k, _ in events if k in ("START", "RELEASE", "PICK", "END")]
    kinds = [k for f, k, _ in events if k in ("START", "RELEASE", "PICK", "END")]
    for f0, k0, f1 in zip(edges, kinds, edges[1:]):
        if k0 in ("START", "RELEASE") and f1 - f0 >= 12 * FPS:
            events.append(((f0 + f1) // 2, "STUCK", f"no pick for {(f1 - f0) / FPS:.0f} s"))
    events += [(min(int(m * FPS), len(state) - 1), "MARK", "") for m in marks]
    return sorted(events)


def summary(events, action):
    closed = action[:, 5] < 10
    return {"picks": sum(k == "PICK" for _, k, _ in events),
            "stuck_s": sum(float(d.split()[-2]) for _, k, d in events if k == "STUCK"),
            "gripper_closes": int((closed[1:] & ~closed[:-1]).sum())}


def tile(top, wrist, t, kind, detail):
    """One labelled moment: overhead | wrist with a coloured border and a caption."""
    img = np.concatenate([top, wrist], 1).copy()
    color = COLORS[kind]
    cv2.rectangle(img, (0, 0), (img.shape[1] - 1, img.shape[0] - 1), color, 10)
    cv2.rectangle(img, (0, 0), (img.shape[1], 44), color, -1)
    cv2.putText(img, f"{t:5.1f} s  {kind} {detail}", (14, 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    return img


def labels_for(root):
    path = Path(root) / "trial_labels.csv"
    return {int(r["episode_index"]): r for r in csv.DictReader(path.open())} if path.exists() else {}


def review(repo_id):
    import torch
    from lerobot.datasets.lerobot_dataset import LeRobotDataset

    ds = LeRobotDataset(repo_id)
    out = Path(__file__).resolve().parent.parent / "media" / "private" / "reviews" / repo_id.split("/")[-1]
    out.mkdir(parents=True, exist_ok=True)
    labels, eps = labels_for(ds.root), ds.meta.episodes
    lines = [f"# Review: {repo_id}", "", "| Trial | Result | In box | Picks | Stuck | Gripper closes |", "|---|---|---|---|---|---|"]
    notes = []
    for ep in range(ds.meta.total_episodes):
        a, b = eps["dataset_from_index"][ep], eps["dataset_to_index"][ep]
        rows = ds.hf_dataset[a:b]
        action, state = torch.stack(list(rows["action"])).numpy(), torch.stack(list(rows["observation.state"])).numpy()
        lab = labels.get(ep, {})
        marks = [float(m) for m in (lab.get("marks") or "").split(";") if m]
        events = find_events(action, state, marks)
        s = summary(events, action)
        tiles = []
        shown = [e for e in events if e[1] != "END"][:11] + [e for e in events if e[1] == "END"]  # always keep the final frame
        for f, kind, detail in shown:
            it = ds[a + f]
            img = lambda k: (it[f"observation.images.{k}"].permute(1, 2, 0).numpy() * 255).astype(np.uint8)
            tiles.append(tile(img("top"), img("wrist"), f / FPS, kind, detail))
        while len(tiles) % 3:
            tiles.append(np.zeros_like(tiles[0]))
        sheet = np.concatenate([np.concatenate(tiles[k:k + 3], 1) for k in range(0, len(tiles), 3)], 0)
        cv2.imwrite(str(out / f"trial_{ep:02d}.jpg"), cv2.cvtColor(cv2.resize(sheet, None, fx=0.5, fy=0.5), cv2.COLOR_RGB2BGR))
        lines.append(f"| {ep} | {lab.get('result', '?')} | {lab.get('tools_in_box') or '?'} | {s['picks']} | "
                     f"{s['stuck_s']:.0f} s | {s['gripper_closes']} |")
        notes += ["", f"## Trial {ep}", "", f"![trial {ep}](trial_{ep:02d}.jpg)", "",
                  "Events: " + ", ".join(f"{f / FPS:.1f} s {k.lower()}{' ' + d if d else ''}" for f, k, d in events), "",
                  "Notes: "]
    md = out / "review.md"
    if md.exists():  # it may hold written notes: never overwrite them
        md = out / "review.new.md"
    md.write_text("\n".join(lines + notes) + "\n")
    print(f"Review written to {md}")


def selftest():
    n = 30 * FPS
    action, state = np.zeros((n, 6)), np.zeros((n, 6))
    action[:, 5] = state[:, 5] = 20  # gripper open
    state[:, :5] = np.linspace(0, 200, n)[:, None]  # the arm keeps moving
    action[300:330, 5] = 0; state[300:330, 5] = 12  # a 1 s pick: told to close, held open by a tool
    action[600:610, 5] = 0; state[600:610, 5] = 0  # closing on nothing: not a pick
    ev = find_events(action, state, marks=[5.0])
    kinds = [(f, k) for f, k, _ in ev]
    assert (300, "PICK") in kinds and (329, "RELEASE") in kinds and (150, "MARK") in kinds, kinds
    assert sum(k == "PICK" for _, k in kinds) == 1  # the empty close isn't counted
    stuck = [(f, d) for f, k, d in ev if k == "STUCK"]
    assert stuck == [(614, "no pick for 19 s")], stuck  # release at 329 to the end at 899; the first 10 s is too short
    s = summary(ev, action)
    assert s["picks"] == 1 and s["gripper_closes"] == 2 and s["stuck_s"] == 19
    assert tile(np.zeros((480, 640, 3), np.uint8), np.zeros((480, 640, 3), np.uint8), 1.0, "PICK", "").shape == (480, 1280, 3)
    print("selftest OK")


if __name__ == "__main__":
    selftest() if sys.argv[1:] == ["--selftest"] else review(sys.argv[1])
