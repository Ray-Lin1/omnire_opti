"""Compose synchronized held-out experiment MP4s without resizing decoded views.

Run from repository root after restoring the local artifacts archive.
Requires numpy, Pillow, ffmpeg and ffprobe.
"""
from pathlib import Path
import json,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/experiments/comparisons/videos'
LOCAL=ROOT/'artifacts/20261108-fresh/combined-videos'
LABELS=['GT','Baseline | step 29381','EXP-001 | resume control 40k','EXP-002 | resume high-res 40k','EXP-003 | resume densify 40k','EXP-004 | scratch control 40k','EXP-005 | scratch high-res 40k']
EXPS=['exp-001-control','exp-002-resolution','exp-003-bg-densify','exp-004-from-scratch-control','exp-005-from-scratch-resolution']
PATHS=[ROOT/'docs/experiments/baseline-001/videos/scene0061_test_gt.mp4',ROOT/'docs/experiments/baseline-001/videos/scene0061_step29381_test_rgb.mp4']+[ROOT/'docs/experiments'/n/'test_rgb_step40000.mp4' for n in EXPS]
CAMERAS=[('CAM_FRONT',(533,0,1067,304)),('CAM_FRONT_LEFT',(0,0,533,304)),('CAM_FRONT_RIGHT',(1067,0,1600,304)),('CAM_BACK_LEFT',(0,304,533,608)),('CAM_BACK',(533,304,1067,608)),('CAM_BACK_RIGHT',(1067,304,1600,608))]

def probe(path):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_frames,duration','-of','json',str(path)],text=True))['streams'][0]

def read(path):
 meta=probe(path)
 assert (meta['width'],meta['height'],meta['nb_frames'],meta['avg_frame_rate'])==(1600,608,'19','2/1'),(path,meta)
 raw=subprocess.check_output(['ffmpeg','-v','error','-threads','2','-i',str(path),'-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
 frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,608,1600,3)
 assert len(frames)==19
 return list(frames)

class Writer:
 def __init__(self,path,width,height):
  self.process=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r','2','-i','pipe:0','-an','-c:v','libx264','-pix_fmt','yuv420p','-crf','16','-preset','medium','-threads','2','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
 def append(self,frame):self.process.stdin.write(frame.tobytes())
 def close(self):
  self.process.stdin.close()
  assert self.process.wait()==0

def decode_frame(path,index,width,height):
 raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(index/2),'-i',str(path),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
 return np.frombuffer(raw,dtype=np.uint8).reshape(height,width,3)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 LOCAL.mkdir(parents=True,exist_ok=True)
 frames=[read(p) for p in PATHS]
 print('Loaded seven synchronized 19-frame source videos',flush=True)
 gtpaths=[ROOT/'artifacts/20261107/exp-001-control/videos/test_set_40000_gt_rgbs.mp4',ROOT/'artifacts/20261107/exp-002-resolution/videos_eval/test_set_40000_gt_rgbs.mp4',ROOT/'artifacts/20261107/exp-003-bg-densify/videos/test_set_40000_gt_rgbs.mp4',ROOT/'artifacts/20261108-fresh/exp-004-from-scratch-control/eval_native/videos/test_gt.mp4',ROOT/'artifacts/20261108-fresh/exp-005-from-scratch-resolution/eval_common/videos/test_gt.mp4']
 checks=[]
 for path in gtpaths:
  other=read(path);mae=[]
  for i,a in enumerate(other):
   # Matching the closest decoded GT frame detects offsets in source timelines.
   errors=[float(np.abs(a.astype(np.int16)-b.astype(np.int16)).mean()) for b in frames[0]]
   assert int(np.argmin(errors))==i,(path,i,errors)
   assert errors[i]<3,(path,i,errors[i])
   mae.append(errors[i])
  checks.append({'path':str(path.relative_to(ROOT)),'aligned_frames':19,'max_decoded_gt_mae':max(mae)})
 print('Verified all five experiment GT timelines against baseline GT',flush=True)
 fontpath='C:/Windows/Fonts/arial.ttf'
 font=ImageFont.truetype(fontpath,19);small=ImageFont.truetype(fontpath,17)
 def panel(indices,cam,index,cols):
  name,box=cam;rows=(len(indices)+cols-1)//cols
  canvas=Image.new('RGB',(534*cols,336*rows+44),'#181c24');d=ImageDraw.Draw(canvas)
  for slot,source in enumerate(indices):
   x=(slot%cols)*534;y=(slot//cols)*336
   d.text((x+9,y+6),LABELS[source],font=font,fill='white')
   view=Image.fromarray(frames[source][index]).crop(box)
   canvas.paste(view,(x,y+32))
  if len(indices)==7:
   x=3*534;y=336
   for n,line in enumerate([name,'Held-out images; common resolution','Baseline: 29,381 steps','EXP-001 to EXP-005: 40,000 steps','No resizing of decoded camera crops','MP4 comparison only; metrics use originals']):
    d.text((x+12,y+18+n*35),line,font=small,fill='#d1d9e6')
  d.text((10,336*rows+10),f'{name} | held-out frame {index+1:02d}/19 | timestep {(index+1)*10:03d} | 2 FPS (slow playback)',font=small,fill='#d1d9e6')
  return np.asarray(canvas)
 specs=[('all_experiments_front.mp4',list(range(7)),CAMERAS[:1],4),('all_experiments_all_cameras.mp4',list(range(7)),CAMERAS,4),('control_exp004_exp005_all_cameras.mp4',[0,2,5,6],CAMERAS,2)]
 outputs=[]
 for filename,indices,cams,cols in specs:
  target=(OUT if filename=='all_experiments_front.mp4' else LOCAL)/filename
  writer=Writer(target,534*cols,336*((len(indices)+cols-1)//cols)+44)
  try:
   for cam in cams:
    for i in range(19):writer.append(panel(indices,cam,i,cols))
  finally:writer.close()
  meta=probe(target)
  assert int(meta['nb_frames'])==19*len(cams) and meta['avg_frame_rate']=='2/1'
  outputs.append({'filename':filename,'path':target.relative_to(ROOT).as_posix(),'bytes':target.stat().st_size,**meta})
  print(json.dumps(outputs[-1]),flush=True)
 # Decode middle and final frames to verify outputs and create a representative preview.
 for output in outputs:
  for index in [0,int(output['nb_frames'])//2,int(output['nb_frames'])-1]:
   im=decode_frame(ROOT/output['path'],index,output['width'],output['height'])
  if output['filename']=='all_experiments_front.mp4':Image.fromarray(decode_frame(ROOT/output['path'],9,output['width'],output['height'])).save(LOCAL/'preview.png')
 (ROOT/'artifacts/20261108-fresh/combined-video-verification.json').write_text(json.dumps({'passed':True,'gt_timeline_checks':checks,'outputs':outputs},indent=2))
 print('Verified output frame counts, dimensions, FPS, and decoded first/middle/final frames.',flush=True)

if __name__=='__main__':main()
