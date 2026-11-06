# Runbook: SO-101 + π0.5

Work from top to bottom. The flags were checked against LeRobot 0.6.2, but none of these commands has been run on the arm yet.

## Before you start

Do this once:

```bash
cp so101.env.example so101.env
```

Then fill in the first five values in `so101.env`.

Do this in every new terminal, from this folder:

```bash
source ~/miniforge3/bin/activate lerobot
```

```bash
source so101.env
```

## 1. Get access

No hardware is needed for this step.

1. Create a token with **Write** access at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
2. Accept the license at [google/paligemma-3b-pt-224](https://huggingface.co/google/paligemma-3b-pt-224). π0.5 can't load its tokenizer without this.
3. Add credit at [huggingface.co/settings/billing](https://huggingface.co/settings/billing). Jobs need a positive balance. About $20 covers the plan below.
4. Log in:

```bash
hf auth login
```

5. Put your username in `so101.env` as `HF_USER`, then source the file again. This prints your username:

```bash
hf auth whoami
```

## 2. Finish the hardware

1. Check that the camera board's holes are about 27 mm apart. Both mounts are designed for that.
2. Print the [overhead stand](https://github.com/TheRobotStudio/SO-ARM100/tree/a758567c3978dfeefe282ede0500085a48fe8f78/Optional/Overhead_Cam_Mount_32x32_UVC_Module) and the [wrist mount](https://github.com/TheRobotStudio/SO-ARM100/tree/a758567c3978dfeefe282ede0500085a48fe8f78/Optional/Wrist_Cam_Mount_32x32_UVC_Module). Together they take about 8.5 hours and 260 g of filament, so check the spool first.
3. Test-fit each stand joint by hand, then assemble it with M2 screws.
4. With power off, swap the wrist mount in for `Wrist_Roll_Follower_SO101`. Note how the old part sits on the horn first, and keep it.
5. Recalibrate the follower, then the leader. At the existing-file prompt, type `c` and press Enter, because plain Enter reuses the old calibration. Use the same reference pose on both arms.

```bash
lerobot-calibrate --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower
```

```bash
lerobot-calibrate --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=leader
```

6. Mount the follower on the stand and fit both cameras.

Calibrate after the wrist swap, so you only do it once.

## 3. Check the cameras

```bash
lerobot-find-cameras opencv
```

This saves a test image from each camera. Use the images to set `WRIST_CAM` and `TOP_CAM` in `so101.env`, then source it again. The Mac's own camera also gets an index. Indexes can change after a replug, so recheck them each session.

Now teleoperate with both feeds on screen:

```bash
lerobot-teleoperate --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower --robot.cameras="$CAMERAS" --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=leader --display_data=true
```

Check that you could do the task yourself using only those two views. Support the follower before Ctrl+C, because stopping releases its holding torque.

## 4. Record demonstrations

Start with 5 test episodes:

```bash
lerobot-record \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower \
  --robot.cameras="$CAMERAS" \
  --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=leader \
  --display_data=true \
  --dataset.repo_id=${DATASET}_test \
  --dataset.num_episodes=5 \
  --dataset.single_task="$TASK" \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=15 \
  --dataset.private=true \
  --dataset.streaming_encoding=true \
  --dataset.encoder_threads=2
```

| Key | What it does |
| --- | --- |
| `→` or `n` | Ends the episode early |
| `←` or `r` | Discards the episode and re-records it |
| `Esc` or `q` | Stops, encodes the video and uploads |

If the keys do nothing, keep the Terminal window focused. LeRobot falls back to reading keys there without macOS Accessibility permission.

Replay one episode to check the recording:

```bash
lerobot-replay --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower --dataset.repo_id=${DATASET}_test --dataset.episode=0
```

Then run the same record command with `--dataset.repo_id=$DATASET` and `--dataset.num_episodes=50`.

- Use 5 object positions with 10 episodes each.
- Don't move the cameras between episodes.
- Grasp the same way each time, and keep the object in view.
- Leave `--dataset.private=true` on, because the overhead camera can see your room.

## 5. Fine-tune π0.5

This can't run on the Mac. It runs on a cloud A100 at $2.50 an hour, and the timeout caps the spend.

### Smoke test

This costs at most $1.25. It proves the cloud image, your dataset and checkpoint upload all work before you pay for the long run.

```bash
lerobot-train \
  --dataset.repo_id=$DATASET \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --policy.repo_id=${POLICY}_smoke \
  --policy.private=true \
  --policy.empty_cameras=1 \
  --policy.gradient_checkpointing=true \
  --policy.dtype=bfloat16 \
  --batch_size=32 \
  --steps=20 \
  --save_freq=20 \
  --save_checkpoint_to_hub=true \
  --output_dir=outputs/pi05_smoke \
  --job_name=pi05_smoke \
  --job.target=a100-large \
  --job.timeout=30m
```

Read the seconds per step from the log, then multiply by 10,000. If that's over 6 hours, raise `--job.timeout` below. Each extra hour adds $2.50.

Delete the smoke test model afterward:

```bash
hf repo delete ${POLICY}_smoke
```

### Full run

This costs at most $15.

```bash
lerobot-train \
  --dataset.repo_id=$DATASET \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --policy.repo_id=$POLICY \
  --policy.private=true \
  --policy.empty_cameras=1 \
  --policy.gradient_checkpointing=true \
  --policy.dtype=bfloat16 \
  --batch_size=32 \
  --steps=10000 \
  --save_freq=2500 \
  --save_checkpoint_to_hub=true \
  --output_dir=outputs/pi05_so101_cube_bin \
  --job_name=pi05_so101_cube_bin \
  --job.target=a100-large \
  --job.timeout=6h
```

Ctrl+C only detaches from the logs. The job keeps running and billing, so use these to watch or stop it:

```bash
hf jobs logs <job-id>
```

```bash
hf jobs cancel <job-id>
```

`--save_checkpoint_to_hub=true` matters: without it, a job that hits its timeout loses everything. Each saved checkpoint includes optimizer state, so expect the model repo to get large. Delete what you don't need afterward.

If the job times out, resume it:

```bash
lerobot-train --config_path=$POLICY --resume=true --job.target=a100-large --job.timeout=6h
```

## 6. Run it on the arm

Before every first run:

- Clamp the base and clear the workspace.
- Keep a hand near the follower's DC power. Pulling it is the physical stop.
- Start the arm in a pose close to where your demonstrations began.

Use the exact task text from recording. The first run downloads the model, and the first chunk takes about 5 seconds, so the arm will sit still briefly.

```bash
lerobot-rollout --strategy.type=base --policy.path=$POLICY --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower --robot.cameras="$CAMERAS" --task="$TASK" --duration=30 --device=mps
```

In this mode the arm pauses for about 0.65 s or more between chunks. That's expected. Once it works, try real-time chunking, which computes the next chunk while the arm is moving:

```bash
lerobot-rollout --strategy.type=base --inference.type=rtc --inference.rtc.execution_horizon=25 --inference.rtc.max_guidance_weight=10.0 --policy.path=$POLICY --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower --robot.cameras="$CAMERAS" --task="$TASK" --duration=30 --device=mps
```

The horizon is 25 here, not the docs' example of 10. At 30 FPS the Mac's inference delay is about 20 steps, and the horizon has to be longer than that delay.

## 7. Measure it

Run 20 scored trials. Use the leader arm to reset between trials.

```bash
lerobot-rollout \
  --strategy.type=episodic \
  --policy.path=$POLICY \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower \
  --robot.cameras="$CAMERAS" \
  --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=leader \
  --dataset.repo_id=$HF_USER/eval_so101_cube_bin \
  --dataset.num_episodes=20 \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=15 \
  --dataset.single_task="$TASK" \
  --dataset.private=true \
  --device=mps
```

For each trial, write down the object position, whether it succeeded and how it failed. Include some positions you didn't train on.

Then compare earlier checkpoints, because the last one isn't always the best. One published [SO-101 π0.5 run](https://huggingface.co/Project-IRA/TPSoSe2026_Pi05_LeRobot_SO101_Finetuning_V7_Full_V2) got its best real-arm results near step 8,000 and got worse after that. It was a different, much larger dataset, so treat that as a reason to check, not a prediction.

```bash
hf download $POLICY --include "checkpoints/005000/pretrained_model/*" --local-dir outputs/ckpts
```

Then use `--policy.path=outputs/ckpts/checkpoints/005000/pretrained_model` in the rollout command.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| `QUANTILES normalization mode requires q01 and q99 stats` | Add `--policy.normalization_mapping='{"ACTION": "MEAN_STD", "STATE": "MEAN_STD", "VISUAL": "IDENTITY"}'` to the train command. |
| 401 or 403 from `paligemma` | Accept the license in step 1, and check you're logged in with `hf auth whoami`. |
| A camera times out or shows black | Run `lerobot-find-cameras opencv` again, and try each camera on its own USB port. If that fails, add `fourcc: "MJPG"` to that camera in `CAMERAS`. |
| `No status packet` at startup | Run the same command again. This cleared on retry here before. |
| `Overload error` on a motor | Stop and cut DC power, then check for a jam or a pinched cable. The elbow did this once and the cause was never found. |
| The smoke test fails on a config key | The cloud image doesn't match your LeRobot version. Compare your version with the image, or pin one with `--job.image`. |
| The checkpoint won't load on the Mac | Same cause. The cloud image may be newer than your LeRobot 0.6.2. |
| The job timed out before finishing | Resume it as shown in step 5. The saved checkpoints are under `checkpoints/` in the model repo. |

## References

- [LeRobot π0.5 docs](https://huggingface.co/docs/lerobot/pi05)
- [LeRobot imitation learning guide](https://huggingface.co/docs/lerobot/il_robots)
- [Hugging Face Jobs pricing](https://huggingface.co/docs/hub/jobs-pricing)
- [Physical Intelligence openpi](https://github.com/Physical-Intelligence/openpi)
