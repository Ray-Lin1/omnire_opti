"""Export uncompressed RGB references at fixed held-out timestamps."""
import sys
from pathlib import Path
import imageio.v2 as imageio
import numpy as np
import torch
from omegaconf import OmegaConf
from datasets.driving_dataset import DrivingDataset
from utils.misc import import_str
from models.video_utils import render_images


@torch.no_grad()
def main():
    checkpoint=Path(sys.argv[1]); folder=checkpoint.parent
    cfg=OmegaConf.load(folder/'config.yaml')
    dataset=DrivingDataset(data_cfg=cfg.data)
    trainer=import_str(cfg.trainer.type)(**cfg.trainer,num_timesteps=dataset.num_img_timesteps,model_config=cfg.model,num_train_images=len(dataset.train_image_set),num_full_images=len(dataset.full_image_set),test_set_indices=dataset.test_timesteps,scene_aabb=dataset.get_aabb().reshape(2,3),device=torch.device('cuda'))
    trainer.resume_from_checkpoint(str(checkpoint),load_only_model=True)
    trainer.set_eval()
    dest=folder/'comparison_images'; dest.mkdir(exist_ok=True)
    for timestamp in [50,100,150]:
        data=render_images(trainer,dataset.full_image_set,compute_metrics=False,vis_indices=[timestamp*6+i for i in range(6)])
        for key in ['rgbs','gt_rgbs']:
            for cam,img in enumerate(data[key]):
                imageio.imwrite(dest/f't{timestamp:03d}_cam{cam}_{key}.png',(np.clip(img,0,1)*255).round().astype(np.uint8))


if __name__=='__main__':
    main()
