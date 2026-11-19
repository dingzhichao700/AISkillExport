"""Bounded remote verification; same-transaction strong ETag revalidation only."""
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Unexpected redirect from COS')


def strong_etag(value):
    return value if isinstance(value, str) and re.fullmatch(r'"[^"\x00-\x20\x7f]+"', value) else None


def get_object(url, etag=None):
    headers = {'Cache-Control': 'no-cache', 'Accept-Encoding': 'identity'}
    if etag:
        headers['If-None-Match'] = etag
    request = urllib.request.Request(url + '?verification=' + uuid.uuid4().hex, headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=90) as response:
            if response.status != 200:
                raise ValueError('Unexpected object response')
            return 200, response.read(), strong_etag(response.headers.get('ETag'))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return 404, b'', None
        if error.code == 304 and etag:
            observed = strong_etag(error.headers.get('ETag'))
            if observed == etag:
                return 304, b'', observed
            # Missing/mismatched validator cannot establish object identity.
            return get_object(url)
        raise


def trusted_stage(step, transaction, public, base, release):
    """Only a receipt hash anchored by the shared transaction may enable reuse."""
    try:
        raw = Path(step['evidence']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != step['sha256']:
            return {}
        receipt = json.loads(raw)
        if (receipt.get('transactionId'), receipt.get('publicRoot'), receipt.get('baseVersion'),
            receipt.get('release'), receipt.get('action')) != (transaction, public, base, release, 'stage'):
            return {}
        rows = receipt['files']
        if len({r['key'] for r in rows}) != len(rows):
            return {}
        return {r['key']: r for r in rows}
    except (OSError, KeyError, TypeError, ValueError):
        return {}


def verify_files(paths, root, public, action, upload, previous=None, workers=4):
    previous = previous or {}
    started = time.perf_counter()
    def verify(key):
        path = root / key
        data = path.read_bytes()
        expected = hashlib.sha256(data).hexdigest()
        old = previous.get(key, {})
        etag = strong_etag(old.get('etag')) if (action == 'activate' and
            old.get('sha256') == expected and old.get('bytes') == len(data)) else None
        status, remote, observed = get_object(public + key, etag)
        if status == 404 and action == 'stage':
            upload(key, path)
            status, remote, observed = get_object(public + key)
        if status == 304:
            if not etag or observed != etag:
                raise ValueError('Untrusted not-modified response: ' + key)
            mode = 'conditional-304'
        elif status == 200 and hashlib.sha256(remote).hexdigest() == expected:
            mode = 'full-sha256'
        else:
            raise ValueError('Missing or mismatched immutable resource: ' + key)
        return {'key': key, 'sha256': expected, 'bytes': len(data), 'etag': observed,
                'verification': mode, 'downloadedBytes': len(remote)}
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 4))) as pool:
        rows = list(pool.map(verify, sorted(paths)))
    stats = {'seconds': round(time.perf_counter()-started, 3), 'workers': max(1,min(workers,4)),
             'downloadedBytes': sum(r['downloadedBytes'] for r in rows),
             'conditionalReused': sum(r['verification']=='conditional-304' for r in rows),
             'fullDownloads': sum(r['verification']=='full-sha256' for r in rows)}
    return rows, stats
