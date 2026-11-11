<h1 align="center">SO-101 → π0.5: a robot arm that tidies tools</h1>

<p align="center">
  Two 3D-printed robot arms. One learns to put tools in a toolbox.<br>
  <b>First full run on its own: four tools, no help.</b>
</p>

<p align="center">
  <img src="media/2026-11-10-first-pass.gif" width="640" alt="Animated: overhead and wrist camera views as the arm puts three bit strips and a screwdriver into the toolbox on its own; a label bar counts the tools in the box up to 4 of 4"><br>
  <sub>Sped up 3×, pauses between moves cut. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-10-first-pass.mp4">MP4 at real speed</a></sub>
</p>

<p align="center">
  <a href="#status">Status</a> ·
  <a href="#first-results">Results</a> ·
  <a href="#recording-demonstrations">Recording</a> ·
  <a href="#problems-solved">Problems solved</a> ·
  <a href="#the-build">Build</a> ·
  <a href="BUILD_LOG.md">Build log</a> ·
  <a href="RUNBOOK.md">Runbook</a>
</p>

## In short

- ***Built:*** two [SO-101](https://github.com/TheRobotStudio/SO-ARM100) arms (a leader moved by hand, a follower that copies it) and two cameras.
- ***Taught:*** 50 demonstrations, then fine-tuned [π0.5](https://www.physicalintelligence.company/blog/pi05) with [Hugging Face LeRobot](https://github.com/huggingface/lerobot).
- ***Result:*** <ins>**about half the tools into the box, one full pass.**</ins>

## Status

Updated November 10, 2026.

| Step | Status |
| --- | --- |
| Print, wire and assemble both arms | ✅ Done |
| Calibrate and teleoperate | ✅ Done |
| Wrist and overhead cameras | ✅ Done |
| Recording tool | ✅ Done |
| 50 demonstrations | ✅ Done |
| Fine-tune π0.5 | ✅ Done |
| Run on the arm | ✅ First full pass |
| Scoring and review tools | ✅ Done |
| More data where it fails | 🔄 Next |
| Retrain, score 20 trials | ⏳ After that |

> [!NOTE]
> The wrist camera still drops off USB at times, and macOS can then swap the two cameras' numbers. The tools detect this and fix it before the arm moves.

## First results

<ins>**11 of 20 tools in the box over 5 trials, including one full pass.**</ins> Not reliable yet. Every failure is recorded and reviewed.

<table>
  <tr>
    <th width="50%">Scoring page</th>
    <th width="50%">Annotated review</th>
  </tr>
  <tr>
    <td align="center"><img src="media/2026-11-10-eval-page.jpg" width="100%" alt="The eval page during a trial: timer, Pass, Fail, Go home and Mark keys, and both camera feeds"></td>
    <td align="center"><img src="media/2026-11-10-annotated-review-pass.jpg" width="100%" alt="Annotated review of the full pass: frames at each pick, release and pause, labelled with times"></td>
  </tr>
  <tr>
    <td><sub><b>A</b> start · <b>B</b> pass · <b>C</b> fail + tool count · <b>D</b> go home · <b>M</b> mark a moment. The arm resets after every trial. <a href="tools/eval_ui.py">Code</a></sub></td>
    <td><sub>Every pick, release and long pause marked on the frames, from the gripper's readings. <a href="tools/review_trials.py">Code</a></sub></td>
  </tr>
  <tr>
    <th>Where it fails</th>
    <th>The bug that made it look blind</th>
  </tr>
  <tr>
    <td align="center"><img src="media/2026-11-10-coverage-map.jpg" width="100%" alt="Overhead view: white dots where tools sat in the demos, green circles for tools the model got into the box, red circles for tools it left; nothing on the right side went in"></td>
    <td align="center"><img src="media/2026-11-10-camera-swap.jpg" width="100%" alt="Training data with the overhead and wrist views in their slots, above an eval run where the two views had swapped slots"></td>
  </tr>
  <tr>
    <td><sub>White = demo tool spots · green = put in the box · red = left behind. <b>Only 8% of demo spots were on the right; nothing from there went in.</b></sub></td>
    <td><sub>For 21 trials the two camera views were swapped. macOS renumbered the identical cameras after a USB dropout.</sub></td>
  </tr>
</table>

### The full pass, raw

<ins>**Trial 2 of 5, 3,500-step checkpoint: all four tools in the box at 40.9 s.**</ins>

- 🎥 ***[Raw video](https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-10-first-pass-raw.mp4)***: overhead and wrist cameras exactly as the robot saw them, real speed, no edits or labels.
- 📈 ***[Joint data (CSV)](media/2026-11-10-first-pass-joints.csv)***: all six joints, measured and commanded, 30 times per second (1,229 rows).

<p align="center"><img src="media/2026-11-10-first-pass-joints.png" width="720" alt="Joint angles over the 41-second full pass. Top: shoulder, elbow and wrist angles as the arm reaches and returns. Bottom: gripper measured and commanded; four flat stretches where the measured gripper stays open above the command are the four tools being held."></p>
<p align="center"><sub><b>Bottom chart:</b> where the black line stays above the orange one, the gripper is closed on a tool. <b><i>Four holds = four tools.</i></b></sub></p>

***Next:*** record data for the spots it misses, then retrain. Details in the [build log](BUILD_LOG.md#november-10-first-runs-on-the-arm-and-finding-out-why-it-fails).

## Recording demonstrations

<table>
  <tr>
    <th width="24%">Teleoperating a demo</th>
    <th width="52%">The recording page</th>
    <th width="24%">First replay</th>
  </tr>
  <tr>
    <td align="center"><img src="media/2026-11-08-data-collection.gif" height="240" alt="Animated: the follower arm, driven from the leader, picks up a bit strip and puts it into the open toolbox"></td>
    <td align="center"><img src="media/2026-11-08-recording-page.gif" height="240" alt="Animated: the recording page cancels an episode, records one with a red timer bar, then saves it as passed"></td>
    <td align="center"><img src="media/2026-11-08-first-replay.gif" height="240" alt="Animated: the follower arm moves through a recorded episode by itself"></td>
  </tr>
  <tr>
    <td><sub>The follower copies the leader. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-data-collection.mp4">MP4</a></sub></td>
    <td><sub>Sped up 2×. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-recording-page.mp4">MP4</a></sub></td>
    <td><sub>Replay only repeats motions; no cameras. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-first-replay.mp4">MP4</a></sub></td>
  </tr>
</table>

A small [recording page](tools/record_ui.py) replaces LeRobot's keyboard shortcuts: ***one key starts a take, others mark pass, fail or redo***. It resumes where it left off. Commands: [runbook](RUNBOOK.md#4-record-demonstrations).

## Problems solved

Full story in the [build log](BUILD_LOG.md).

- **21 failed trials: <ins>cameras swapped, not a bad model.</ins>** After a USB dropout macOS swapped the two identical cameras. The pages now compare the feeds (only the overhead sees the wall) and fix the order.
- **Indecisive arm: <ins>smooth mode replanned too often.</ins>** Real-time mode switched targets every ~0.7 s. Plain mode commits for 1.7 s: ***0 → 5 of 20 tools.***
- **More training was worse: <ins>overfitting and a data gap.</ins>** Halfway checkpoint 11 of 20, final 6 of 20. Only 8% of demo tool spots were on the right.
- **Wrist camera cutouts: <ins>a cable, not bandwidth.</ins>** The macOS log showed ~200 physical disconnects in one evening, on that camera only.
- **Cloud model wouldn't load: <ins>version mismatch.</ins>** A cheap test job caught renamed weights in a newer LeRobot. Pinning the cloud to the Mac's versions fixed it.
- **Arms didn't line up: <ins>uneven calibration sweeps.</ins>** A joint's zero is the middle of its swept range. Matching the sweeps cut the gap from ~7° to under 0.5°.
- **Startup lurch: <ins>motors on before a target was set.</ins>** Fixed the order; tests reproduce the bug first.
- **Data checked before training.** Caught a hand and a laptop screen in view, and a frame bug in the review script.

## The build

<table>
  <tr>
    <th>Printing</th>
    <th>Motor bring-up</th>
    <th>Assembly</th>
    <th>Camera stand</th>
  </tr>
  <tr>
    <td align="center"><img src="media/2026-10-12-printing-parts.jpg" height="220" alt="Bambu P1S print bed with SO-101 arm parts"></td>
    <td align="center"><img src="media/2026-10-12-motor-setup-bench.jpg" height="220" alt="Servo boxes, printed parts and the servo controller board on a desk"></td>
    <td align="center"><img src="media/2026-10-15-shoulder-assembly.jpg" height="220" alt="SO-101 shoulder joint and upper arm on its base"></td>
    <td align="center"><img src="media/2026-11-08-camera-stand.jpg" height="220" alt="Printed overhead camera tower with a camera board on top, next to the follower arm"></td>
  </tr>
</table>

<table>
  <tr>
    <th>First teleoperation</th>
    <th>Overhead camera</th>
    <th>Wrist camera</th>
  </tr>
  <tr>
    <td align="center"><img src="media/2026-10-19-first-teleop.gif" height="160" alt="Animated: leader and follower arms on a desk; the follower copies the leader's motion"></td>
    <td align="center"><img src="media/2026-11-08-robot-view-overhead.jpg" height="160" alt="Overhead camera view of the desk"></td>
    <td align="center"><img src="media/2026-11-08-robot-view-wrist.jpg" height="160" alt="Wrist camera view showing the gripper jaws"></td>
  </tr>
</table>

| Part | Used |
| --- | --- |
| Arms | Two SO-101s in PLA+: leader (by hand) and follower |
| Motors | 12 Feetech STS3215 servos |
| Controllers | 2 Waveshare servo boards |
| Cameras | 2 small USB cameras: wrist and overhead |
| Software | LeRobot on a MacBook Pro (M3 Max), plus custom [recording, scoring and review tools](tools/) |

## How it learns

1. ***Show:*** steer the follower with the leader.
2. ***Record:*** both camera videos, joint angles, pass or fail.
3. ***Train:*** fine-tune π0.5 on the passes, in the cloud.
4. ***Run:*** the model drives the arm from the Mac.
5. ***Score:*** [eval page](tools/eval_ui.py) for results, [review tool](tools/review_trials.py) for every pick, drop and stall.
6. ***Repeat:*** more data where it fails, retrain, publish results, failures included.

Every command: [runbook](RUNBOOK.md).

## Credits

Arm design: [TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100). π0.5: [Physical Intelligence](https://github.com/Physical-Intelligence/openpi). Robot software: [Hugging Face LeRobot](https://github.com/huggingface/lerobot). Claude Code helped read the LeRobot source, write diagnostic scripts and keep notes. Build and hands-on testing by Jaxson Bie.
