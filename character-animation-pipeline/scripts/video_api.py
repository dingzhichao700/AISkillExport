"""Bailian submit-once/resume adapter. No keys, request image data or media URLs logged."""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

HOSTS = {'beijing': 'https://dashscope.aliyuncs.com',
         'singapore': 'https://dashscope-intl.aliyuncs.com'}


def save(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def request_json(url, key, payload=None):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None  # Never forward API credentials to a redirected host.
    headers = {'Authorization': 'Bearer '+key, 'Content-Type': 'application/json'}
    if payload is not None:
        headers['X-DashScope-Async'] = 'enable'
    req = urllib.request.Request(url, headers=headers,
        data=json.dumps(payload).encode('utf-8') if payload is not None else None)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError('API HTTP '+str(exc.code)) from None
    except (OSError, ValueError, urllib.error.URLError):
        raise RuntimeError('API transport/JSON failure; outcome may be unknown') from None


def config(path):
    c = read(path)
    if c.get('provider', 'bailian') != 'bailian' or c.get('region') not in HOSTS:
        raise ValueError('Unsupported provider/region; no fallback')
    env = c.get('key_env', 'QWEN_ANI')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', env):
        raise ValueError('Invalid environment-variable name')
    if not os.environ.get(env, '').strip():
        raise ValueError('Required credential environment variable is absent')
    ref = Path(c['reference'])
    if not ref.is_absolute():
        ref = Path(path).resolve().parent / ref
    if not ref.is_file() or not c.get('prompt') or not c.get('model'):
        raise ValueError('Reference, prompt and model are required')
    params = c.get('parameters', {})
    if c['model'] == 'wan2.6-i2v-flash':
        if params.get('resolution') not in ('720P', '1080P') or not 2 <= params.get('duration', 0) <= 15:
            raise ValueError('wan2.6-i2v-flash requires 720P/1080P and 2–15 seconds')
    c = {k: c[k] for k in ('provider', 'region', 'model', 'prompt', 'parameters') if k in c}
    c.update(key_env=env, reference=str(ref.resolve()))
    return c


def submit(config_path, run_dir):
    from PIL import Image
    c = config(config_path)
    key = os.environ[c['key_env']].strip()
    # Reject accidentally pasted credentials in public configuration fields.
    if key in json.dumps(c):
        raise ValueError('Credential must not occur in public configuration')
    image = Image.open(c['reference'])
    if image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] < 255:
        raise ValueError('Prepare an approved opaque video reference background first')
    if min(image.size) < 240 or max(image.size) > 8000:
        raise ValueError('Reference dimensions must be 240–8000 pixels')
    data = io.BytesIO()
    image.convert('RGB').save(data, format='JPEG', quality=95, subsampling=0)
    run = Path(run_dir); run.mkdir(parents=True, exist_ok=True)
    # Exclusive reservation survives crashes, and prevents concurrent/double POST.
    state_path = run/'state.json'
    state = {'status': 'submitting_outcome_unknown', 'config': c,
        'source_sha256': hashlib.sha256(Path(c['reference']).read_bytes()).hexdigest(),
        'transport': {'format': 'JPEG', 'quality': 95, 'size': list(image.size)}, 'task_id': None}
    with state_path.open('x', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    payload = {'model': c['model'], 'input': {'prompt': c['prompt'],
        'img_url': 'data:image/jpeg;base64,'+base64.b64encode(data.getvalue()).decode()},
        'parameters': c['parameters']}
    try:
        result = request_json(HOSTS[c['region']]+'/api/v1/services/aigc/video-generation/video-synthesis', key, payload)
        task = result.get('output', {}).get('task_id')
        if not isinstance(task, str) or not re.fullmatch(r'[A-Za-z0-9._-]+', task):
            raise RuntimeError('No valid task ID returned; do not resubmit automatically')
        state.update(task_id=task, status='submitted')
        save(state_path, state)
    except Exception:
        state['status'] = 'submission_outcome_unknown'
        save(state_path, state)
        raise
    return {'status': 'submitted', 'task_id': task, 'next': 'poll same run directory'}


def poll(run_dir):
    run = Path(run_dir); path = run/'state.json'; state = read(path)
    if state.get('status') == 'downloaded' and (run/'source.mp4').is_file():
        return {'status': 'downloaded', 'file': str(run/'source.mp4')}
    task = state.get('task_id')
    if not isinstance(task, str) or not re.fullmatch(r'[A-Za-z0-9._-]+', task):
        raise ValueError('No task ID; submission outcome unknown. Never auto-resubmit.')
    c = state['config']
    key = os.environ.get(c['key_env'], '').strip()
    if not key:
        raise ValueError('Credential unavailable; task ID retained')
    result = request_json(HOSTS[c['region']]+'/api/v1/tasks/'+task, key)
    output = result.get('output', {}); status = output.get('task_status')
    state['status'] = status or 'poll_response_unknown'; save(path, state)
    if status in ('FAILED', 'CANCELED', 'UNKNOWN'):
        raise RuntimeError('Provider task '+status+'; task ID retained')
    if status == 'SUCCEEDED':
        url = output.get('video_url', '')
        if not url.startswith('https://'):
            raise RuntimeError('Missing HTTPS video URL; resume same task')
        # No Authorization header on media download; URL never saved/printed.
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                data = response.read()
        except Exception:
            raise RuntimeError('Download failed; resume same task, no new submission') from None
        if b'ftyp' not in data[:32]:
            raise RuntimeError('Invalid MP4; resume same task')
        tmp = run/'source.part'; tmp.write_bytes(data); tmp.replace(run/'source.mp4')
        state.update(status='downloaded', video_sha256=hashlib.sha256(data).hexdigest(), usage=result.get('usage'))
        save(path, state)
        return {'status': 'downloaded', 'file': str(run/'source.mp4')}
    return {'status': state['status'], 'task_id': task, 'next': 'poll same run after about 10 seconds'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['validate', 'submit', 'poll'])
    p.add_argument('--config'); p.add_argument('--run-dir')
    a = p.parse_args()
    if a.command == 'validate':
        c = config(a.config); result = {'status': 'valid', 'model': c['model'], 'region': c['region']}
    elif a.command == 'submit':
        if not a.run_dir: p.error('--run-dir required')
        result = submit(a.config, a.run_dir)
    else:
        if not a.run_dir: p.error('--run-dir required')
        result = poll(a.run_dir)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # OSError / FileExistsError can carry paths, never emit a raw request or key.
        safe = str(exc) if isinstance(exc, (RuntimeError, ValueError)) else type(exc).__name__
        print(json.dumps({'error': safe, 'automatic_resubmit': False}, ensure_ascii=False))
        raise SystemExit(1)
