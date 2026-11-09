# SO-101 robot arms → π0.5 → voice commands

I'm building a robot-learning setup end to end. I printed, wired and calibrated a pair of [SO-101](https://github.com/TheRobotStudio/SO-ARM100) arms and integrated two cameras. Next I'll teach the follower arm a real task with Physical Intelligence's [π0.5](https://www.physicalintelligence.company/blog/pi05). The goal: say *"put the tools in the toolbox"* and have the arm do it.

![Animated: teleoperation with the Rerun viewer on the laptop showing both camera feeds and live joint plots](media/2026-11-08-teleop-with-cameras.gif)

Full clips (MP4 download): [teleoperation with both cameras and live joint plots](https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-teleop-with-cameras.mp4) (Nov 8, 11 s) · [first leader–follower teleoperation](https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-10-19-first-teleop.mp4) (Oct 19, 16 s)

## Status, November 8, 2026

| Stage | Status | How I know |
| --- | --- | --- |
| Print 23 structural parts and both camera mounts | ✅ Done | All printed on a Bambu P1S; two parts revised for fit |
| Set up and verify 12 servos | ✅ Done | Each ID read back; both arms answer IDs 1–6 in 3 of 3 scans |
| Assemble and wire both arms | ✅ Done | Full-bus scans, register checks with torque off |
| Calibrate and align | ✅ Done | Base 0.48° and wrist 0.04° apart when posed the same, measured |
| Teleoperation | ✅ Done | 59.5 Hz over 95.5 s, 0 of 5,680 ticks over budget |
| Cameras | ✅ Done | Wrist and overhead, about 30 fps each, worst frame gap 67 ms |
| Record 50 demonstrations | Next | Task: put three tools into a toolbox |
| Fine-tune π0.5 | Planned | Hugging Face Jobs, one A100, at most about $16 |
| Autonomous runs | Planned | 20 scored trials, then checkpoint comparison |
| Voice commands | Planned | Speech-to-text picks the trained task sentence |

## Test and integration highlights

Problems I hit, how I isolated them, and how I checked the fix. The full detail is in the **[build log](BUILD_LOG.md)**.

- **Calibration offset traced to its root cause.** The follower sat a few degrees left of the leader, and recalibrating didn't fix it. In the LeRobot source I found that each joint's zero is the middle of the calibration sweep, not the reference pose. My hand sweeps put the two arms' middles about 7° apart. I shifted the passive leader's range, kept backups, and verified with a read-only measurement: 0.48° on the base, 0.04° on the wrist.
- **A startup bug found and covered by tests.** On the first teleoperation the follower's elbow raised an overload fault and the wrist moved by itself. In the source, torque was enabled before target positions were set. I reproduced it in tests, fixed the startup order and made shutdown release every motor even after an error: 51 focused tests pass.
- **Evidence before blame.** A USB error pointed at a new cable. On the same board, motor and port, both cables passed 50 of 50 reads, so I didn't replace hardware that wasn't faulty.
- **Camera integration.** I fixed a macOS permission block and investigated a frame stall on a shared USB 2 hub. Checking real frames showed the two camera names were swapped, and I fixed that before recording any training data.
- **Correcting my own mistakes.** I added a step limit "for safety" that made teleoperation slow and noisy, then went back to the official command and changed one thing at a time. When a fix I'd credited (MJPG video) turned out to do nothing, I corrected the record.
- **Mechanical fit.** I iterated the controller-mount holes (+0.6 mm too loose, +0.2 mm snug), widened a tight handle slot by 1 mm in CAD, and chose print orientations that keep support scars off grip surfaces.

## The build

| Printing | Motor bring-up | Assembly |
| --- | --- | --- |
| ![Bambu P1S print bed with SO-101 arm parts](media/2026-10-12-printing-parts.jpg) | ![Servo boxes, printed parts and the servo controller board on a desk](media/2026-10-12-motor-setup-bench.jpg) | ![SO-101 shoulder joint and upper arm on its base](media/2026-10-15-shoulder-assembly.jpg) |

| First teleoperation | Camera stand | What the robot sees |
| --- | --- | --- |
| ![Animated: leader and follower arms on a desk; the follower copies the leader's motion](media/2026-10-19-first-teleop.gif) | ![Printed overhead camera tower with a camera board on top, next to the follower arm](media/2026-11-08-camera-stand.jpg) | ![Overhead camera view of the desk](media/2026-11-08-robot-view-overhead.jpg) ![Wrist camera view showing the gripper jaws](media/2026-11-08-robot-view-wrist.jpg) |

- **Arms:** one leader (moved by hand) and one follower (copies it), 3D printed in PLA+
- **Motors:** 12 Feetech STS3215. The follower uses 1:345 gearing; the leader mixes 1:191, 1:345 and 1:147 so it's easy to move by hand
- **Controllers:** 2 Waveshare Bus Servo Adapter (A), 5 V supplies, checked with a multimeter
- **Cameras:** 2 InnoMaker 32×32 mm USB boards, wrist and overhead, 640×480 at 30 fps
- **Software:** LeRobot 0.6.2 on an M3 Max MacBook

## How it will learn the task

1. **Teleoperate:** I move the leader and the follower copies it.
2. **Record:** each episode saves both camera videos, the joint angles and the task sentence.
3. **Fine-tune:** start from `pi05_base` and train on my 50 episodes in the cloud.
4. **Run:** the Mac runs the trained model on the arm, using real-time chunking for smooth motion.
5. **Measure:** 20 scored trials. I'll publish the success rate and what went wrong.
6. **Voice:** speech-to-text on the Mac turns what I say into the task sentence. π0.5 can only do tasks it has practised, so each new task gets its own demonstrations.

Every command is in the **[runbook](RUNBOOK.md)**.

## Measured so far without the robot

- **π0.5 speed on an M3 Max:** 0.64 s per 50-action chunk, using 9.2 GiB in bfloat16. That chunk covers 1.67 s of motion at 30 fps, so the Mac is fast enough on paper. This timed the model alone on random weights.
- **Real-time chunking on the same Mac:** 0.66 s per chunk, using 9.3 GiB.

## Not tested yet

- Anything with a trained π0.5 on the real arm
- The cloud training job, which is why the smoke test comes first
- Loading a cloud-trained checkpoint on the Mac, because the cloud image may be newer than my LeRobot 0.6.2

## Credits

Arm design by [TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100). π0.5 by [Physical Intelligence](https://github.com/Physical-Intelligence/openpi). Robot software by [Hugging Face LeRobot](https://github.com/huggingface/lerobot). Claude Code helped with source reading, diagnostic scripts and notes; the build and every hands-on test are mine.
