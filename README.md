<h1 align="center">SO-101 → π0.5 → voice commands</h1>

<p align="center">
  Two 3D-printed robot arms, taught a real task from my own demonstrations.<br>
  The goal: say <i>"put the tools in the toolbox"</i> and have the arm do it.
</p>

<p align="center">
  <img src="media/2026-11-08-teleop-with-cameras.gif" width="640" alt="Animated: teleoperation with the Rerun viewer on the laptop showing both camera feeds and live joint plots">
</p>

<p align="center">
  <a href="#status">Status</a> ·
  <a href="#recording-demonstrations">Recording</a> ·
  <a href="#test-and-integration-highlights">Highlights</a> ·
  <a href="#the-build">The build</a> ·
  <a href="BUILD_LOG.md">Build log</a> ·
  <a href="RUNBOOK.md">Runbook</a>
</p>

I printed, wired and calibrated a pair of [SO-101](https://github.com/TheRobotStudio/SO-ARM100) arms, integrated two cameras and built a recording workflow. Now I'm recording demonstrations to fine-tune Physical Intelligence's [π0.5](https://www.physicalintelligence.company/blog/pi05), an open vision-language-action model, with [Hugging Face LeRobot](https://github.com/huggingface/lerobot).

## Status

As of November 8, 2026.

| Stage | Status | Evidence |
| --- | --- | --- |
| Print 23 parts and both camera mounts | ✅ Done | Bambu P1S; two parts revised for fit |
| Set up 12 servos | ✅ Done | Each ID read back; both arms answer IDs 1–6 in 3 of 3 scans |
| Assemble and wire both arms | ✅ Done | Full-bus scans and register checks with torque off |
| Calibrate and align | ✅ Done | Base 0.48° and wrist 0.04° apart when posed the same |
| Teleoperation | ✅ Done | 59.5 Hz over 95.5 s, 0 of 5,680 ticks over budget |
| Cameras | ✅ Done | Wrist and overhead, about 30 fps each |
| Recording workflow | ✅ Done | Start, pass, fail and cancel page; self-test passes |
| First replay | ✅ Done | The follower replays a recorded episode on its own |
| Record 50 demonstrations | 🔄 Ongoing | 19 of 50 passed so far (plus 2 failed), private dataset |
| Fine-tune π0.5 | ⏳ Next | Hugging Face Jobs, one A100, at most about $16 |
| Autonomous runs | ⏳ Planned | 20 scored trials, then checkpoint comparison |
| Voice commands | ⏳ Planned | Speech-to-text picks the trained task sentence |

> [!NOTE]
> **Open issue:** the wrist camera keeps dropping off USB for about 30 ms at a time, which stops a recording. The system log points at its cable, plug or hub port. Saved episodes survive, and the recorder picks up where it left off.

## Recording demonstrations

<table>
  <tr>
    <th width="24%">Teleoperating a demonstration</th>
    <th width="52%">The recording page</th>
    <th width="24%">First replay</th>
  </tr>
  <tr>
    <td align="center"><img src="media/2026-11-08-data-collection.gif" height="240" alt="Animated: the follower arm, driven from the leader, picks up a bit strip and puts it into the open toolbox"></td>
    <td align="center"><img src="media/2026-11-08-recording-page.gif" height="240" alt="Animated: the recording page cancels an episode, records one with a red timer bar, then saves it as passed"></td>
    <td align="center"><img src="media/2026-11-08-first-replay.gif" height="240" alt="Animated: the follower arm moves through a recorded episode by itself"></td>
  </tr>
  <tr>
    <td><sub>I drive the leader; the follower puts a bit strip into the toolbox. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-data-collection.mp4">MP4</a></sub></td>
    <td><sub>Cancel, record, then save as passed (GIF at 2× speed). <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-recording-page.mp4">MP4</a></sub></td>
    <td><sub>The follower plays back a recorded episode. It doesn't use the cameras yet; that's π0.5's job. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-first-replay.mp4">MP4</a></sub></td>
  </tr>
</table>

The [recording page](tools/record_ui.py) wraps LeRobot's own recorder: **A** start, **B** pass, **C** fail, **D** cancel, with both camera feeds. Failed attempts are kept with a label, and the pass count carries over between sessions. Commands are in the [runbook](RUNBOOK.md#4-record-demonstrations).

## Test and integration highlights

How I found each problem, isolated it and proved the fix. The full detail is in the [build log](BUILD_LOG.md).

- **Camera fault traced in the system log.** Recording kept stopping with "latest frame is too old". The macOS kernel log showed the wrist camera physically disconnecting at those moments: 193 times in one evening, against once for the overhead camera on the same hub. That ruled out software, the hub and my first theory, USB bandwidth.
- **A recorder built around LeRobot, not inside it.** I wrapped LeRobot's own `record()` with a start, pass, fail and cancel page that keeps failed attempts with labels. An independent review against LeRobot's source found three bugs before first use; each fix has a self-test case.
- **Reviewing my own data first.** Before the real 50, I checked all 8 test episodes from sampled frames and joint data. That caught false starts, my hand and laptop screen in the overhead view, and look-alike objects on the table. I fixed the scene before recording.
- **Calibration offset traced to its root cause.** LeRobot puts each joint's zero at the middle of the calibration sweep, not at the reference pose. I matched the two arms' middles and measured 0.48° on the base and 0.04° on the wrist.
- **A startup bug found and covered by tests.** Torque was enabled before target positions were set, so stale targets could move the arm. I fixed the order and made shutdown release every motor even after an error; 51 focused tests pass.
- **Evidence before blame.** A USB error pointed at a new cable. On the same board, motor and port, both cables passed 50 of 50 reads, so I kept it.
- **Correcting my own mistakes.** A "safety" step limit made teleoperation slow and noisy, a video setting I'd credited did nothing, and my USB-bandwidth theory was wrong. Each one is corrected in the log.

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

| Part | Details |
| --- | --- |
| Arms | One leader (moved by hand) and one follower (copies it), printed in PLA+ |
| Motors | 12 Feetech STS3215. The follower uses 1:345 gearing; the leader mixes 1:191, 1:345 and 1:147 so it's easy to move by hand |
| Controllers | 2 Waveshare Bus Servo Adapter (A), 5 V supplies checked with a multimeter |
| Cameras | 2 InnoMaker 32×32 mm USB boards, wrist and overhead, 640×480 at 30 fps |
| Software | LeRobot 0.6.2 on an M3 Max MacBook, plus my [recording tools](tools/) |

## How it learns the task

1. **Teleoperate:** I move the leader and the follower copies it.
2. **Record:** each episode saves both camera videos, the joint angles, the task sentence and my pass or fail label.
3. **Fine-tune:** start from `pi05_base` and train on the passed episodes on a cloud A100.
4. **Run:** the Mac runs the trained model on the arm, with real-time chunking for smooth motion.
5. **Measure:** 20 scored trials. I'll publish the success rate and what went wrong.
6. **Voice:** speech-to-text on the Mac turns what I say into the task sentence. π0.5 only does tasks it has practised, so each new task gets its own demonstrations.

Every command is in the [runbook](RUNBOOK.md).

## Measured so far

- **π0.5 on an M3 Max:** 0.64 s per 50-action chunk, using 9.2 GiB in bfloat16. A chunk covers 1.67 s of motion at 30 fps, so the Mac keeps up on paper. This timed the model alone on random weights.
- **Real-time chunking:** 0.66 s per chunk, using 9.3 GiB.

## Not tested yet

- Anything with a trained π0.5 on the real arm
- The cloud training job, which is why a smoke test comes first
- Loading a cloud-trained checkpoint on the Mac, because the cloud image may be newer than my LeRobot 0.6.2
- A full recording session without a wrist-camera dropout

## Credits

Arm design by [TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100). π0.5 by [Physical Intelligence](https://github.com/Physical-Intelligence/openpi). Robot software by [Hugging Face LeRobot](https://github.com/huggingface/lerobot). Claude Code helped with source reading, diagnostic scripts and notes; the build and every hands-on test are mine.
