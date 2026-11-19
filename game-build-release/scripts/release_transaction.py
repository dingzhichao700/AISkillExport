"""Persistent release transaction journal; no timeout or automatic lock stealing."""
import argparse
import contextlib
import hashlib
import json
import os
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path
from release_resource_gate import check as resource_preflight


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def now():
    return datetime.now(timezone.utc).isoformat()


def binding(project):
    config = read(Path(project) / 'ProjectSettings/FrameworkPlatform.json')
    bound = config.get('buildRelease', {}).get('releaseTransaction', {})
    require(all(bound.get(k) for k in ('stateRoot', 'projectId', 'environment')), 'Configure releaseTransaction stateRoot/projectId/environment')
    root = Path(bound['stateRoot'])
    require(root.is_absolute(), 'stateRoot must be absolute and shared across candidate checkouts')
    identity = {k: bound[k] for k in ('projectId', 'environment')}
    identity['bootstrapUrl'] = config.get('bootstrapUrl')
    return root.resolve(), identity


class Journal:
    def __init__(self, root, identity):
        self.root, self.identity = Path(root), identity

    @contextlib.contextmanager
    def edit(self):
        self.root.mkdir(parents=True, exist_ok=True)
        lock = self.root / '.journal.lock'
        try:
            fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError:
            raise ValueError('Journal lock exists; inspect owner/process/state; never auto-steal')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump({'host': socket.gethostname(), 'pid': os.getpid(), 'time': now()}, stream)
            path = self.root / 'transactions.json'
            data = read(path) if path.exists() else {'schema': 1, 'identity': self.identity, 'transactions': []}
            require(data['identity'] == self.identity, 'Environment identity mismatch')
            yield data
            temp = self.root / (uuid.uuid4().hex + '.tmp')
            with temp.open('w', encoding='utf-8') as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, path)
        finally:
            lock.unlink()

    @staticmethod
    def tx(data, txid, owner=None):
        tx = next((t for t in data['transactions'] if t['id'] == txid), None)
        require(tx is not None, 'Unknown transaction')
        if owner is not None:
            require(tx['owner'] == owner, 'Owner mismatch')
        return tx

    def register(self, request):
        fields = ('requestId', 'messageId', 'source', 'text', 'target', 'intent', 'buildKind', 'changes')
        require(all(request.get(k) for k in fields), 'Incomplete request provenance')
        require(request['intent'] in ('build', 'content', 'build-publish', 'publish', 'rollback'), 'Unknown intent')
        require(request['buildKind'] in ('base', 'content', 'none'), 'Explicit buildKind required')
        require(request['intent'] not in ('publish', 'rollback') or request['buildKind'] == 'none', 'Publish/rollback must use existing candidate')
        require(request['intent'] != 'content' or request['buildKind'] == 'content', 'Content request must retain base')
        with self.edit() as data:
            for tx in reversed(data['transactions']):
                for old in tx['requests']:
                    if old['requestId'] == request['requestId'] or old['messageId'] == request['messageId']:
                        require(all(old[k] == request[k] for k in ('text', 'target', 'intent', 'buildKind', 'changes')), 'Same request identity has conflicting payload')
                        if request not in tx['requests']:
                            tx['requests'].append(request)
                        return {'transactionId': tx['id'], 'duplicate': True, 'state': tx['state']}
            tx = next((t for t in data['transactions'] if t['state'] == 'registered' and t['target'] == request['target'] and t['intent'] == request['intent'] and t['buildKind'] == request['buildKind']), None)
            if tx is None:
                tx = {'id': uuid.uuid4().hex, 'target': request['target'], 'intent': request['intent'], 'buildKind': request['buildKind'], 'requests': [], 'state': 'registered', 'owner': None, 'steps': {}, 'created': now()}
                data['transactions'].append(tx)
            tx['requests'].append(request)
            return {'transactionId': tx['id'], 'duplicate': False, 'state': tx['state']}

    def freeze(self, txid, owner, candidate, baseline, input_manifest, project=None):
        require(owner and len(candidate) == 64 and all(c in '0123456789abcdef' for c in candidate), 'Owner and SHA256 input manifest required')
        require(isinstance(baseline, dict) and 'bootstrap' in baseline and isinstance(baseline.get('currents'), dict), 'Expected bootstrap/all current hashes required')
        verified = verify_input(input_manifest, candidate, project)
        with self.edit() as data:
            tx = self.tx(data, txid)
            require(tx['state'] == 'registered', 'Already frozen/terminal; do not start another pipeline')
            require(not any(t['state'] in ('frozen', 'running', 'failed') for t in data['transactions']), 'Environment has active/unresolved transaction')
            require(not any(t['state'] == 'registered' for t in data['transactions'][:data['transactions'].index(tx)]), 'Earlier queued transaction must run first')
            predecessor = next((t for t in data['transactions'] if t['id']==tx.get('supersedes')), {})
            governance = resource_preflight(verified['project'], input_manifest, 'freeze', transaction_id=txid, verified_input=verified, previous=predecessor.get('resourceGovernanceEvidence'))
            tx.update(state='frozen', owner=owner, candidateSha256=candidate, inputManifest=str(Path(input_manifest).resolve()), baseline=baseline, frozen=now())
            if governance:
                tx['resourceGovernanceFreeze'] = governance
                tx['resourceGovernanceEvidence'] = {'path':governance,'sha256':sha(Path(governance).read_bytes())}

    def begin(self, txid, owner, step, operation, project, worker_pid=None):
        with self.edit() as data:
            tx = self.tx(data, txid, owner)
            require(tx['state'] in ('frozen', 'running'), 'Transaction is not executable; resolve failure first')
            require(not tx.get('inFlight'), 'Operation active or unknown; inspect before recovery')
            require(step in ('prepare', 'generate', 'export', 'content', 'publish-local', 'stage', 'activate', 'rollback', 'archive'), 'Unknown step')
            require(step not in tx['steps'], 'Step already complete; reuse receipt')
            require(step not in ('publish-local', 'stage', 'activate', 'rollback') or tx['intent'] in ('build-publish', 'publish', 'rollback'), 'Build-only transaction cannot publish')
            require(not (tx['intent'] == 'content' and step in ('prepare', 'generate', 'export')), 'Content-only transaction cannot build new base')
            require(tx['intent'] not in ('publish', 'rollback') or step not in ('prepare', 'generate', 'export', 'content'), 'Publish/rollback cannot rebuild')
            require(tx['buildKind'] != 'content' or step not in ('prepare', 'generate', 'export'), 'Content candidate cannot rebuild base')
            require(tx['buildKind'] != 'base' or step != 'content', 'Base candidate cannot silently switch to content')
            verified = verify_input(tx['inputManifest'], tx['candidateSha256'], project)
            require(operation, 'Operation ID required')
            governance = resource_preflight(project, tx['inputManifest'], step, transaction_id=txid, verified_input=verified, previous=tx.get('resourceGovernanceEvidence')) if step != 'archive' else None
            if governance:
                tx['resourceGovernanceLatest'] = governance
                tx['resourceGovernanceEvidence'] = {'path':governance,'sha256':sha(Path(governance).read_bytes())}
            tx.update(state='running', inFlight={'step': step, 'operationId': operation, 'host': socket.gethostname(), 'journalPid': os.getpid(), 'workerPid': worker_pid, 'started': now()})
            return tx

    def finish(self, txid, owner, operation, evidence):
        with self.edit() as data:
            tx = self.tx(data, txid, owner)
            op = tx.get('inFlight')
            require(op and op['operationId'] == operation, 'Operation identity mismatch')
            require(Path(evidence).is_file(), 'Completion evidence missing')
            tx['steps'][op['step']] = {**op, 'completed': now(), 'evidence': str(Path(evidence).resolve()), 'sha256': sha(Path(evidence).read_bytes())}
            tx.pop('inFlight')

    def fail(self, txid, owner, operation):
        with self.edit() as data:
            tx = self.tx(data, txid, owner)
            require(tx.get('inFlight', {}).get('operationId') == operation, 'Operation mismatch')
            tx['state'] = 'failed'

    def resolve(self, txid, owner, evidence, completed=False):
        proof = read(evidence)
        require(proof.get('transactionId') == txid and proof.get('owner') == owner and proof.get('processesStopped') is True and proof.get('pointersReviewed') is True, 'Recovery requires explicit owner/process/pointer review')
        with self.edit() as data:
            tx = self.tx(data, txid, owner)
            op = tx.get('inFlight')
            require(op and proof.get('operationId') == op['operationId'], 'Recovery operation mismatch')
            tx.setdefault('recoveries', []).append({'evidence': str(Path(evidence).resolve()), 'sha256': sha(Path(evidence).read_bytes()), 'completed': completed, 'operation': op})
            if completed:
                tx['steps'][op['step']] = {**op, 'evidence': str(Path(evidence).resolve()), 'recovered': True}
            tx.pop('inFlight')
            tx['state'] = 'running'

    def deliver(self, txid, owner, evidence):
        with self.edit() as data:
            tx = self.tx(data, txid, owner)
            require(tx['state'] in ('frozen', 'running') and not tx.get('inFlight'), 'Unresolved operation')
            require(Path(evidence).is_file() and 'archive' in tx['steps'], 'Archive/delivery evidence required')
            if tx['intent'] in ('build-publish', 'publish', 'rollback'):
                require('activate' in tx['steps'] or 'rollback' in tx['steps'], 'Remote activation evidence missing')
            else:
                require('content' in tx['steps'] or 'export' in tx['steps'], 'Build evidence missing')
            tx.update(state='delivered-pending-acceptance', delivery=str(Path(evidence).resolve()), delivered=now())


    def supersede(self, txid, owner, evidence):
        proof = read(evidence)
        require(proof.get('transactionId') == txid and proof.get('owner') == owner and proof.get('processesStopped') is True and proof.get('pointersReviewed') is True and proof.get('reason'), 'Supersede needs owner/process/pointer review and reason')
        with self.edit() as data:
            tx = self.tx(data, txid, owner)
            require(tx['state'] in ('frozen', 'running', 'failed'), 'Only unresolved frozen transaction may be superseded')
            if tx.get('inFlight'):
                require(proof.get('operationId') == tx['inFlight']['operationId'], 'Unknown operation was not reviewed')
            successor = {'id': uuid.uuid4().hex, 'target': tx['target'], 'intent': tx['intent'], 'buildKind': tx['buildKind'], 'requests': list(tx['requests']), 'state': 'registered', 'owner': None, 'steps': {}, 'created': now(), 'supersedes': txid}
            tx.update(state='superseded', successor=successor['id'], supersedeEvidence=str(Path(evidence).resolve()))
            data['transactions'].append(successor)
            return {'transactionId': successor['id'], 'state': 'registered'}

    def cancel(self, txid, evidence):
        require(Path(evidence).is_file(), "Cancellation evidence required")
        with self.edit() as data:
            tx = self.tx(data, txid)
            require(tx['state'] == 'registered', 'Only queued/unfrozen requests may be cancelled here')
            tx.update(state='cancelled', cancellation=str(Path(evidence).resolve()))


def scoped_files(root, scopes, excludes):
    actual = set()
    for scope in scopes:
        folder = (root / scope).resolve()
        require(folder == root or root in folder.parents, 'Unsafe input scope')
        require(folder.is_dir(), 'Source scope must be an existing directory')
        for file in folder.rglob('*'):
            if file.is_file():
                relative = file.relative_to(root).as_posix()
                if not any(relative == e.rstrip('/') or relative.startswith(e.rstrip('/') + '/') for e in excludes):
                    actual.add(relative)
    return actual


def verify_input(manifest, expected, project=None):
    path = Path(manifest)
    require(path.is_file() and sha(path.read_bytes()) == expected, 'Frozen input manifest hash changed')
    data = read(path)
    root = Path(data['project']).resolve()
    require(project is None or root == Path(project).resolve(), 'Frozen input belongs to another execution project')
    require(data.get('files'), 'Input manifest must list reviewed source files')
    seen = set()
    for entry in data['files']:
        relative = entry['path']
        file = (root / relative).resolve()
        require(not Path(relative).is_absolute() and root in file.parents and relative not in seen, 'Unsafe/duplicate input path')
        seen.add(relative)
        require(file.is_file() and sha(file.read_bytes()) == entry['sha256'], 'Frozen input changed: ' + relative)
    # Explicit scopes catch additions/deletions as well as changed listed files.
    scopes = data.get('scopes', [])
    require(scopes, 'Input manifest needs explicit source scopes')
    actual = scoped_files(root, scopes, data.get('excludes', []))
    require(actual == seen, 'Frozen source scope additions/deletions or incomplete manifest')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--action', required=True, choices=('inspect', 'register', 'freeze', 'begin', 'complete-unity', 'resolve', 'deliver', 'cancel', 'complete-archive', 'snapshot-input', 'supersede'))
    for name in ('transaction', 'owner', 'request', 'candidate', 'baseline', 'step', 'operation', 'evidence', 'input-manifest'):
        parser.add_argument('--' + name)
    parser.add_argument('--worker-pid', type=int)
    parser.add_argument('--scope', action='append')
    parser.add_argument('--exclude', action='append', default=[])
    parser.add_argument('--output')
    parser.add_argument('--completed', action='store_true')
    args = parser.parse_args()
    if args.action == 'snapshot-input':
        require(args.scope and args.output, 'Explicit source scopes/output required')
        project = Path(args.project).resolve()
        resource_preflight(project, phase='before-snapshot', transaction_id=args.transaction)
        files = scoped_files(project, args.scope, args.exclude)
        manifest = {'project': str(project), 'scopes': args.scope, 'excludes': args.exclude, 'files': [{'path': relative, 'sha256': sha((project / relative).read_bytes())} for relative in sorted(files)]}
        output = Path(args.output)
        output.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print(json.dumps({'inputManifest': str(output.resolve()), 'candidateSha256': sha(output.read_bytes()), 'files': len(files)}))
        return
    root, identity = binding(args.project)
    journal = Journal(root, identity)
    if args.action == 'inspect':
        print(json.dumps({'root': str(root), 'journal': read(root / 'transactions.json') if (root / 'transactions.json').exists() else None, 'lockExists': (root / '.journal.lock').exists()}, ensure_ascii=False))
        return
    if args.action == 'register':
        result = journal.register(read(args.request))
    elif args.action == 'freeze':
        result = journal.freeze(args.transaction, args.owner, args.candidate, read(args.baseline), args.input_manifest, args.project)
    elif args.action == 'begin':
        result = journal.begin(args.transaction, args.owner, args.step, args.operation, args.project, args.worker_pid)
    elif args.action == 'complete-unity':
        proof = read(args.evidence)
        with journal.edit() as data:
            tx = journal.tx(data, args.transaction, args.owner)
            op = tx.get('inFlight', {})
            expected = {'prepare': 'prepared', 'generate': 'generated', 'export': 'exported', 'content': 'content-built', 'publish-local': 'published-locally'}.get(op.get('step'))
            require(expected and proof.get('requestId') == args.operation and proof.get('status') == expected, 'Unity result identity/terminal mismatch')
        result = journal.finish(args.transaction, args.owner, args.operation, args.evidence)
    elif args.action == 'supersede':
        result = journal.supersede(args.transaction, args.owner, args.evidence)
    elif args.action == 'cancel':
        result = journal.cancel(args.transaction, args.evidence)
    elif args.action == 'complete-archive':
        proof = read(args.evidence)
        with journal.edit() as data:
            tx = journal.tx(data, args.transaction, args.owner)
            require(tx.get('inFlight', {}).get('step') == 'archive' and proof.get('transactionId') == args.transaction and proof.get('candidateSha256') == tx['candidateSha256'], 'Archive evidence identity mismatch')
        require(proof.get('files'), 'Archive files required')
        for entry in proof['files']:
            require(sha(Path(entry['path']).read_bytes()) == entry['sha256'], 'Archive hash mismatch')
        result = journal.finish(args.transaction, args.owner, args.operation, args.evidence)
    elif args.action == 'resolve':
        result = journal.resolve(args.transaction, args.owner, args.evidence, args.completed)
    else:
        result = journal.deliver(args.transaction, args.owner, args.evidence)
    print(json.dumps({'ok': True, 'result': result}, ensure_ascii=False))


if __name__ == '__main__':
    main()
