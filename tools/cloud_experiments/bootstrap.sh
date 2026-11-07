#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/omnire_exp_20261107
exec >> "$ROOT/logs/bootstrap.log" 2>&1
trap 'echo "FAILED line=$LINENO code=$?"; touch "$ROOT/reports/bootstrap.failed"' ERR
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq build-essential ninja-build libgl1-mesa-dev libegl1-mesa-dev ffmpeg git
tar -xzf "$ROOT/incoming/source.tar.gz" -C "$ROOT"
CONDA=/home/vipuser/miniconda3/bin/conda
"$CONDA" create -y -p "$ROOT/env39" python=3.9 pip
export PATH="$ROOT/env39/bin:/usr/local/cuda-11.8/bin:$PATH"
export CUDA_HOME=/usr/local/cuda-11.8 TORCH_CUDA_ARCH_LIST=7.0 MAX_JOBS=4 FORCE_CUDA=1
export PIP_DEFAULT_TIMEOUT=60 PIP_RETRIES=2 PIP_DISABLE_PIP_VERSION_CHECK=1
export MPLBACKEND=Agg OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
python -m pip install 'pip<25' 'setuptools<70' wheel
python -m pip install --index-url https://download.pytorch.org/whl/cu118 'torch==2.0.0+cu118' 'torchvision==0.15.0+cu118'
python -m pip install -r "$ROOT/code/tools/cloud_experiments/requirements_cloud.txt"
python -m pip install --no-deps xformers==0.0.18
python -m pip install --no-build-isolation --no-deps gsplat==1.3.0
tar -xzf "$ROOT/incoming/pytorch3d-v0.7.5.tar.gz" -C "$ROOT/sources"
tar -xzf "$ROOT/incoming/nvdiffrast-v0.3.1.tar.gz" -C "$ROOT/sources"
python -m pip install --no-build-isolation --no-deps "$ROOT/sources/pytorch3d-0.7.5"
python -m pip install --no-build-isolation --no-deps "$ROOT/sources/nvdiffrast-0.3.1"
python -m pip install --no-deps -e "$ROOT/code/third_party/smplx"
mkdir -p /root/.cache/torch/hub/checkpoints
if [ -f "$ROOT/incoming/alexnet-owt-7be5be79.pth" ]; then
 cp "$ROOT/incoming/alexnet-owt-7be5be79.pth" /root/.cache/torch/hub/checkpoints/
fi
python -m pip freeze > "$ROOT/reports/requirements_resolved.txt"
python -m pip check > "$ROOT/reports/pip_check.txt"
python - <<'PY'
import torch, gsplat, pytorch3d, nvdiffrast, smplx, json, sys
from pathlib import Path
from pytorch3d.ops import knn_points
x=torch.rand(1,32,3,device='cuda',requires_grad=True)
v=knn_points(x,x,K=3); v.dists.sum().backward()
assert torch.isfinite(x.grad).all()
Path('/root/omnire_exp_20261107/reports/runtime.json').write_text(json.dumps(dict(python=sys.version,torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),knn_backward=True),indent=2))
PY
touch "$ROOT/reports/bootstrap.done"
echo "DONE $(date -Is)"
