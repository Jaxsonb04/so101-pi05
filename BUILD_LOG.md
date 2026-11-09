# Build log

Dated engineering notes from building two SO-101 arms and getting them ready for π0.5. I keep what I measured separate from what I assumed, and I keep the mistakes in.

I built, wired, measured and operated the arms myself. [Claude Code](https://claude.com/claude-code), an AI coding assistant, helped me read the LeRobot source, write diagnostic scripts and keep these notes.

## October 3–5: first prints and fit tests

- Printed the controller mount on a Bambu P1S. The board's brass spacers wouldn't go into the printed holes.
- Changed only the four hole sizes. +0.6 mm was too loose and the spacers slid out; +0.2 mm total gave a snug fit. Outer size and hole spacing stayed the same.
- Printed the leader handle upright instead of on its side, so support material wouldn't scar the grip surface.
- Installed LeRobot 0.6.2 from source. Before touching hardware, I checked the imports, CPU and Apple GPU (MPS), and video encoding and decoding.

## October 11–12: printing and motor bring-up

<img src="media/2026-10-12-motor-setup-bench.jpg" alt="Desk with Feetech STS3215 servo boxes, printed arm parts, a power supply and the Waveshare servo controller board" width="360">

- Printed the remaining 15 of the 23 structural parts on four plates. I checked the slicer project against the official part list, so there were no missing or duplicate parts.
- Matched the 12 servos to the bill of materials from their box labels: 7× C001 (1:345 gearing), 2× C044 (1:191) and 3× C046 (1:147). The follower uses six C001s. The leader mixes all three, so the hand-held arm is easy to move.
- Checked the controller board's jumpers for USB control. Confirmed from its documentation that it has no voltage regulator, so the servos get whatever the supply puts out.
- Measured the 5 V / 4 A supply with a multimeter: **5.5 V unloaded**, center-positive.
- Set the follower's motor IDs one motor at a time, from 6 down to 1, switching DC power off for every swap. The first try failed with "motor not found": USB powers the board's chip, but not the servos.

## October 15: leader IDs and an intermittent USB error

<img src="media/2026-10-15-shoulder-assembly.jpg" alt="Close-up of the SO-101 shoulder joint and upper arm mounted on its printed base" width="320">

- Leader setup stopped with `termios.error: Device not configured` during a motor scan. A new USB cable was the suspect.
- Tested the cable before blaming it. On the same board, motor, power and port, both cables passed **50 of 50** ping and model reads with zero errors. The error hasn't come back.
- Finished the leader's IDs with a guarded routine. It refuses to write unless exactly one motor answers at ID 1, then reads back the stored ID and baud rate (**20 of 20** checks for the wrist roll).

## October 18–19: assembly, bus checks, first teleoperation

- Assembled and wired both arms. The first full scan of the follower missed motor 5. After reseating, both arms returned IDs 1–6 in **3 of 3** read-only scans.
- The leader's handle didn't slide into its mount. I widened only the slot in CAD, by 1 mm total, kept the outer shape, and checked the result with cross-sections before reprinting.
- First teleoperation ran at 10 Hz with a 1° step limit I'd added. On shutdown the follower's elbow reported **Overload**, and at startup the wrist turned without the leader moving. A register read of all 12 motors afterwards showed torque off and no fault flags.
- Traced the startup motion in the source: the follower turned its motors on before setting their target positions, so stale targets could run. Patched it locally to set targets first and enable torque last. Also made shutdown try every motor and always close the port, instead of stopping at the first error. Both bugs were reproduced in tests before the fix; afterwards **51 focused tests passed**.
- My step limit made following slow and filled the log with warnings. Lesson: start with the official command and change one thing at a time. With the standard command: **59.5 Hz over 95.5 s**, 0 of 5,680 loop ticks over budget, clean shutdown.

[![Leader and follower arms on a desk; the follower copies the leader's pose](media/2026-10-19-first-teleop.jpg)](media/2026-10-19-first-teleop.mp4)

*First teleoperation: I move the leader arm (right) and the follower (left) copies it. Click to play (16 s).*

## October 30: restart check

- Before running, I did a read-only check of all 12 motors: torque 0, status 0, and the calibration stored in each motor matched the saved files.
- The first start failed once with `No status packet` on the gripper. A read-only recheck passed 10 of 10, and the unchanged command then ran at 60 Hz.

## November 4–8: camera mounts

<img src="media/2026-11-08-camera-stand.jpg" alt="Printed overhead camera tower with an InnoMaker camera board on top, next to the follower arm with its wrist camera" width="360">

- Printed the official overhead camera stand (4 parts, about 6 hours) and the wrist camera mount, which replaces the follower's wrist part.
- Compared six print orientations for the wrist mount on surface finish, support contact and strength before slicing.
- The first attempt at the stand's second plate failed because the first layer didn't stick. The retry finished.

## November 6: π0.5 plan and Mac timing

- Timed π0.5 on my M3 Max: **0.64 s per 50-action chunk**, using 9.2 GiB in bfloat16. That's the model alone on random weights, so real runs will be slower. Real-time chunking took 0.66 s per chunk.
- Checked that every record, train and rollout command in the [runbook](RUNBOOK.md) parses against LeRobot 0.6.2.

## November 8: calibration root cause and cameras

### The follower sat a few degrees left of the leader

- Recalibrated both arms, and the offset was still there. I had to redo the leader once: its saved gripper range was 2045–2047, so I hadn't moved the gripper during the sweep. Checking the saved file caught it.
- Read the source to see how a joint's angle is computed: `(raw − middle of recorded range) × 360 / 4095`. **Zero is the middle of your calibration sweep, not the pose you hold at the start.** The base has no hard stops, so how far I swung it each way set its zero, and that differed between the arms. The follower's middle was 1978 and the leader's was 1894.5, about 7° apart.
- Shifted the leader's base range by +84 steps so the middles match. I changed the passive leader only, so the follower's motion limits are untouched, and kept a backup of every file.
- Verified with a read-only script, both arms posed the same way by hand: the base angles were **0.48°** apart, where the old numbers would have given about 7°.
- The wrist flex had the same problem: **21.67°** apart. I shifted the leader's range by −246 steps and re-measured **0.04°**.
- One thing still doesn't fully add up: the October files predicted an offset in the opposite direction from the one I saw. So I treated the shift as a test and measured the result rather than assuming it worked.

### Cameras

| Overhead camera (index 0) | Wrist camera (index 1) |
| --- | --- |
| ![Robot's overhead camera view: the desk, an open toolkit and the follower arm at the bottom edge](media/2026-11-08-robot-view-overhead.jpg) | ![Robot's wrist camera view: the gripper jaws at the bottom with the desk ahead](media/2026-11-08-robot-view-wrist.jpg) |

- macOS found 0 cameras at first because the terminal didn't have camera permission.
- The first run with both camera feeds stopped after 19.8 s: a frame from one camera was more than 500 ms old. Both cameras share one USB 2 hub, because the Mac has no USB-A ports.
- I tried compressed video (MJPG). A later test showed macOS ignores that setting, so it wasn't the fix, and I corrected my notes. The stall hasn't come back. A 15 s camera-only test gave 29.6 and 29.5 fps, with a worst frame gap of 67 ms, and teleoperation with both feeds ran for over 3 minutes.
- Looking at the saved frames showed the camera names were swapped: index 0 is the overhead camera, index 1 the wrist. I fixed the config before recording any data. Training on swapped camera names would have taught the model the wrong views.

[![Teleoperation with the Rerun viewer on the laptop showing both camera feeds and live joint plots](media/2026-11-08-teleop-with-cameras.jpg)](media/2026-11-08-teleop-with-cameras.mp4)

*Teleoperation with both camera feeds and live joint plots in Rerun. Click to play (11 s).*

## Next

1. Record 50 demonstrations of putting three tools into the toolbox.
2. Fine-tune π0.5 on Hugging Face Jobs: a smoke test first, then the full run.
3. Run it on the arm, score 20 trials and compare checkpoints.
4. Add voice: speech-to-text on the Mac picks the task sentence π0.5 was trained on.
