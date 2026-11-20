"""Offline scene proof, review video, delivery inventory and verified ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def fresh(path):
    path = Path(path).resolve()
    if path.exists():
        raise ValueError('Output exists: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def scene(config, output):
    from PIL import Image
    cfg = json.loads(config.read_text(encoding='utf-8-sig'))
    image = Image.open(config.parent / cfg['background']).convert('RGBA')
    records = []
    for item in cfg['units']:
        source = (config.parent / item['frame']).resolve()
        frame = Image.open(source).convert('RGBA')
        scale = float(item['displayScale'])
        if not 0 < scale <= 100:
            raise ValueError('Invalid displayScale')
        size = tuple(max(1, round(v * scale)) for v in frame.size)
        frame = frame.resize(size, Image.Resampling.LANCZOS)
        px, py = item['pivot']
        if not (0 <= px <= 1 and 0 <= py <= 1):
            raise ValueError('Invalid pivot')
        x, y = item['anchor']
        origin = (round(x - px * size[0]), round(y - (1 - py) * size[1]))
        bounds = frame.getbbox()
        if bounds and (origin[0]+bounds[0] < 0 or origin[1]+bounds[1] < 0
                       or origin[0]+bounds[2] > image.width or origin[1]+bounds[3] > image.height):
            raise ValueError('Scene clips visible unit: ' + item['name'])
        image.alpha_composite(frame, origin)
        records.append(dict(item, sourceSha256=sha(source), displayedCanvas=size, alphaBounds=bounds))
    output = fresh(output)
    report = fresh(str(output)+'.json')
    image.save(output)
    report.write_text(json.dumps({'status':'awaiting-human-scale-review','units':records,
        'note':'Offline composition, not engine rendering.'}, ensure_ascii=False, indent=2), encoding='utf-8')

def check(manifest):
    cfg = json.loads(manifest.read_text(encoding='utf-8-sig'))
    errors, files = [], []
    def file(value):
        path = (manifest.parent / value).resolve()
        if not path.is_file() or path.stat().st_size == 0:
            errors.append('Missing/empty: ' + str(path))
        else:
            files.append({'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)})
    scale = cfg.get('scaleReview', {})
    if scale.get('status') != 'approved':
        errors.append('Scene scale not approved')
    for key in ('evidence','approval','geometryVersion'):
        if not scale.get(key): errors.append('Missing scaleReview.'+key)
    if scale.get('evidence'): file(scale['evidence'])
    required = cfg.get('requiredAnimations', [])
    animations = cfg.get('animations', [])
    if not required or len(required) != len(set(required)):
        errors.append('Missing/duplicate requiredAnimations')
    if sorted(a['key'] for a in animations) != sorted(required):
        errors.append('Animation inventory differs from contract')
    scales = set()
    for item in animations:
        directory = (manifest.parent / item['sequence']).resolve()
        config = directory / 'animation.json'
        file(str(config))
        if config.is_file(): scales.add(json.loads(config.read_text(encoding='utf-8-sig')).get('scale'))
        if not list(directory.glob('[0-9]*.png')): errors.append('No sequence: '+str(directory))
        if (len(item.get('atlases',[])) != 1 or len(item.get('playbackClips',[])) != 1) and not item.get('splitApproval'):
            errors.append('Expected one independent animation/atlas pair: '+item['key'])
        for pair in item.get('atlases',[]):
            file(pair['png']); file(pair['json'])
    if len(scales) != 1: errors.append('Inconsistent animation scales')
    previews = cfg.get('previews', {})
    for key in ['sceneTransitions'] + (['interruptedDeath'] if cfg.get('includesDeath') else []):
        if not previews.get(key): errors.append('Missing preview: '+key)
    for path in previews.values(): file(path)
    for key in ('sequences','atlasRestore','timingPivot'):
        entry = cfg.get('checks',{}).get(key,{})
        if entry.get('status') != 'passed': errors.append('Check not passed: '+key)
        if entry.get('evidence'): file(entry['evidence'])
        else: errors.append('Missing check evidence: '+key)
    return {'passed':not errors,'errors':errors,'files':files,
            'scope':'Inventory only; independently verify approval and report contents.'}

def archive(root, output):
    root, output = root.resolve(), output.resolve()
    if root == output or root in output.parents: raise ValueError('ZIP must be outside source root')
    files = sorted(p for p in root.rglob('*') if p.is_file())
    if not files: raise ValueError('Empty archive source')
    if any(p.is_symlink() or root not in p.resolve().parents for p in files):
        raise ValueError('External/symbolic links in archive source')
    output, report = fresh(output), fresh(str(output)+'.json')
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as z:
        for p in files: z.write(p,p.relative_to(root).as_posix())
    hashes = {}
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None or len(z.infolist()) != len(files): raise ValueError('ZIP integrity mismatch')
        for p in files:
            name = p.relative_to(root).as_posix()
            hashes[name] = sha(p)
            if hashlib.sha256(z.read(name)).hexdigest() != hashes[name]: raise ValueError('ZIP hash mismatch: '+name)
    report.write_text(json.dumps({'passed':True,'entries':hashes,'bytes':output.stat().st_size,
                                  'sha256':sha(output)},indent=2),encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command',required=True)
    for name in ('scene','check','archive'):
        sub = subs.add_parser(name); sub.add_argument('source',type=Path); sub.add_argument('output',type=Path)
    video = subs.add_parser('video')
    video.add_argument('frames',type=Path); video.add_argument('output',type=Path)
    video.add_argument('--ffmpeg',required=True); video.add_argument('--fps',required=True,type=float)
    args = parser.parse_args()
    if args.command == 'scene': scene(args.source,args.output)
    elif args.command == 'archive': archive(args.source,args.output)
    elif args.command == 'check':
        result = check(args.source)
        fresh(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        return 0 if result['passed'] else 2
    else:
        if not 0 < args.fps <= 240: raise ValueError('Invalid fps')
        frames = sorted(args.frames.glob('*.png'))
        if not frames or [p.name for p in frames] != [f'{i:06d}.png' for i in range(1,len(frames)+1)]:
            raise ValueError('Preview PNG frames must be contiguous, starting at 000001.png')
        output = fresh(args.output)
        subprocess.run([args.ffmpeg,'-nostdin','-v','error','-n','-framerate',str(args.fps),
            '-start_number','1','-i',str(args.frames/'%06d.png'),'-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2',
            '-c:v','libx264','-pix_fmt','yuv420p',str(output)],check=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
