#!/usr/bin/env bash
# Practice and testing only. The same recording page (A start, B pass, C fail, live cameras),
# but into a separate practice dataset that is never uploaded and is wiped when the next
# practice run starts. Your real datasets are not touched. Stop any time with Ctrl+C.
#
#   tools/practice.sh
set -eo pipefail
cd "$(dirname "$0")/.."
source ~/miniforge3/bin/activate lerobot
source so101.env

practice="${HF_USER:?Set HF_USER in so101.env}/so101_practice"
rm -rf "${HF_LEROBOT_HOME:-$HOME/.cache/huggingface/lerobot}/$practice"  # last run's practice episodes

python tools/record_ui.py \
  --robot.type=so101_follower --robot.port="$FOLLOWER_PORT" --robot.id=follower --robot.cameras="$CAMERAS" \
  --teleop.type=so101_leader --teleop.port="$LEADER_PORT" --teleop.id=leader \
  --dataset.repo_id="$practice" --dataset.single_task="$TASK" \
  --dataset.num_episodes=100 --dataset.episode_time_s=120 \
  --dataset.push_to_hub=false --dataset.no_stamp=true \
  --dataset.streaming_encoding=true --dataset.encoder_threads=2
