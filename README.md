<h1 align="center">SO-101 → π0.5 → voice commands</h1>

<p align="center">
  I built two robot arms and I'm teaching one of them to put my tools away.<br>
  The goal: say <i>"put the tools in the toolbox"</i> and watch it happen.
</p>

<p align="center">
  <img src="media/2026-11-08-teleop-with-cameras.gif" width="640" alt="Animated: teleoperation with the Rerun viewer on the laptop showing both camera feeds and live joint plots">
</p>

<p align="center">
  <a href="#status">Status</a> ·
  <a href="#recording-demonstrations">Recording</a> ·
  <a href="#problems-i-ran-into">Problems I ran into</a> ·
  <a href="#the-build">The build</a> ·
  <a href="BUILD_LOG.md">Build log</a> ·
  <a href="RUNBOOK.md">Runbook</a>
</p>

I 3D-printed and put together a pair of [SO-101](https://github.com/TheRobotStudio/SO-ARM100) arms, added two cameras, and recorded 50 demonstrations of the task by steering one arm with the other. Now I'm fine-tuning [π0.5](https://www.physicalintelligence.company/blog/pi05), an open robot model from Physical Intelligence, on those recordings using [Hugging Face LeRobot](https://github.com/huggingface/lerobot). Next, the arm tries it on its own.

## Status

Updated November 9, 2026.

| Step | Status |
| --- | --- |
| Print, wire and assemble both arms | ✅ Done |
| Calibrate and teleoperate | ✅ Done |
| Add wrist and overhead cameras | ✅ Done |
| Build a tool for recording demonstrations | ✅ Done |
| Record 50 demonstrations | ✅ Done |
| Fine-tune π0.5 | 🔄 Training now |
| Run it on the arm and score it | ⏳ Next |
| Voice commands | ⏳ Later |

The trained model hasn't touched the arm yet. I'll post the results here, good or bad.

> [!NOTE]
> The wrist camera still drops off USB every so often. I've narrowed it down to that camera's cable or port, but haven't fixed it yet.

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
    <td><sub>I move the leader arm and the follower copies it. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-data-collection.mp4">MP4</a></sub></td>
    <td><sub>The recording page, sped up 2×. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-recording-page.mp4">MP4</a></sub></td>
    <td><sub>Replaying a recording. It just repeats the motions and doesn't look at the cameras yet. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-first-replay.mp4">MP4</a></sub></td>
  </tr>
</table>

LeRobot's recorder is driven by keyboard shortcuts, which got in the way, so I wrote a small [recording page](tools/record_ui.py) on top of it. One key starts a take, and the others mark it as a pass, a fail or a do-over. It also remembers where I left off, so I could spread the recording over two evenings. The commands are in the [runbook](RUNBOOK.md#4-record-demonstrations).

## Problems I ran into

The full story is in the [build log](BUILD_LOG.md). These are the ones I learned the most from.

**The wrist camera kept cutting out.** Recording would stop with "latest frame is too old", and I assumed it was USB bandwidth. The macOS system log said otherwise: the wrist camera was physically disconnecting, nearly 200 times in one evening, while the overhead camera on the same hub barely did. So it's that camera's cable or port, not my code.

**My cloud-trained model wouldn't have loaded.** I train in the cloud on Hugging Face, and their training image had moved to a newer LeRobot that same day. I ran a short test job before paying for the real one and checked whether my Mac could load the result. It couldn't: about half the weights had been renamed between versions. Making the cloud job install the exact versions I run locally fixed it.

**The arms didn't line up.** Even after recalibrating, the follower always sat a few degrees off from the leader. Reading LeRobot's source showed why: a joint's zero is the middle of whatever range you sweep during calibration, and I'd swept the two arms differently. Matching them took the gap from about 7° to under half a degree.

**The arm could lurch on startup.** The follower switched its motors on before telling them where to be, so it could jump toward an old target. I fixed the order and wrote tests that reproduced the bug first.

**I checked my own data before trusting it.** A few test recordings caught my hand and my laptop screen in the camera view, so I cleaned up the scene before the real 50. Reviewing those 50 also caught a bug in my own review script, which had been grabbing the wrong video frames.

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

| Part | What I used |
| --- | --- |
| Arms | Two SO-101s printed in PLA+: a leader I move by hand and a follower that copies it |
| Motors | 12 Feetech STS3215 servos |
| Controllers | 2 Waveshare servo boards |
| Cameras | 2 small USB cameras, one on the wrist and one overhead |
| Software | LeRobot on a MacBook Pro (M3 Max), plus my own [recording tools](tools/) |

## How it learns the task

1. I steer the follower with the leader arm to show it the task.
2. Each recording saves both camera videos, the arm's joint angles, and whether the attempt worked.
3. π0.5 is fine-tuned on the successful recordings in the cloud.
4. The trained model runs on my Mac and drives the arm.
5. I run 20 trials and publish the success rate, failures included.
6. Then voice: speech-to-text turns what I say into the task.

Every command is in the [runbook](RUNBOOK.md).

## Credits

Arm design by [TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100). π0.5 by [Physical Intelligence](https://github.com/Physical-Intelligence/openpi). Robot software by [Hugging Face LeRobot](https://github.com/huggingface/lerobot). I used Claude Code to help read the LeRobot source, write diagnostic scripts and keep notes. The build and the hands-on testing are mine.
