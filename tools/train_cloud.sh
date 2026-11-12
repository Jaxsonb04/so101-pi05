#!/bin/bash
# Retrain π0.5 on Hugging Face Jobs (H200). LeRobot and transformers are pinned to the Mac's versions;
# torch and CUDA come from the lerobot-gpu image.
#   source so101.env
#   EXCLUDE="[2, 12, ...]" bash tools/train_cloud.sh            # add --dry-run to print the job without starting it
# EXCLUDE lists the episodes to leave out (failed or off-rule demos). STEPS should be ~2.5-3 passes over the
# kept frames: 2.8 x frames / 32. Checkpoints stay inside the job, and at the end only the model part
# (9.4 GB each, without the 15 GB optimizer state) of the last three is uploaded to ${POLICY}_v2, which fits
# a 100 GB private storage limit. Nothing reaches the Hub until the end. A run costs about $5 per hour.
set -e
: "${DATASET:?source so101.env first}" "${POLICY:?source so101.env first}" "${EXCLUDE:?set EXCLUDE to a list like [2, 12]}"
STEPS=${STEPS:-11000}
# checkpoints are saved every 1000 steps, so the three to upload only exist for whole thousands
if [ $((STEPS % 1000)) -ne 0 ] || [ "$STEPS" -lt 3000 ]; then echo "STEPS must be a multiple of 1000, at least 3000"; exit 1; fi
KEEP=$(for k in 2 1 0; do printf '"%06d", ' $((STEPS - k * 1000)); done)
REPO=${POLICY}_v2

hf jobs run --flavor h200 --timeout 9h --secrets HF_TOKEN --detach "$@" \
  huggingface/lerobot-gpu:latest \
  bash -c 'set -e
uv pip install --python /lerobot/.venv/bin/python "lerobot[pi] @ git+https://github.com/huggingface/lerobot@8c920c4270460851cedd2737657584586d3dc66f" "transformers==5.5.4"
python -c "import lerobot, transformers, torch; print(lerobot.__version__, transformers.__version__, torch.__version__)"
OUT=outputs/pi05_v2
# Keep the job disk small: drop optimizer states (only needed to resume) and checkpoints older than the
# three to upload, never touching the newest checkpoint, which may still be being written.
(trap "kill \$S 2>/dev/null; exit 0" TERM  # on kill, stop the sleep too, so it cannot linger
while true; do
  sleep 120 & S=$!; wait $S
  for d in $(ls -d $OUT/checkpoints/0* 2>/dev/null | sort | sed '"'\$d'"'); do
    rm -rf "$d/training_state"
    if [ "$(basename $d)" -lt '"$((STEPS - 2000))"' ]; then rm -rf "$d"; fi
  done
done) &
PRUNE=$!
STATUS=0
lerobot-train "$@" --output_dir=$OUT || STATUS=$?  # on a crash, still upload the checkpoints it saved
kill $PRUNE  # so nothing keeps the job (and its billing) alive after training
python - <<EOF
import os
from huggingface_hub import HfApi
api = HfApi()
api.create_repo("'"$REPO"'", private=True, exist_ok=True)
for s in ('"$KEEP"'):
    if not os.path.isdir(f"outputs/pi05_v2/checkpoints/{s}/pretrained_model"):
        print("not saved, skipping", s, flush=True); continue
    api.upload_folder(folder_path=f"outputs/pi05_v2/checkpoints/{s}/pretrained_model",
                      repo_id="'"$REPO"'", path_in_repo=f"checkpoints/{s}/pretrained_model")
    print("uploaded", s, flush=True)
EOF
exit $STATUS' _ \
  --dataset.repo_id=$DATASET \
  --dataset.exclude_episodes="$EXCLUDE" \
  --dataset.image_transforms.enable=true \
  --num_workers=8 \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --policy.repo_id=$REPO \
  --policy.private=true \
  --policy.push_to_hub=false \
  --policy.empty_cameras=1 \
  --policy.gradient_checkpointing=true \
  --policy.dtype=bfloat16 \
  --batch_size=32 \
  --steps=$STEPS \
  --save_freq=1000 \
  --job_name=pi05_v2
