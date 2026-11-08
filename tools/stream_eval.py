"""Bounded-memory evaluation using OmniRe's original per-image renderer."""
import argparse,json,logging
from pathlib import Path
import imageio.v2 as imageio
import numpy as np
import torch
from omegaconf import OmegaConf
from datasets.driving_dataset import DrivingDataset
from utils.misc import import_str
from utils.visualization import to8b
from models import video_utils as video

KEYS=['psnr','ssim','lpips','occupied_psnr','occupied_ssim','masked_psnr','masked_ssim','human_psnr','human_ssim','vehicle_psnr','vehicle_ssim']
def aggregate(rows):
    return {k:sum(r[k] for r in rows if r[k]!=-1)/sum(r[k]!=-1 for r in rows) if any(r[k]!=-1 for r in rows) else -1 for k in KEYS}

@torch.no_grad()
def main():
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--out',required=True);p.add_argument('--downscale',type=int);args=p.parse_args()
    checkpoint=Path(args.checkpoint);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    cfg=OmegaConf.load(checkpoint.parent/'config.yaml')
    if args.downscale:cfg.data.pixel_source.downscale_when_loading=[args.downscale]*len(cfg.data.pixel_source.cameras)
    OmegaConf.save(cfg,str(out/'config.yaml'))
    logging.getLogger().setLevel(logging.ERROR);video.tqdm=lambda iterable,**kwargs:iterable
    dataset=DrivingDataset(data_cfg=cfg.data)
    trainer=import_str(cfg.trainer.type)(**cfg.trainer,num_timesteps=dataset.num_img_timesteps,model_config=cfg.model,num_train_images=len(dataset.train_image_set),num_full_images=len(dataset.full_image_set),test_set_indices=dataset.test_timesteps,scene_aabb=dataset.get_aabb().reshape(2,3),device=torch.device('cuda'))
    trainer.resume_from_checkpoint(str(checkpoint),load_only_model=True);trainer.set_eval();trainer.render_each_class=False
    batch=video.render_images(trainer,dataset.full_image_set,compute_metrics=True,vis_indices=list(range(6)))
    sample=[];rgb_error=0.
    for i in range(6):
        d=video.render_images(trainer,dataset.full_image_set,compute_metrics=True,vis_indices=[i]);sample.append({k:d[k] for k in KEYS})
        rgb_error=max(rgb_error,float(np.abs(batch['rgbs'][i]-d['rgbs'][0]).max()))
    errors={k:abs(v-batch[k]) for k,v in aggregate(sample).items()};assert max(errors.values())<1e-6 and rgb_error<1e-6
    (out/'aggregation_check.json').write_text(json.dumps({'passed':True,'metric_errors':errors,'rgb_error':rgb_error},indent=2));del batch,d
    videos=out/'videos';videos.mkdir(exist_ok=True);images=out/'images';images.mkdir(exist_ok=True)
    writers={(s,k):imageio.get_writer(videos/f'{s}_{k}.mp4',fps=10 if s=='full' else 2) for s in ['full','test'] for k in ['rgb','gt']}
    rows=[];test_rows=[];frames={'rgb':[],'gt':[]};names=[];cams=dataset.pixel_source.num_cams
    test_times={int(t) for t in dataset.test_timesteps}
    try:
        with (out/'per_image_metrics.jsonl').open('w') as log:
            for i in range(len(dataset.full_image_set)):
                d=video.render_images(trainer,dataset.full_image_set,compute_metrics=True,vis_indices=[i]);t,cam=divmod(i,cams)
                row={k:float(d[k]) for k in KEYS};rows.append(row)
                if t in test_times:test_rows.append(row)
                log.write(json.dumps({'image_index':i,'metrics':row})+'\n')
                for key,source in [('rgb','rgbs'),('gt','gt_rgbs')]:
                    frame=d[source][0];frames[key].append(frame)
                    if t in [50,100,150]:imageio.imwrite(images/f't{t:03d}_cam{cam}_{key}.png',to8b(frame))
                names.append(d['cam_names'][0])
                if len(names)==cams:
                    for key in frames:
                        mosaic=to8b(dataset.layout(frames[key],names));writers[('full',key)].append_data(mosaic)
                        if t in test_times:writers[('test',key)].append_data(mosaic)
                    frames={'rgb':[],'gt':[]};names=[]
                if i%60==0:(out/'progress.json').write_text(json.dumps({'images':i+1,'total':len(dataset.full_image_set)}))
                del d
    finally:
        for w in writers.values():w.close()
    for split,values in [('full',rows),('test',test_rows)]:
        (out/f'metrics_{split}.json').write_text(json.dumps({f'image_metrics/{split}/{k}':v for k,v in aggregate(values).items()},indent=2))
    (out/'RESULT.json').write_text(json.dumps({'step':int(trainer.step),'full_images':len(rows),'test_images':len(test_rows),'full_frames':len(rows)//cams,'test_frames':len(test_rows)//cams,'load_downscale':list(cfg.data.pixel_source.downscale_when_loading)},indent=2))
if __name__=='__main__':main()
