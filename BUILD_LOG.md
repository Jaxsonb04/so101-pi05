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

![Animated: leader and follower arms on a desk; the follower copies the leader's motion](media/2026-10-19-first-teleop.gif)

*First teleoperation: I move the leader arm (right) and the follower (left) copies it. [Full 16 s clip (MP4)](https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-10-19-first-teleop.mp4).*

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
- I tried compressed video (MJPG). A later test showed macOS ignores that setting, so it wasn't the fix, and I corrected my notes. The stall hasn't come back. A 15 s camera-only test gave 29.6 and 29.5 fps, with a worst frame gap of 67 ms, and teleoperation with both feeds ran for over 3 minutes. *Correction, later the same evening: the stall hadn't gone away, and it wasn't the hub's bandwidth. The wrist camera was physically disconnecting; see "Camera dropouts" below.*
- Looking at the saved frames showed the camera names were swapped: index 0 is the overhead camera, index 1 the wrist. I fixed the config before recording any data. Training on swapped camera names would have taught the model the wrong views.

![Animated: teleoperation with the Rerun viewer on the laptop showing both camera feeds and live joint plots](media/2026-11-08-teleop-with-cameras.gif)

*Teleoperation with both camera feeds and live joint plots in Rerun. [Full 11 s clip (MP4)](https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-teleop-with-cameras.mp4).*

## November 8 (evening): recording the demonstrations

### Data collection

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
    <td><sub>I drive the leader; the follower puts a bit strip into the toolbox. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-data-collection.mp4">MP4, 9 s</a></sub></td>
    <td><sub>Cancel, record, then save as passed (GIF at 2× speed). <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-recording-page.mp4">MP4, 43 s, real time</a></sub></td>
    <td><sub><code>lerobot-replay</code> of a recorded test episode. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-first-replay.mp4">MP4, 25 s</a></sub></td>
  </tr>
</table>

The replay is the first time the follower moved without me driving it. It plays back the recorded joint motions without looking at the cameras, and I'd moved the toolbox since recording, so it goes through the motions without picking anything up. A trained policy is the next step.

### A recording page instead of keyboard shortcuts

- Plain `lerobot-record` has three keys: end the episode, re-record it, and stop. It can't wait for me to start an episode, or label an attempt passed or failed, and its keys are read system-wide through macOS Accessibility, so a launcher can't simply type them for me. Its timed reset pause also got in the way: I lost a complete 60-second episode by pressing Ctrl+C during that pause, because LeRobot saves an episode only after it.
- I built [`tools/record_ui.py`](tools/record_ui.py). It runs LeRobot's own `record()` unchanged and swaps two things at runtime: the keyboard listener and the per-episode loop. A local page shows both cameras and the state: **A** start, **B** pass, **C** fail, **D** cancel. Passed and failed episodes are both saved, with a label in `episode_labels.csv`. Cancelled ones are discarded through LeRobot's own re-record path, which also cancels that episode's video encoding.
- `--dataset.num_episodes` counts passes only, and the count carries over between sessions, so after Ctrl+C the same command picks up where it left off.
- Before using it on the arm I had the launcher reviewed independently against LeRobot's source. That found three real bugs: resuming would have crashed, because LeRobot's `resume()` needs the dataset folder passed explicitly; a label could be written for an episode whose save was cut off by Ctrl+C; and the list of failed episodes to skip covered only the current session. I fixed all three and added each case to a self-test that runs without the robot.
- Smaller things it handles: LeRobot adds a date-time stamp to every new dataset name unless `--dataset.no_stamp=true`, and refuses to create a dataset in a folder an interrupted run left behind.

### Camera dropouts: the real cause

- Recording kept stopping with `OpenCVCamera(1) latest frame is too old`. That only says the wrist camera sent nothing for half a second.
- The macOS kernel log said more: `hardware connection lost` for the wrist camera, then a re-enumeration about 30 ms later, at the same second each run stopped. Because the camera comes back so fast, it always looks connected.
- I counted the events per USB port: **193 disconnects of the wrist camera in one evening against 1 for the overhead camera** on the same hub, and 2,857 USB transaction errors against 2. The servo board on that hub never dropped by itself.
- That rules out software and the hub as a whole: drops started before any LeRobot command, happened during calibration when no program had the cameras open, and continued with nothing running. It also rules out USB bandwidth: OpenCV runs 640×480 MJPEG at 30 fps, and the idle-time errors were on the control endpoints, not the video endpoint. My earlier bandwidth explanation was wrong.
- The remaining suspects are the wrist camera's cable or plug, which flex with the arm, its hub port, or the camera board. A test session of about 6 minutes had no drops, but it dropped again soon after, so this is still open.
- I decided against adding an automatic camera reconnect: it couldn't save an episode the drop interrupted, and it would hide the fault.

### Reviewing my own data

- I recorded 5 test passes, then checked all 8 test episodes (5 passes, 3 fails): 8 sampled frames per camera, plus joint ranges and leader–follower tracking error.
- All 5 passes were complete. Two "failed" episodes weren't attempts at all: 5 s and 1 s long, with under 0.2° of joint motion. That's why the page now has Cancel.
- The review also caught problems in the scene: my hand entering the overhead view at the end of most episodes, my laptop screen in the corner of the overhead view (its content changes between episodes, which a policy can latch onto), a dark image, and orange scraps that look like the bit strips. I fixed the scene before the real recording. The overhead camera and the toolbox now stay put; only the tools move between episodes.

### Where it stands

- As of November 8 the real dataset has **21 episodes: 19 passed, 2 failed**, uploaded privately to Hugging Face at the end of that session. 50 passes is the target.
- The wrist camera fault isn't fixed yet.

## November 9: 50 demonstrations, then training

### The dataset

- Finished recording: **52 episodes, 50 passed and 2 failed**, 25.4 minutes at 30 fps over two evenings. The same command continued the dataset, and the pass count carried over.
- The wrist camera dropped off USB 18 more times, mostly in the first few minutes. No saved episode was affected, but it isn't fixed.

### Reviewing all 52 episodes

- For every episode I checked the joint data (length, idle time at start and end, motion, leader–follower gap, start pose) and frames from both cameras, then looked at the last overhead frame of each one myself.
- All 50 passes end with every tool in the box and nothing on the table. Both fails are real: one left a screwdriver and a strip out, the other moved nothing.
- No bad episodes. Passes take 16.6–61.6 s (median 28 s), motion starts within 2.3 s of the start and stops within 2.5 s of the end, and start poses stay within 10°. The longest pass seems to include a regrasp that still succeeded, which is useful recovery data.
- One thing I hadn't controlled: the toolbox sat in 4 different places. 38 of the 50 passes are at the main spot, so I'll test there first. The other spots would need 10–15 more demonstrations each.
- **A mistake in the review itself.** My first frame grab used ffmpeg's fast seek, which lands a few seconds late in these AV1 videos, so the "last frames" showed the next episode's setup. Judged on those frames, 15 passes looked like the tools had been reset and one looked unfinished. None of that was true. Decoding each video from the start by frame number fixed it. Lesson: check LeRobot videos by frame number, or with LeRobot's own loader.
- A frame-by-frame scan of every episode found no joint glitches, one 100 ms wrist-camera stall, and short holds in 0.2% of overhead frames. The cameras trail the joint data by a median of 1–2 frames, which will be the same on the arm. Nothing needed dropping.

### The cloud trained a model my Mac couldn't load

- The first 20-step smoke test failed after 28 s: `` `ema`: Could not decode the value ``. LeRobot 0.6.2 doesn't send the command line to the cloud. It uploads a config file, and the cloud image (`huggingface/lerobot-gpu:latest`) had been rebuilt that day from LeRobot 0.7.1, which changed that setting's format. The image has no version tags to pin.
- Passing the flags straight to the cloud's trainer got a 20-step run through. But the model didn't fit my Mac: its config had a field 0.6.2 rejects (`optimizer_fused`), and **437 of 813 weight names** differed, because the image's newer `transformers` drops one level from the vision encoder's names. It would have failed at the first rollout.
- Fix: the job installs the Mac's exact LeRobot commit and `transformers` 5.5.4 into the image before training. The pinned smoke test's model matches: the config and both processors load, and all 813 weights have the names and shapes my π0.5 expects. That was a check of the saved files only; the weights first get loaded for real at the first rollout.
- The smoke tests also compared GPUs: **2.28 s per step on an H200** against 5.17 s on an A100, at twice the price, so the H200 is slightly cheaper per step. The two runs used different software versions, so that's rough.
- It also corrected my cost estimate: 10,000 steps on the A100 would have taken about 14 hours and $36, not the 6 hours and $15 I'd planned.

### Training settings

- **Full fine-tune**, not just the action expert. Freezing the 3B vision-language model saves memory, which the H200's 141 GB doesn't need, and LeRobot's docs say it comes at some cost in success rate.
- **Image augmentation on.** It's off by default in LeRobot's π0.5, but openpi's own training uses crops, small rotations and colour changes. My data has two sessions in different light, and the wrist camera's colour drifts.
- **7,000 steps** at batch 32, about 5 passes over the data, with checkpoints at 3,500 and 7,000. I'll choose between them on the arm. In one reported comparison (openpi issue #1060), two models had the same offline error but very different task success, so I didn't hold out a validation set.
- **Left out:** EMA weights, and subtask annotations. π0.5's processors in LeRobot 0.6.2 read only the single task sentence, so subtask labels wouldn't reach the model yet.

### Training run

- Started at 21:08 on an H200 with a 6-hour cap. The log confirms the pinned versions and 50 episodes (44,270 frames), so the two fails were skipped.
- **2.28 s per step**, the same as the smoke test, so augmentation costs nothing: data loading waits 0.002 s per step. It uses 45 of the GPU's 141 GB.
- Training loss: 0.099 at step 200, 0.063 at step 400, 0.020 at step 3,200 (at 23:20). That only shows it's fitting the demonstrations; whether it works gets decided on the arm.
- At that pace it finishes around 01:45 on November 10, for about $23.

## Next

1. Fix the wrist camera's connection. A drop during a rollout would stop the policy, just as it stopped recording.
2. Run the trained model on the arm with the toolbox at its main spot: plain mode first, then real-time chunking.
3. Score 20 trials and compare the 3,500- and 7,000-step checkpoints.
4. Add voice: speech-to-text on the Mac picks the task sentence π0.5 was trained on.
