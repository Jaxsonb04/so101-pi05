<h1 align="center">SO-101 → π0.5: teaching a robot arm to tidy my tools</h1>

<p align="center">
  I built two robot arms and I'm teaching one of them to put my tools away.<br>
  Below is its first full run on its own: four tools, no help.
</p>

<p align="center">
  <img src="media/2026-11-10-first-pass.gif" width="640" alt="Animated: overhead and wrist camera views as the arm puts three bit strips and a screwdriver into the toolbox on its own; a label bar counts the tools in the box up to 4 of 4"><br>
  <sub>Sped up 3×, with the pauses between moves cut. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-10-first-pass.mp4">MP4 at real speed</a></sub>
</p>

<p align="center">
  <a href="#status">Status</a> ·
  <a href="#first-results">First results</a> ·
  <a href="#recording-demonstrations">Recording</a> ·
  <a href="#problems-i-ran-into">Problems I ran into</a> ·
  <a href="#the-build">The build</a> ·
  <a href="BUILD_LOG.md">Build log</a> ·
  <a href="RUNBOOK.md">Runbook</a>
</p>

I 3D-printed and put together a pair of [SO-101](https://github.com/TheRobotStudio/SO-ARM100) arms, added two cameras, and recorded 50 demonstrations of the task by steering one arm with the other. Then I fine-tuned [π0.5](https://www.physicalintelligence.company/blog/pi05), an open robot model from Physical Intelligence, on those recordings using [Hugging Face LeRobot](https://github.com/huggingface/lerobot), and let it try the task on its own. It now gets about half the tools into the box, and I know why it misses the rest.

## Status

Updated November 10, 2026.

| Step | Status |
| --- | --- |
| Print, wire and assemble both arms | ✅ Done |
| Calibrate and teleoperate | ✅ Done |
| Add wrist and overhead cameras | ✅ Done |
| Build a tool for recording demonstrations | ✅ Done |
| Record 50 demonstrations | ✅ Done |
| Fine-tune π0.5 | ✅ Done |
| Run it on the arm | ✅ First full pass |
| Build tools to score and review trials | ✅ Done |
| Record more data where it fails | 🔄 Next |
| Retrain and score 20 trials | ⏳ After that |

> [!NOTE]
> The wrist camera still drops off USB now and then, and when it comes back macOS can swap the two cameras' numbers. My tools now catch that and fix it before the arm moves.

## First results

My best setup so far got **11 of 20 tools into the box over 5 trials, including one full pass**. It's not reliable yet, but every failure is recorded and reviewed, so I know what to fix.

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
    <td><sub>A starts a trial and B marks a pass. C marks a fail and asks how many tools made it into the box. D sends the arm home, and M marks a moment to review. The arm resets itself after every trial. <a href="tools/eval_ui.py">Code</a></sub></td>
    <td><sub>My review tool marks every pick, release and long pause on the camera frames, using the gripper's own readings. This is the full pass. <a href="tools/review_trials.py">Code</a></sub></td>
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
    <td><sub>White dots show where the tools sat in my 50 demos, green shows tools it got into the box, and red shows tools it left behind. Only 8% of my demo placements were on the right, and it never got a tool from there.</sub></td>
    <td><sub>For 21 trials the model saw the overhead view where it expected the gripper's view. macOS had renumbered the two identical cameras after a USB dropout.</sub></td>
  </tr>
</table>

Next, I'll record data for exactly the spots it fails on and retrain. The full story is in the [build log](BUILD_LOG.md#november-10-first-runs-on-the-arm-and-finding-out-why-it-fails).

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

**My first 21 trials all failed, and the model wasn't to blame.** Going through the recordings showed the two camera feeds had swapped places. After a USB dropout, macOS gave the two identical cameras each other's numbers. Only the overhead camera can see the wall, so my pages now compare the two feeds and put them in the right slots before the arm moves.

**The arm couldn't make up its mind.** It swung back and forth between two tools. LeRobot's smooth real-time mode replans about every 0.7 seconds and keeps little of the old plan, so the model kept switching targets. Plain mode commits to each plan for 1.7 seconds. That took it from 0 to 5 of 20 tools in my first comparison.

**Longer training wasn't better, and the gaps were in my data.** The halfway checkpoint got 11 of 20 tools into the box, and the final one got 6. A map of where my demos put the tools showed why the right side always failed: only 8% of my demo placements were there.

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
| Software | LeRobot on a MacBook Pro (M3 Max), plus my own [recording, scoring and review tools](tools/) |

## How it learns the task

1. I steer the follower with the leader arm to show it the task.
2. Each recording saves both camera videos, the arm's joint angles, and whether the attempt worked.
3. π0.5 is fine-tuned on the successful recordings in the cloud.
4. The trained model runs on my Mac and drives the arm.
5. I score trials on my [eval page](tools/eval_ui.py) (pass, fail, or how many tools made it), and a [review tool](tools/review_trials.py) marks every pick, drop and stall on the recordings.
6. I record more data where it fails, retrain, and publish the results, failures included.

Every command is in the [runbook](RUNBOOK.md).

## Credits

Arm design by [TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100). π0.5 by [Physical Intelligence](https://github.com/Physical-Intelligence/openpi). Robot software by [Hugging Face LeRobot](https://github.com/huggingface/lerobot). I used Claude Code to help read the LeRobot source, write diagnostic scripts and keep notes. The build and the hands-on testing are mine.
