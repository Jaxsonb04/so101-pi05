# Build log

My notes from building two SO-101 robot arms and getting them ready to learn a task with π0.5, in the order it happened. I've left the mistakes in, because that's where I learned the most.

I did the building, wiring and testing myself. I used [Claude Code](https://claude.com/claude-code), an AI coding assistant, to help me read the LeRobot source, write diagnostic scripts and keep these notes.

## October 3–5: first prints

I started by printing the mount for the motor controller board on my Bambu P1S. The board's brass spacers wouldn't go into the printed holes, so I widened just those four holes. My first try (+0.6 mm) was so loose the spacers slid out. +0.2 mm was snug.

I printed the leader arm's handle standing up instead of on its side, so the support material wouldn't leave marks on the part you hold.

I also installed LeRobot, Hugging Face's robotics library, and made sure it could use my Mac's GPU and handle video before I touched any hardware.

## October 11–12: printing and motors

<img src="media/2026-10-12-motor-setup-bench.jpg" alt="Desk with Feetech STS3215 servo boxes, printed arm parts, a power supply and the Waveshare servo controller board" width="360">

I printed the other 15 parts on four plates, checking against the official parts list so nothing was missing or doubled up.

The two arms use 12 servo motors, and they aren't all the same. The follower uses six with the strongest gearing. The leader, which I move by hand, mixes three gear ratios so it's easy to push around. I sorted them by the labels on their boxes.

Before plugging anything in, I measured the power supply with a multimeter. It read 5.5 V with nothing connected, and the controller board doesn't regulate voltage, so that's exactly what the motors get.

Each motor needs its own ID, set one motor at a time. My first try failed with "motor not found" because I'd only plugged in USB. USB powers the board, but the motors need the separate power supply.

## October 15: a USB error I almost blamed on the wrong thing

<img src="media/2026-10-15-shoulder-assembly.jpg" alt="Close-up of the SO-101 shoulder joint and upper arm mounted on its printed base" width="320">

While I was setting up the leader's motors, the program crashed with a "device not configured" error. I'd just switched to a new USB cable and assumed that was the problem. Before throwing it out, I tested both cables on the same setup, and each one passed 50 out of 50 reads. The cable was fine, and the error hasn't come back.

For the rest of the leader's IDs, I used a small routine that refuses to change anything unless exactly one motor answers, then reads the new ID back to make sure it stuck.

## October 18–19: assembly and first teleoperation

I assembled and wired both arms. The first scan missed one of the follower's motors, and after I reseated its cable, both arms found all six motors every time.

The leader's handle didn't fit into its mount, so I widened the slot by 1 mm in CAD and reprinted it.

The first teleoperation, where I move the leader and the follower copies it, was rough. The follower moved slowly, the elbow motor reported an overload when I shut it down, and at startup the wrist moved on its own.

I traced the startup movement to LeRobot's code. It switched the motors on before telling them where to be, so they could jump toward an old target. I changed the order locally, and I fixed shutdown so it releases every motor even if one of them throws an error. I wrote tests that reproduced both bugs before I fixed them.

The slowness was my own fault. I'd added a speed limit as a "safety" measure, and all it did was make the follower lag and fill the screen with warnings. With the official command and no changes, it ran smoothly at about 60 updates a second. Lesson learned: start with the standard setup and change one thing at a time.

![Animated: leader and follower arms on a desk; the follower copies the leader's motion](media/2026-10-19-first-teleop.gif)

*First teleoperation: I move the leader arm (right) and the follower (left) copies it. [Full clip (MP4)](https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-10-19-first-teleop.mp4).*

## October 30: picking it back up

After a week and a half away, I checked all 12 motors before running anything. No faults, and the calibration stored in each motor still matched. The first start failed once with a communication error on the gripper, and running the same command again worked.

## November 4–8: camera mounts

<img src="media/2026-11-08-camera-stand.jpg" alt="Printed overhead camera tower with an InnoMaker camera board on top, next to the follower arm with its wrist camera" width="360">

I printed the official overhead camera stand (about 6 hours) and a wrist camera mount that replaces part of the follower's wrist. For the wrist mount, I compared six print orientations for finish, supports and strength before picking one. One plate of the stand failed when the first layer didn't stick, and the reprint came out fine.

## November 6: can my Mac run π0.5?

I timed π0.5 on my M3 Max MacBook. It took about 0.64 seconds to plan the next 1.7 seconds of motion, so the Mac should be able to keep up. That was the bare model with random weights, so real runs will be a little slower.

## November 8: calibration root cause and cameras

### The follower sat a few degrees off the leader

Even after I recalibrated both arms, the follower's base sat a few degrees to the left of the leader's. I also had to redo the leader once, because I'd forgotten to move the gripper during calibration. Checking the saved file caught it.

Reading LeRobot's source explained the offset. A joint's zero isn't the pose you hold at the start of calibration. It's the middle of the range you sweep through. The base can turn a long way in both directions, so how far I happened to swing it each way set its zero, and I'd swung the two arms differently. Their middles were about 7° apart.

I shifted the leader's saved range so the two middles matched, kept a backup, and left the follower's limits alone. Then I posed both arms the same way by hand and measured them: under half a degree apart. The wrist had the same problem, about 22° off, and after the same fix it was within a tenth of a degree.

### Cameras

| Overhead camera | Wrist camera |
| --- | --- |
| ![Robot's overhead camera view: the desk, an open toolkit and the follower arm at the bottom edge](media/2026-11-08-robot-view-overhead.jpg) | ![Robot's wrist camera view: the gripper jaws at the bottom with the desk ahead](media/2026-11-08-robot-view-wrist.jpg) |

At first my Mac found no cameras at all, because the terminal didn't have permission to use them.

Then the first run with both cameras stopped after 20 seconds because one feed went stale. Both cameras share one USB hub, so I blamed bandwidth and tried a compressed video setting. It turned out macOS ignores that setting, so it couldn't have been the fix. I found the real cause later that evening (below).

Looking at saved frames also showed the two cameras were labeled backwards. I fixed that before recording anything. Training with the views swapped would have taught the model the wrong thing.

![Animated: teleoperation with the Rerun viewer on the laptop showing both camera feeds and live joint plots](media/2026-11-08-teleop-with-cameras.gif)

*Teleoperation with both camera feeds and live joint plots on the laptop. [Full clip (MP4)](https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-teleop-with-cameras.mp4).*

## November 8 (evening): recording demonstrations

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
    <td><sub>I move the leader arm and the follower puts a bit strip in the toolbox. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-data-collection.mp4">MP4</a></sub></td>
    <td><sub>The recording page, sped up 2×. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-recording-page.mp4">MP4</a></sub></td>
    <td><sub>Replaying a recorded take. <a href="https://github.com/Jaxsonb04/so101-pi05/raw/main/media/2026-11-08-first-replay.mp4">MP4</a></sub></td>
  </tr>
</table>

The replay was the first time the follower moved without me driving it. It just repeats the recorded joint motions without looking at the cameras, and I'd moved the toolbox since recording, so it goes through the motions without picking anything up. Getting it to actually do the task is π0.5's job.

### A recording page instead of keyboard shortcuts

LeRobot's recorder is controlled with keyboard shortcuts, and they didn't fit how I wanted to work. I couldn't start a take when I was ready, or mark it as a pass or a fail. Stopping at the wrong moment could also lose a take: I lost a full one-minute take by pressing Ctrl+C during its reset pause.

So I built a small [recording page](tools/record_ui.py) around LeRobot's own recorder. It shows both cameras, and four keys start a take, mark it passed, mark it failed, or throw it away. Failed takes are kept with a label, since they're data too. Only passes count toward the goal, and it picks up where I left off if I stop and restart.

Before I used it on the robot, I had the code reviewed independently against LeRobot's source. That caught three real bugs, including one that would have crashed when resuming a session. I fixed them and added each case to a test that runs without the robot.

### Camera dropouts: the real cause

Recording kept stopping with "latest frame is too old", which just means the wrist camera didn't send anything for half a second.

The macOS system log told the real story. The wrist camera was physically disconnecting and reconnecting about 30 milliseconds later, at the exact moment each recording stopped. It came back so fast that it always looked connected. Over one evening it disconnected 193 times. The overhead camera, on the same hub, disconnected once.

That ruled out my code, since it happened even with nothing running. It also ruled out bandwidth, so my earlier theory was wrong. The problem is the wrist camera's cable or plug (which flexes as the arm moves), its port, or the camera itself. I decided not to add an automatic reconnect, because it would hide the problem without saving the take that got interrupted.

### Checking my own data

Before the real recording, I did 8 test takes and went through each one, looking at frames from both cameras and at the joint data.

Two of the "failed" takes weren't attempts at all, just one to five seconds of nothing, which is why the page now has a throw-away key. The frames also showed problems with the scene: my hand reaching into the overhead view, my laptop screen in the corner (its content changes between takes, which the model could latch onto), a dark image, and orange scraps that looked like the tools. I cleaned all of that up, and from then on only the tools moved between takes.

By the end of the night I had 21 real takes: 19 good and 2 failed.

## November 9: 50 demonstrations, then training

### Finishing the dataset

I recorded the rest of the demonstrations over two evenings and ended up with 52 takes: 50 good and 2 failed. The recording page picked up where I'd left off each time, which is exactly why I built it. The wrist camera kept dropping out, but luckily never in the middle of a take I kept.

Before training anything, I went through every take. All 50 good ones end with the three tools in the box. The joint data looked clean too, with no long pauses, no false starts, and every take starting from roughly the same pose. One take runs about twice as long as the rest because the arm missed a grab and went back for it. That's actually useful for the model to see.

One thing I didn't plan for: the toolbox ended up in four different spots across the takes. Most of them (38) are in the same place, so that's where I'll test first.

I also made a mistake in the review. My script jumped to the last frame of each video with a fast seek, which in these files lands a few seconds late. So I was really looking at the start of the next take, and some good takes looked unfinished. Decoding the videos frame by frame fixed it. Lesson learned: don't trust fast seeking on robot video.

### A model my Mac couldn't load

π0.5 is too big to train on a laptop, so training runs in the cloud on Hugging Face Jobs. My first 20-step test run failed almost immediately with a config error. LeRobot's cloud image had been updated to a newer version that same day, and it couldn't read the config my older local version sent it.

Getting around that produced a test model, so I checked whether my Mac could actually load it. It couldn't, because about half the weights had been renamed between versions. Without that check, I'd only have found out when I tried to run it on the arm.

The fix was to make the cloud job install the exact LeRobot and `transformers` versions I run locally before it starts training. The next test model matched my setup exactly. I also switched from an A100 to an H200 GPU, which ran more than twice as fast for twice the price.

### Training

I went with a full fine-tune and turned on image augmentation, since the recordings came from two sessions with different lighting. The run makes about five passes over the data and saves a checkpoint halfway and at the end, so I can try both on the arm. It started around 9 pm and should finish overnight. The training loss is dropping, which is a good sign, but the real test is whether the arm can actually do the task.

## Next

1. Fix the wrist camera's connection.
2. Run the trained model on the arm.
3. Score 20 attempts and compare the two checkpoints.
4. Add voice commands.
