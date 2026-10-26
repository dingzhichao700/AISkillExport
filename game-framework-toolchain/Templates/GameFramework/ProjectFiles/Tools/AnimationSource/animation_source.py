"""Export and validate animation source deliveries. Requires Python 3.10+ and Pillow."""
import argparse
import json
import math
from pathlib import Path
import re
import shutil
import tempfile

from PIL import Image


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, low, high):
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def config_check(config, count):
    require(isinstance(config, dict), 'Configuration must be an object')
    require(set(config) <= {'duration', 'scale', 'pivot'}, 'Unknown configuration fields')
    duration = config.get('duration')
    require(type(duration) is int and duration >= max(1, count), 'duration must be an integer >= frame count')
    require(number(config.get('scale', 100), 10, 200), 'scale must be 10..200')
    pivot = config.get('pivot')
    require(isinstance(pivot, dict) and set(pivot) == {'x', 'y'}, 'pivot requires x/y only')
    require(all(number(pivot[k], 0, 1) for k in ('x', 'y')), 'pivot coordinates must be 0..1')


def png_info(path):
    with Image.open(path) as img:
        require(img.format == 'PNG' and img.mode in ('RGBA', 'LA'), f'{path}: requires a real Alpha channel')
        require(getattr(img, 'n_frames', 1) == 1, f'{path}: animated PNG is not a single frame')
        img.load()
        alpha = img.getchannel('A')
        hist = alpha.histogram()
        bounds = alpha.getbbox()
        return {'size': list(img.size), 'transparent': hist[0],
                'partialAlpha': sum(hist[1:255]), 'bounds': bounds,
                'touchesEdge': bool(bounds and (bounds[0] == 0 or bounds[1] == 0 or
                                               bounds[2] == img.width or bounds[3] == img.height))}


def validate_unit(folder):
    config = json.loads((folder / 'animation.json').read_text(encoding='utf-8-sig'))
    children = list(folder.iterdir())
    frames = [p for p in children if p.is_file() and re.fullmatch(r'[0-9]+\.png', p.name)]
    require(len(children) == len(frames) + 1, f'{folder}: only animation.json and numbered PNGs allowed')
    require(frames, f'{folder}: no frames')
    frames.sort(key=lambda p: int(p.stem))
    width = len(frames[0].stem)
    require(width >= max(3, len(str(len(frames)))), f'{folder}: numbering too narrow')
    require([p.name for p in frames] == [f'{i:0{width}d}.png' for i in range(1, len(frames) + 1)],
            f'{folder}: numbering must be continuous from 001 with uniform width')
    config_check(config, len(frames))
    info = [png_info(p) for p in frames]
    require(all(f['size'] == info[0]['size'] for f in info), f'{folder}: canvas sizes differ')
    return {'path': str(folder), 'name': folder.name, 'frameCount': len(frames),
            'config': config, 'frames': info,
            'visualReviewRequired': ['alignment', 'background contamination', 'unintended clipping',
                                     'confirmed duration and pivot']}


def validate(root):
    root = Path(root).resolve()
    require(root.is_dir(), f'Input directory missing: {root}')
    configs = sorted(root.rglob('animation.json'))
    require(configs, f'No animation.json found under {root}')
    units = {p.parent for p in configs}
    # A delivery root contains classifications and animation units, not auxiliary files.
    for p in root.rglob('*'):
        require(not p.is_symlink(), f'Symlinks are not delivery files: {p}')
        if p.is_file():
            require(p.parent in units, f'Auxiliary file outside animation unit: {p}')
    return [validate_unit(folder) for folder in sorted(units)]


def export(source, destination, duration, pivot_x, pivot_y, scale=100):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    require(source.is_dir(), 'Source directory does not exist')
    require(source != destination and source not in destination.parents and destination not in source.parents,
            'Source and destination must be separate directories')
    require(not destination.exists(), f'Refusing to overwrite: {destination}')
    frames = sorted((p for p in source.iterdir() if p.is_file() and re.fullmatch(r'[0-9]+\.png', p.name)),
                    key=lambda p: int(p.stem))
    require(frames, 'No numeric PNG source frames')
    require(len({int(p.stem) for p in frames}) == len(frames), 'Ambiguous duplicate frame numbers')
    config = {'duration': duration, 'scale': scale, 'pivot': {'x': pivot_x, 'y': pivot_y}}
    config_check(config, len(frames))
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Stage beside destination; validation failure cannot leave a partial animation.
    with tempfile.TemporaryDirectory(prefix='.animation-source-', dir=destination.parent) as staging:
        stage = Path(staging) / destination.name
        stage.mkdir()
        width = max(3, len(str(len(frames))))
        for i, frame in enumerate(frames, 1):
            shutil.copyfile(frame, stage / f'{i:0{width}d}.png')
        (stage / 'animation.json').write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        validate_unit(stage)
        stage.rename(destination)
    return validate_unit(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('validate')
    check.add_argument('root', type=Path)
    create = commands.add_parser('export')
    create.add_argument('source', type=Path)
    create.add_argument('destination', type=Path)
    create.add_argument('--duration', type=int, required=True)
    create.add_argument('--pivot-x', type=float, required=True)
    create.add_argument('--pivot-y', type=float, required=True)
    create.add_argument('--scale', type=float, default=100)
    args = parser.parse_args()
    try:
        result = validate(args.root) if args.command == 'validate' else export(
            args.source, args.destination, args.duration, args.pivot_x, args.pivot_y, args.scale)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    main()
