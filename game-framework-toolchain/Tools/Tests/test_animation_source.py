"""Behavioral tests plus a retained synthetic delivery outside the repository."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('animation_source', REPO / 'Templates/GameFramework/ProjectFiles/Tools/AnimationSource/animation_source.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def rejected(callback):
    try:
        callback()
    except (ValueError, OSError):
        return
    raise AssertionError('Invalid input was accepted')


def run(output):
    output = output.resolve()
    assert not output.exists(), 'Use a new verification directory'
    output.mkdir(parents=True)
    delivery = output / 'Delivery'
    with tempfile.TemporaryDirectory(prefix='animation-source-test-') as temp:
        source = Path(temp) / 'input'
        source.mkdir()
        # Synthetic reference points are defined by construction, not production defaults.
        cases = [('Characters/TestActor/Idle', (64, 80), 803, (0.5, 0.2)),
                 ('Effects/Pulse', (96, 96), 503, (0.5, 0.5))]
        for name, size, duration, pivot in cases:
            for i in range(1, 5):
                img = Image.new('RGBA', size)
                draw = ImageDraw.Draw(img)
                x, y = size[0] // 2, int(size[1] * (1 - pivot[1]))
                radius = 8 + i
                draw.ellipse((x-radius, y-radius*2, x+radius, y), fill=(70, 160, 240, 140))
                draw.ellipse((x-2, y-2, x+2, y+2), fill=(255, 200, 60, 255))
                img.save(source / f'{i}.png')
            dest = delivery / name
            result = tool.export(source, dest, duration, *pivot, scale=75)
            assert result['frameCount'] == 4
            for i in range(1, 5):
                assert (source / f'{i}.png').read_bytes() == (dest / f'{i:03}.png').read_bytes()
            assert all(f['partialAlpha'] > 0 and f['transparent'] > 0 and not f['touchesEdge'] for f in result['frames'])
            rejected(lambda: tool.export(source, dest, duration, *pivot))
        report = tool.validate(delivery)
        assert len(report) == 2
        assert len(tool.validate(delivery / cases[0][0])) == 1
        many = Path(temp) / 'many'
        many.mkdir()
        sample = Image.new('RGBA', (1, 1), (0, 0, 0, 120))
        for i in range(1, 1001):
            sample.save(many / f'{i}.png')
        wide = Path(temp) / 'wide'
        tool.export(many, wide, 1001, 0, 1)
        assert (wide / '0001.png').exists() and (wide / '1000.png').exists()
        assert not (wide / '001.png').exists()
        bad = Path(temp) / 'bad'
        tool.export(source, bad, 800, 0.5, 0.5)
        config = bad / 'animation.json'
        good = json.loads(config.read_text())
        omitted_scale = dict(good)
        omitted_scale.pop('scale')
        config.write_text(json.dumps(omitted_scale))
        tool.validate(bad)
        invalid = [dict(good, duration=3), dict(good, duration=True), dict(good, scale=201),
                   dict(good, pivot={'x': -0.1, 'y': 0.5}), dict(good, loop=True)]
        for value in invalid:
            config.write_text(json.dumps(value))
            rejected(lambda: tool.validate(bad))
        config.write_text(json.dumps(good))
        (bad / '002.png').rename(bad / '010.png')
        rejected(lambda: tool.validate(bad))
        (bad / '010.png').rename(bad / '002.png')
        (bad / 'frames').mkdir()
        rejected(lambda: tool.validate(bad))
        (bad / 'frames').rmdir()
        Image.new('RGB', (96, 96)).save(bad / '002.png')
        rejected(lambda: tool.validate(bad))
        Image.new('RGBA', (95, 96)).save(bad / '002.png')
        rejected(lambda: tool.validate(bad))
        (bad / '002.png').write_bytes(b'not png')
        rejected(lambda: tool.validate(bad))
        rejected(lambda: tool.export(bad, Path(temp) / 'failed', 800, 0.5, 0.5))
        assert not (Path(temp) / 'failed').exists()
    # Contact sheet outside Delivery, including a visible reference line.
    sheet = Image.new('RGB', (4 * 120, 2 * 120), '#353535')
    for row, (name, _, _, _) in enumerate(cases):
        for col, path in enumerate(sorted((delivery / name).glob('*.png'))):
            with Image.open(path) as img:
                sheet.paste(img, (col*120+12, row*120+12), img)
    sheet.save(output / 'contact-sheet.png')
    (output / 'validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (output / 'README.txt').write_text('Synthetic contract fixtures, not game art.\n'
        'Idle: 803ms, pivot (0.5,0.2), 64x80. Pulse: 503ms, pivot (0.5,0.5), 96x96.\n'
        '4 frames each; scale 75 is metadata only. Fixed gold reference marker; growing translucent shape.\n'
        'No source pixels transformed; no clipping by construction. Visual review remains required for real art.\n', encoding='utf-8')
    print(f'Animation source regression passed; delivery: {delivery}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
