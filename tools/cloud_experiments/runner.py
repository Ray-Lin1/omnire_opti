"""Sequential cloud runs. Credentials are never read or stored by this script."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

ROOT = Path('/root/omnire_exp_20261107')
CODE = ROOT / 'code'
PY = str(ROOT / 'env39/bin/python')
DEADLINE = dt.datetime(2026, 11, 8, 6, tzinfo=dt.timezone(dt.timedelta(hours=8))).timestamp()


def status(**values):
    values['time'] = dt.datetime.now(dt.timezone.utc).isoformat()
    p = ROOT / 'reports/status.json'
    p.with_suffix('.tmp').write_text(json.dumps(values, indent=2))
    p.with_suffix('.tmp').replace(p)
    with (ROOT / 'logs/events.jsonl').open('a') as f:
        f.write(json.dumps(values) + '\n')


def run(cmd, log, env=None):
    with open(log, 'a') as f:
        return subprocess.call(cmd, cwd=CODE, env=env, stdout=f, stderr=subprocess.STDOUT)


def package(name, result):
    folder = ROOT / 'results/scene0061' / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'RESULT.json').write_text(json.dumps(result, indent=2))
    files = [p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    manifest = []
    for p in files:
        h = hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda: f.read(4*1024*1024), b''):
                h.update(b)
        manifest.append(dict(path=str(p.relative_to(folder)), bytes=p.stat().st_size, sha256=h.hexdigest()))
    (folder / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2))
    archive = ROOT / 'results' / (name + '.tar.gz')
    with tarfile.open(str(archive)+'.part', 'w:gz', compresslevel=1) as t:
        t.add(folder, arcname=name)
    Path(str(archive)+'.part').replace(archive)
    (ROOT / 'reports' / (name + '.ready.json')).write_text(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,result=result),indent=2))


def main():
    os.environ.update(PATH=str(ROOT/'env39/bin')+':/usr/local/cuda-11.8/bin:'+os.environ['PATH'], CUDA_HOME='/usr/local/cuda-11.8', TORCH_CUDA_ARCH_LIST='7.0', MAX_JOBS='4', MPLBACKEND='Agg', OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4', PYTHONUNBUFFERED='1', PYTHONPATH=str(CODE))
    status(stage='waiting_environment')
    while not (ROOT/'reports/bootstrap.done').exists():
        if (ROOT/'reports/bootstrap.failed').exists():
            status(stage='blocked', reason='bootstrap_failed'); return 1
        time.sleep(30)
    import yaml
    import torch
    import shutil
    model = ROOT/'incoming/checkpoint_final.pth'
    h=hashlib.sha256(model.read_bytes()).hexdigest()
    assert h == 'b35d159add7a01ae899b2aa321373181a92691ff6ec81cac4ac0b6867a5db7f4', h
    (CODE/'smpl_models').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'bundle/smpl_models/SMPL_NEUTRAL.pkl', CODE/'smpl_models/SMPL_NEUTRAL.pkl')
    ckpt=torch.load(model,map_location='cpu'); step=int(ckpt['step']); del ckpt
    assert step == 29381, step
    status(stage='smoke', baseline_step=step)
    common = ['--output_root',str(ROOT/'results'),'--project','scene0061','--resume_from',str(model)]
    for smoke, config, end in [('smoke_control','exp-001-control',29402),('smoke_densify','exp-003-bg-densify',29402)]:
        rc=run([PY,'tools/train.py','--config_file',f'configs/experiments/{config}.yaml',*common,'--run_name',smoke,f'trainer.optim.num_iters={end}','logging.vis_freq=0','trainer.optim.cache_buffer_freq=-1','render.render_full=false','render.render_test=false','render.render_novel=null'],ROOT/'logs'/f'{smoke}.log')
        if rc:
            status(stage='blocked',reason=smoke,exit_code=rc); return rc
    # Smoke includes a refinement boundary; all formal runs independently reload baseline.
    for name in ['exp-001-control','exp-002-resolution','exp-003-bg-densify']:
        if time.time() >= DEADLINE-3600:
            status(stage='skipped',experiment=name,reason='reserve_evaluation_and_return'); continue
        folder=ROOT/'results/scene0061'/name
        log=ROOT/'logs'/f'{name}.log'
        env=os.environ.copy()
        # Reserve time for the higher priority resolution comparison.
        end_time=min(DEADLINE, time.time()+(2.0*3600 if name=='exp-001-control' else 3.0*3600))
        env['OMNIRE_DEADLINE_EPOCH']=str(end_time)
        status(stage='training',experiment=name,deadline=end_time)
        start=time.time()
        rc=run([PY,'tools/train.py','--config_file',f'configs/experiments/{name}.yaml',*common,'--run_name',name],log,env)
        result=dict(experiment=name,train_exit=rc,seconds=time.time()-start,baseline_step=step)
        if (folder/'checkpoint_final.pth').exists():
            c=torch.load(folder/'checkpoint_final.pth',map_location='cpu'); result['final_step']=int(c['step']); del c
            status(stage='evaluating',experiment=name)
            # Common evaluation loads the exact same 533x300 GT and masks in every group.
            # Separate directories preserve native-resolution and common-resolution results.
            if name=='exp-002-resolution':
                eval_rc=run([PY,'tools/eval.py','--resume_from',str(folder/'checkpoint_final.pth'),'data.pixel_source.downscale_when_loading=[3,3,3,3,3,3]','render.render_novel=null'],ROOT/'logs'/f'{name}-common-eval.log')
                result['common_eval_exit']=eval_rc
            matched = folder/'checkpoint_35000.pth'
            if matched.exists():
                evaluation=folder/'comparison_35000'
                for sub in ['metrics_eval','videos_eval']:
                    (evaluation/sub).mkdir(parents=True,exist_ok=True)
                result['matched_eval_exit']=run([PY,'tools/eval.py','--resume_from',str(matched),f'log_dir={evaluation}','data.pixel_source.downscale_when_loading=[3,3,3,3,3,3]','render.render_full=false','render.render_novel=null'],ROOT/'logs'/f'{name}-matched-eval.log')
            result['images_exit']=run([PY,'tools/cloud_experiments/export_images.py',str(folder/'checkpoint_final.pth')],ROOT/'logs'/f'{name}-images.log')
            shutil.copy2(log,folder/'train.stdout.log')
            for p in (ROOT/'reports').glob('*'):
                if p.is_file() and p.suffix in ['.json','.txt']:
                    (folder/'environment').mkdir(exist_ok=True)
                    shutil.copy2(p,folder/'environment'/p.name)
        status(stage='packaging',experiment=name,result=result)
        package(name,result)
        status(stage='completed_experiment',experiment=name,result=result)
        if rc:
            status(stage='failed_experiment',experiment=name,exit_code=rc)
    status(stage='finished')
    return 0


if __name__ == '__main__':
    sys.exit(main())
