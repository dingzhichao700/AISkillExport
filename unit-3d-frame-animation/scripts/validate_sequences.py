"""Read-only validation of 3D-rendered animation deliveries. Requires Pillow."""
import argparse,json,re,math
from pathlib import Path
from PIL import Image

def validate(root):
    root=Path(root).resolve();results=[];errors=[]
    configs=sorted(root.rglob('animation.json'))
    if not configs:errors.append('No animation.json found')
    for config in configs:
        item={'animation':str(config.parent.relative_to(root)),'errors':[]};e=item['errors']
        try:
            c=json.loads(config.read_text(encoding='utf-8-sig'))
            if set(c)!={'duration','scale','pivot'}:e.append('Expected only duration, scale, pivot')
            duration=c.get('duration');scale=c.get('scale');pivot=c.get('pivot',{})
            if type(duration)!=int or duration<1:e.append('Invalid duration')
            if type(scale) not in (int,float) or not math.isfinite(scale) or not 10<=scale<=200:e.append('Invalid scale')
            if not isinstance(pivot,dict) or set(pivot)!={'x','y'} or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in pivot.values()):e.append('Invalid pivot')
            children=list(config.parent.iterdir());pngs=sorted([p for p in children if p.suffix.lower()=='.png'],key=lambda p:int(p.stem) if p.stem.isdigit() else -1)
            if not pngs:e.append('No PNG frames')
            if any(not p.stem.isdigit() for p in pngs):e.append('Non-numeric PNG name')
            elif pngs:
                width=max(3,len(str(len(pngs))))
                if [p.name for p in pngs]!=[f'{i:0{width}d}.png' for i in range(1,len(pngs)+1)]:e.append('Non-contiguous or non-uniform numbering')
            if type(duration)==int and duration<len(pngs):e.append('Duration shorter than frame count')
            if any(p.name!='animation.json' and p not in pngs for p in children):e.append('Unexpected delivery entry')
            sizes=set()
            for p in pngs:
                with Image.open(p) as im:
                    im.load();sizes.add(im.size)
                    if 'A' not in im.getbands():e.append(p.name+': missing Alpha');continue
                    a=im.getchannel('A');w,h=im.size
                    if not a.getbbox():e.append(p.name+': empty frame')
                    if any(a.crop(box).getextrema()[1]>0 for box in [(0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)]):e.append(p.name+': non-transparent border')
            if len(sizes)!=1:e.append('Inconsistent canvas')
            item.update(frames=len(pngs),canvas=sorted(sizes),duration_ms=duration,pivot=pivot)
        except (ValueError,TypeError,KeyError,OSError) as ex:e.append(str(ex))
        results.append(item)
    # Reject images outside the animation leaves rather than silently ingesting review sheets.
    leaves={p.parent for p in configs}
    if any(p.parent not in leaves for p in root.rglob('*.png')):errors.append('PNG outside animation directory')
    return {'root':str(root),'animations':results,'errors':errors,'passed':not errors and all(not x['errors'] for x in results),'total_frames':sum(x.get('frames',0) for x in results)}

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    root=a.root.resolve();report=a.report.resolve()
    if report==root or root in report.parents:p.error('Report must be outside delivery root')
    result=validate(root);report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'passed':result['passed'],'animations':len(result['animations']),'frames':result['total_frames']}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
