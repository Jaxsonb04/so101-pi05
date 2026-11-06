# SO-101 + π0.5

I built a pair of [SO-101](https://github.com/TheRobotStudio/SO-ARM100) robot arms. Next I'm teaching the follower arm a real task: record my own demonstrations, fine-tune [π0.5](https://www.physicalintelligence.company/blog/pi05) on them, and run the result on the arm.

π0.5 is Physical Intelligence's open vision-language-action model. It takes camera images, the arm's joint positions and a text instruction, and outputs a chunk of 50 joint targets. I'm using the [LeRobot](https://github.com/huggingface/lerobot) port.

**Status, November 6, 2026:** the arms are built and teleoperation works. The cameras aren't installed yet, no data has been recorded, and π0.5 hasn't been trained or run on this arm.

Every step below has its commands in the **[runbook](RUNBOOK.md)**.

## What I'm about to do

### 1. Get access

- [ ] Log in to Hugging Face with a write token
- [ ] Accept the PaliGemma license, which π0.5's tokenizer needs
- [ ] Add credit for cloud training

### 2. Finish the hardware

- [ ] Print the overhead camera stand
- [ ] Print the wrist camera mount
- [ ] Swap the wrist mount onto the follower
- [ ] Recalibrate both arms, to correct the follower sitting slightly left of center
- [ ] Mount the follower on the stand and fit both cameras

### 3. Check the cameras

- [ ] Identify the wrist and overhead cameras
- [ ] Teleoperate with both camera feeds on screen

### 4. Record demonstrations

- [ ] Record 5 test episodes and replay one
- [ ] Record 50 episodes: 10 at each of 5 object positions

### 5. Fine-tune π0.5

- [ ] Run a 20-step smoke test in the cloud
- [ ] Run the full 10,000-step fine-tune

### 6. Run it on the arm

- [ ] Run a 30-second first test
- [ ] Try real-time chunking for smoother motion

### 7. Measure it

- [ ] Run 20 scored trials
- [ ] Compare checkpoints
- [ ] Publish the success rate and what went wrong

## The plan at a glance

| Decision | Choice | Why |
| --- | --- | --- |
| First task | Pick up a cube, place it in a bin | LeRobot's suggested starting task. It's one setting, so it's easy to change. |
| Cameras | Wrist and overhead, 640×480 at 30 FPS | Two InnoMaker 32×32 mm boards on the official mounts. |
| Third camera slot | Masked with `--policy.empty_cameras=1` | `pi05_base` has three camera slots and this arm has two cameras. |
| Demonstrations | 50 to start | LeRobot's suggested minimum. The SO-101 π0.5 fine-tunes I found used 100 or more, so I may need to add some. |
| Training | Full fine-tune on one A100 80 GB, on Hugging Face Jobs | LeRobot sizes its π0.5 recipe for a single 80 GB GPU. |
| Training cost | $2.50 an hour, capped with a timeout | The smoke test costs at most $1.25 and the full run at most $15. |
| Inference | On my M3 Max MacBook | No rented GPU needed, based on the timing below. |

## Measured so far

These checks ran without the robot.

- **π0.5 speed on an M3 Max:** 0.64 s per 50-action chunk, using 9.2 GiB in bfloat16. That chunk covers 1.67 s of motion at 30 FPS, so the Mac is fast enough on paper. The first chunk took about 5 s. This timed the model alone on random weights, so real runs will be slower once cameras and preprocessing are included.
- **Real-time chunking on the same Mac:** 0.66 s per chunk, using 9.3 GiB. I counted its guidance steps to confirm they really ran, because the time was so close to plain inference.
- **Commands:** every record, train and rollout command in the runbook parses against LeRobot 0.6.2. Parsing proves the flags are valid, not that the runs will work.

## Not tested yet

- Anything with π0.5 on the real arm
- The cloud training job, which is why the smoke test comes first
- Loading a cloud-trained checkpoint on the Mac, because the cloud image may be newer than my LeRobot 0.6.2

## The build

- **Arms:** one leader and one follower, 3D printed on a Bambu P1S
- **Motors:** 12 Feetech STS3215, with the official gear ratios for each arm
- **Controllers:** 2 Waveshare Bus Servo Adapter (A) boards
- **Software:** LeRobot 0.6.2 on Apple silicon

## Credits

Arm design by [TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100). π0.5 by [Physical Intelligence](https://github.com/Physical-Intelligence/openpi). Robot software by [Hugging Face LeRobot](https://github.com/huggingface/lerobot).
