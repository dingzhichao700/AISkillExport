"""Offline video analysis, explicit cuts and transparent PNG export. No interpolation."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def rate(value):
    a, b = value.split('/'); return float(a)/float(b)


def probe(video):
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_frames',
           '-show_entries', 'stream=width,height,r_frame_rate,avg_frame_rate:frame=best_effort_timestamp_time',
           '-of', 'json', str(video)]
    data = json.loads(subprocess.check_output(cmd))
    s = data['streams'][0]; fps = rate(s['r_frame_rate'])
    ts = [float(f['best_effort_timestamp_time']) for f in data['frames'] if 'best_effort_timestamp_time' in f]
    if fps <= 0 or len(ts) < 2 or np.max(np.abs(np.diff(ts)-1/fps)) > max(.002, .05/fps):
        raise ValueError('Variable/unknown frame timing; preserve or explicitly normalize before processing')
    return {'width': s['width'], 'height': s['height'], 'fps': fps, 'count': len(ts)}


def load_frames(video):
    cap = cv2.VideoCapture(str(video)); frames = []
    try:
        while True:
            ok, frame = cap.read()
            if not ok: break
            frames.append(frame)
    finally:
        cap.release()
    if not frames: raise ValueError('No decodable frames')
    return frames


def validate_range(start, length, count):
    if start < 1 or length < 2 or start-1+length > count:
        raise ValueError('Range must fit source: one-based start, length >= 2')


def sample_indices(start, length, count, loop=True):
    if count < 2 or count > length: raise ValueError('Count must be between 2 and source range length')
    offsets = [round(i*length/count) for i in range(count)] if loop else [round(i*(length-1)/(count-1)) for i in range(count)]
    return [start-1+x for x in offsets]


def analyze(video, output, min_seconds, max_seconds):
    meta = probe(video); fs = load_frames(video)
    if len(fs) != meta['count']: raise ValueError('Decoded frame count differs from probe')
    # Full-image metric intentionally conservative; never claims a semantic cycle.
    a = np.array([cv2.resize(f, (64,96)) for f in fs], dtype=np.float32)/255
    a = a[:,8:92,8:56]; v = np.diff(a, axis=0)
    lo = max(2, math.ceil(min_seconds*meta['fps'])); hi = min(len(fs)-1, math.floor(max_seconds*meta['fps']))
    if lo > hi: raise ValueError('No candidate length within requested window')
    rows = []
    for s in range(len(fs)-lo):
        for length in range(lo, min(hi, len(fs)-1-s)+1):
            e = s+length
            normal = float(np.mean(abs(v[s:e])))
            seam = float(np.mean(abs(a[e-1]-a[s])))
            match = float(np.mean(abs(a[e]-a[s])))
            velocity = float(np.mean(abs(v[s]-v[e-1])))
            rows.append({'start': s+1, 'length': length, 'seconds': length/meta['fps'],
                'score': match+.5*velocity, 'seam_ratio': seam/max(normal,1e-8), 'motion': normal})
    rows.sort(key=lambda r:r['score'])
    write(output, {'source': str(Path(video).resolve()), 'probe': meta, 'candidates': rows[:20],
        'full_source_seam_ratio': float(np.mean(abs(a[-1]-a[0])))/max(float(np.mean(abs(v))),1e-8),
        'semantic_cycle_verified': False, 'note': 'Inspect anatomy, leg identity, complete motion and stationary segments before selecting.'})


def cut(video, start, length, output, preview, repeats):
    meta = probe(video); validate_range(start,length,meta['count'])
    if repeats < 1: raise ValueError('Repeats must be positive')
    for path in [output, preview]:
        if Path(path).exists(): raise ValueError('Output exists; use a new candidate path')
        Path(path).parent.mkdir(parents=True,exist_ok=True)
    if Path(output).resolve() == Path(preview).resolve(): raise ValueError('Cycle and preview paths must differ')
    vf = f'trim=start_frame={start-1}:end_frame={start-1+length},setpts=PTS-STARTPTS'
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(video),'-vf',vf,'-an','-c:v','libx264','-crf','18',
        '-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
    subprocess.run(['ffmpeg','-v','error','-n','-stream_loop',str(repeats-1),'-i',str(output),'-an',
        '-c','copy','-movflags','+faststart',str(preview)],check=True)
    if probe(preview)['count'] != length*repeats: raise ValueError('Preview count mismatch')
    write(Path(output).with_suffix('.json'), {'source': str(Path(video).resolve()), 'start':start,'length':length,
        'fps':meta['fps'],'seconds':length/meta['fps'],'repeats':repeats,'motion_repair':False,'retimed':False})


def edge_connected_background(candidate):
    _, labels = cv2.connectedComponents(candidate.astype(np.uint8), connectivity=8)
    ids = np.unique(np.concatenate([labels[0],labels[-1],labels[:,0],labels[:,-1]]))
    return np.isin(labels, ids[ids != 0])


def matte(bgr, mode, key='FF00FF', tolerance=65, external=None):
    h,w = bgr.shape[:2]; rgb = bgr[:,:,::-1].astype(np.float32)
    if mode == 'masks':
        mask = Image.open(external).convert('L')
        if mask.size != (w,h): raise ValueError('External mask dimensions differ from video')
        alpha = np.array(mask)
    else:
        if mode == 'chroma':
            key = key.lstrip('#')
            if len(key) != 6: raise ValueError('Key must be six hex digits')
            color = np.array([int(key[i:i+2],16) for i in (0,2,4)])
            if not 0 < tolerance < 255: raise ValueError('Invalid chroma tolerance')
            bg = edge_connected_background(np.linalg.norm(rgb-color,axis=2) <= tolerance)
            solid = (~bg).astype(np.uint8)
        elif mode == 'warm-gray':
            warm = rgb[:,:,0]-rgb[:,:,2]
            seed = np.full((h,w),cv2.GC_PR_BGD,np.uint8)
            seed[(warm>3)|(rgb.max(2)<80)] = cv2.GC_PR_FGD
            # Ratios reproduce original margins without assuming one video resolution.
            seed[:max(1,round(h*.048))] = 0;seed[-max(1,round(h*.048)):] = 0
            seed[:,:max(1,round(w*.0935))] = 0;seed[:,-max(1,round(w*.081)):] = 0
            fg = ((warm>15)&(rgb.max(2)<215)).astype(np.uint8)
            k = max(3,round(min(h,w)*.011));k += 1-k%2
            fg = cv2.erode(fg,np.ones((k,k),np.uint8))
            seed[fg.astype(bool)] = cv2.GC_FGD
            cv2.setRNGSeed(140326)
            cv2.grabCut(bgr,seed,None,np.zeros((1,65)),np.zeros((1,65)),5,cv2.GC_INIT_WITH_MASK)
            solid = (~edge_connected_background(~np.isin(seed,[1,3]))).astype(np.uint8)
            n,cc,stats,_ = cv2.connectedComponentsWithStats(solid,8)
            if n < 2: raise ValueError('No foreground')
            solid = (cc == 1+np.argmax(stats[1:,cv2.CC_STAT_AREA])).astype(np.uint8)
        else: raise ValueError('Unsupported matte mode')
        alpha = np.uint8(cv2.GaussianBlur(solid.astype(np.float32),(3,3),.6)*255)
    if np.mean(alpha>0) < .005 or np.mean(alpha>0) > .95:
        raise ValueError('Implausible alpha coverage; inspect matte, do not deliver opaque fallback')
    rgba = np.dstack([rgb.astype(np.uint8),alpha]);rgba[alpha==0,:3]=0
    return Image.fromarray(rgba)


def place(image, profile, direction):
    geometry = profile['directions'][direction]
    body_fraction = float(geometry['body_height_fraction'])
    if not 0 < body_fraction <= 1: raise ValueError('Invalid reference body height fraction')
    scale = float(profile['target_body_height'])/(image.height*body_fraction)
    cw,ch = map(int,profile['canvas']);px,py = profile['pivot']
    ax,ay = geometry['ground_anchor']
    if min(cw,ch,scale) <= 0 or not (0<=ax<=1 and 0<=ay<=1 and 0<=px<cw and 0<=py<ch):
        raise ValueError('Invalid geometry/anchor')
    im = image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.LANCZOS)
    ox = round(px-ax*im.width);oy = round(py-ay*im.height)
    b = im.getbbox()
    if not b or b[0]+ox<1 or b[1]+oy<1 or b[2]+ox>cw-1 or b[3]+oy>ch-1:
        raise ValueError('Character clips shared canvas: revise profile for ALL related sets, do not auto-fit')
    dst = Image.new('RGBA',(cw,ch));dst.paste(im,(ox,oy))
    a=np.array(dst);a[a[:,:,3]==0,:3]=0
    return Image.fromarray(a),scale


def export(a):
    meta=probe(a.video);validate_range(a.start,a.length,meta['count'])
    indices=sample_indices(a.start,a.length,a.count,not a.one_shot)
    profile=read(a.profile);out=Path(a.out)
    if out.exists(): raise ValueError('Export directory exists; use a new output directory')
    if a.direction not in profile['directions']: raise ValueError('Direction missing from geometry profile')
    cap=cv2.VideoCapture(str(a.video));rendered=[];records=[]
    try:
        for j,i in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES,i);ok,bgr=cap.read()
            if not ok: raise ValueError('Could not decode selected frame')
            mask=Path(a.masks_dir)/f'{j+1:02d}.png' if a.masks_dir else None
            if a.matte=='masks' and mask is None: raise ValueError('--masks-dir required')
            im=matte(bgr,a.matte,a.key,a.tolerance,mask);dst,scale=place(im,profile,a.direction)
            alpha=np.array(dst)[:,:,3]
            if alpha[0].any() or alpha[-1].any() or alpha[:,0].any() or alpha[:,-1].any():
                raise ValueError('Opaque canvas border')
            n,_,stats,_=cv2.connectedComponentsWithStats((alpha>127).astype(np.uint8),8)
            if sum(area>2 for area in stats[1:,cv2.CC_STAT_AREA]) != 1:
                raise ValueError('Disconnected foreground: inspect accessories/artifacts')
            rendered.append(dst)
            records.append({'file':f'frames/{j+1:02d}.png','source_frame':i+1,
                'duration_ms':1000*a.length/meta['fps']/a.count,'visible_bbox':dst.getbbox()})
    finally:cap.release()
    # Write only after every frame passes. No partially validated asset set.
    (out/'frames').mkdir(parents=True)
    cw,ch=rendered[0].size;cols=min(4,a.count);rows=math.ceil(a.count/cols)
    cellw,cellh=cw*2+24,ch*2+32
    board=Image.new('RGB',(cols*cellw,rows*cellh),'#eeeeee');draw=ImageDraw.Draw(board)
    for j,im in enumerate(rendered):
        im.save(out/records[j]['file']);large=im.resize((cw*2,ch*2),Image.Resampling.NEAREST)
        bg=Image.new('RGBA',large.size,'#eeeeee');d=ImageDraw.Draw(bg)
        for y in range(0,bg.height,12):
            for x in range(0,bg.width,12):
                if (x//12+y//12)%2:d.rectangle((x,y,x+11,y+11),fill='#cccccc')
        bg.alpha_composite(large);x=j%cols*cellw;y=j//cols*cellh
        board.paste(bg.convert('RGB'),(x+12,y+24));draw.text((x+12,y+6),f'{j+1:02d}',fill='black')
    board.save(out/'overview.png')
    write(out/'animation.json',{'action':a.action,'direction':a.direction,'loop':not a.one_shot,
        'source_sha256':hashlib.sha256(Path(a.video).read_bytes()).hexdigest(),'source_fps':meta['fps'],
        'start':a.start,'length':a.length,'seconds':a.length/meta['fps'],'count':a.count,
        'geometry':profile,'scale':scale,'matte':a.matte,'key':a.key if a.matte=='chroma' else None,
        'tolerance':a.tolerance if a.matte=='chroma' else None,'frames':records,'interpolation':False,
        'qa':'Technical checks passed; agent must visually inspect all frames before delivery.'})


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('analyze');q.add_argument('--video',required=True);q.add_argument('--out',required=True)
    q.add_argument('--min-seconds',type=float,default=1);q.add_argument('--max-seconds',type=float,default=3)
    q=sub.add_parser('cut');q.add_argument('--video',required=True);q.add_argument('--start',type=int,required=True)
    q.add_argument('--length',type=int,required=True);q.add_argument('--out',required=True);q.add_argument('--preview',required=True)
    q.add_argument('--repeats',type=int,default=4)
    q=sub.add_parser('export');q.add_argument('--video',required=True);q.add_argument('--start',type=int,required=True)
    q.add_argument('--length',type=int,required=True);q.add_argument('--count',type=int,default=8)
    q.add_argument('--direction',required=True);q.add_argument('--profile',required=True);q.add_argument('--out',required=True)
    q.add_argument('--action',default='unspecified');q.add_argument('--one-shot',action='store_true')
    q.add_argument('--matte',choices=['warm-gray','chroma','masks'],required=True)
    q.add_argument('--key',default='FF00FF');q.add_argument('--tolerance',type=float,default=65);q.add_argument('--masks-dir')
    a=p.parse_args()
    if a.cmd=='analyze':analyze(a.video,a.out,a.min_seconds,a.max_seconds)
    elif a.cmd=='cut':cut(a.video,a.start,a.length,a.out,a.preview,a.repeats)
    else:export(a)
    print(json.dumps({'status':'complete','output':a.out}))


if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,subprocess.CalledProcessError) as exc:
        print(json.dumps({'error':str(exc)}));raise SystemExit(1)
