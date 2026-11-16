<h1 align="center">SO-101 → π0.5: a robot arm that tidies tools</h1>

<p align="center">
  Two robot arms built from scratch, then taught to put tools away with Physical Intelligence's π0.5.<br>
  <b>Built, wired, calibrated, debugged and tested by Jaxson Bie in six weeks.</b>
</p>

<p align="center">
  <img src="media/2026-11-10-first-pass.gif" width="640" alt="Animated: overhead and wrist camera views as the arm puts three bit strips and a screwdriver into the toolbox on its own; a label bar counts the tools in the box up to 4 of 4"><br>
  <sub><b>The arm on its own: all four tools in the box in 41 seconds, no help.</b> Sped up 3×. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-10-first-pass.mp4">MP4 at real speed</a> · <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-10-first-pass-raw.mp4">raw video</a> · <a href="media/2026-11-10-first-pass-joints.csv">joint data</a></sub>
</p>

<p align="center">
  <a href="REPORT.md"><b>Full project report</b></a> ·
  <a href="#highlights">Highlights</a> ·
  <a href="#problems-found-and-fixed">Problems fixed</a> ·
  <a href="#results">Results</a> ·
  <a href="#test-tools-built-for-the-job">Test tools</a> ·
  <a href="#the-build">Build</a> ·
  <a href="BUILD_LOG.md">Build log</a> ·
  <a href="RUNBOOK.md">Runbook</a>
</p>

## Highlights

- **Built two robot arms from parts.** Printed every piece, set up all 12 servos one at a time, wired both arms, and calibrated the pair to <ins>**under 0.5° apart**</ins>.
- **Brought up a full robot learning system.** Teleoperation at 60 Hz, two cameras, 153 recorded demonstrations, π0.5 fine-tuned on a cloud GPU, and the model driving the arm live from a MacBook.
- **The arm did the whole task on its own:** <ins>**all four tools into the toolbox**</ins>, then <ins>**3 full passes**</ins> on a 20-layout test after retraining.
- **Tracked down 36 problems** across mechanical, electrical, software and data, each traced to its root cause and written up in the [report](REPORT.md#7-fault-log).
- **Built the test tools the job needed:** a recording page, a scoring page, and a review tool that marks every pick, drop and pause on the video.
- **Tested it like a fleet robot:** the same 20 layouts and the same rules for every model, every trial recorded and reviewed.
- **Fixed a motor-safety bug in LeRobot:** motors switched on before they had a target. Reproduced it in tests first, then fixed it ([patch](patches/lerobot-so101-startup-shutdown.patch)).

## Problems found and fixed

The work that took the most care was finding out *why* something failed before changing anything. A few examples:

- **A camera that kept cutting out.** The obvious theory was USB bandwidth. The macOS system log showed the wrist camera physically disconnecting 193 times in one evening, and swapping hub sockets proved the fault followed the camera. <ins>**Isolated to the camera's cable**</ins> instead of rewriting code that wasn't broken.
- **21 failed trials that weren't the model's fault.** The recordings showed the two identical cameras had swapped places after a USB reconnect. The recording and scoring pages now <ins>**check which camera is which before the arm moves**</ins>.
- **A robot that jumped on startup.** Traced to LeRobot switching torque on before giving the motors a target. <ins>**Fixed and covered by tests.**</ins>
- **Arms 7° apart after calibration.** LeRobot's source showed a joint's zero is the middle of its calibration sweep. Matching the sweeps brought the arms to <ins>**under 0.5°**</ins>.
- **A model the robot couldn't load.** A test run that cost about a dollar showed the cloud software had changed versions that day. Pinning versions <ins>**caught it before paying for a full training run**</ins>.
- **27 recordings with mixed-up cameras.** A check on every episode found them, and they were <ins>**repaired without re-recording**</ins>.

<p align="center"><img src="media/2026-11-10-camera-swap.jpg" width="560" alt="Top row: the training data, overhead view in the top slot and gripper view in the wrist slot. Bottom row: an eval run where the two views had swapped slots"></p>
<p align="center"><sub>Top: what the model was trained on. Bottom: what it saw before the fix. The camera check now catches this automatically.</sub></p>

All 36, with how each was found: [report, fault log](REPORT.md#7-fault-log).

## Results

**First model, 50 demonstrations:** the first full pass, and 11 of 20 tools in the box over five trials with the best checkpoint.

**Finding what to fix next:** mapping every trial showed the model never solved the right side of the table, because only 8% of the demonstrations had tools there.

<p align="center"><img src="media/2026-11-11-coverage-before-after.jpg" width="680" alt="Tool start positions on the table. Before: 50 demos, 8 percent right of the box, dense on the left. Now: 120 demos, 40 percent right of the box, with the left side still covered."></p>
<p align="center"><sub>103 new demonstrations, every one checked: <b>8% → 40%</b> of tools right of the box.</sub></p>

**Retrained on 120 checked demonstrations:** the right side went from <ins>**no tools at all to the best zone**</ins>, and the model made <ins>**3 full passes**</ins> on 20 fixed layouts.

<p align="center"><img src="media/2026-11-12-layouts-results.jpg" width="760" alt="The 20 test layouts, as each trial's first overhead frame, labelled with the zone and the tools that ended in the box. Layouts 2, 9 and 10 are passes, in green."></p>
<p align="center"><sub>Every model gets the same 20 layouts in the same order. Each trial's first frame doubles as the layout photo.</sub></p>

| Zone | Tools in the box |
| --- | --- |
| **Right** (the first model's blind spot) | **14 / 20** |
| Left and front | 10 / 20 |
| Far left | 8 / 16 |
| Mixed and hard | 10 / 24 |

**Next step:** the reviews pinned down the one skill left to teach, finishing a grasp. The plan is correction data recorded right at those moments. More in the [report](REPORT.md#11-potential-next-steps).

### The full pass, raw

- ***[Raw video](https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-10-first-pass-raw.mp4)***: both cameras exactly as the robot saw them, real speed, no edits.
- ***[Joint data (CSV)](media/2026-11-10-first-pass-joints.csv)***: all six joints, measured and commanded, 30 times a second.

<p align="center"><img src="media/2026-11-10-first-pass-joints.png" width="720" alt="Joint angles over the 41-second full pass. Top: shoulder, elbow and wrist angles as the arm reaches and returns. Bottom: gripper measured and commanded; four flat stretches where the measured gripper stays open above the command are the four tools being held."></p>
<p align="center"><sub>Bottom chart: where the black line stays above the orange one, the gripper is holding a tool. <b>Four holds, four tools.</b></sub></p>

## Test tools built for the job

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
    <td><sub>One key each to start, pass, fail with a tool count, send the arm home, or mark a moment. The arm resets itself after every trial. <a href="tools/eval_ui.py">Code</a></sub></td>
    <td><sub>Every pick, release and pause marked on the frames, worked out from the gripper's readings. <a href="tools/review_trials.py">Code</a></sub></td>
  </tr>
</table>

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
    <td><sub>One key starts a take, others mark pass, fail or redo. Sped up 2×. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-recording-page.mp4">MP4</a></sub></td>
    <td><sub>The follower replaying a recorded take. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-first-replay.mp4">MP4</a></sub></td>
  </tr>
</table>

### Every episode checked before training

Training runs on a rented cloud GPU, so every episode was checked first: every frame, the joint data, and a look at each one, against limits taken from the best demonstrations.

<table>
  <tr>
    <th width="50%">Every new episode against the limits</th>
    <th width="50%">Telling a thin grasp from a miss</th>
  </tr>
  <tr>
    <td align="center"><img src="media/2026-11-11-qa-limits.png" width="100%" alt="Scatter of 103 new episodes, longest hover against longest stretch with no tool: 83 kept inside both limits, 5 over a limit, 15 failed another check"></td>
    <td align="center"><img src="media/2026-11-11-gripper-strip-vs-miss.png" width="100%" alt="Gripper opening over one episode: about 7 holding the screwdriver, about 4.4 holding a strip by its edge, about 2 closed on nothing"></td>
  </tr>
  <tr>
    <td><sub><b>83 of 103 kept.</b> The rest hovered, searched, grabbed two tools at once or broke the routine.</sub></td>
    <td><sub>A strip held by its edge reads almost like an empty gripper, so grasps are counted by <b>arm travel</b>, not jaw opening.</sub></td>
  </tr>
</table>

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
| Arms | Two SO-101s in PLA+: a leader moved by hand and a follower that copies it |
| Printing | Bambu Lab P1S; small STL fit edits in Bambu Studio and Blender |
| Motors | 12 Feetech STS3215 servos in three gear ratios |
| Controllers | 2 Waveshare servo boards |
| Cameras | 2 USB cameras: wrist and overhead |
| Software | LeRobot on a MacBook Pro (M3 Max), plus custom [recording, scoring and review tools](tools/) |
| Redesigned parts | Controller mount holes and the leader's handle slot, refit for printed tolerances: [hardware/](hardware/) |

## How it learns

1. ***Show:*** steer the follower with the leader.
2. ***Record:*** both camera videos, joint angles, pass or fail.
3. ***Check:*** every episode against limits from the best demos.
4. ***Train:*** fine-tune π0.5 in the cloud ([script](tools/train_cloud.sh)).
5. ***Run:*** the model drives the arm from the Mac.
6. ***Score:*** the same fixed layouts for every model, on the [scoring page](tools/eval_ui.py).
7. ***Improve:*** add data where it struggles, retrain, score again.

Every command: [runbook](RUNBOOK.md).

## In this repo

| Path | What it is |
| --- | --- |
| [REPORT.md](REPORT.md) | Full project report |
| [BUILD_LOG.md](BUILD_LOG.md) | Day-by-day build log |
| [RUNBOOK.md](RUNBOOK.md) | Every command, in order |
| [tools/](tools/) | Recording page, scoring page, review tool, cloud training job |
| [patches/](patches/lerobot-so101-startup-shutdown.patch) | LeRobot startup and shutdown fix, with tests |
| [hardware/](hardware/) | The two redesigned printed parts and the script that made the handle change |
| [media/](media/) | Photos, videos, plots and raw joint data |

## Credits

Arm design: [TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100). π0.5: [Physical Intelligence](https://github.com/Physical-Intelligence/openpi). Robot software: [Hugging Face LeRobot](https://github.com/huggingface/lerobot). Claude Code helped read the LeRobot source, write diagnostic scripts and keep notes. Build and hands-on testing by Jaxson Bie.
