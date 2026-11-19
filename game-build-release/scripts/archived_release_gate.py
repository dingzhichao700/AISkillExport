"""Opt-in, transaction-bound validation of an already built immutable candidate."""
import hashlib
import json
import uuid
from pathlib import Path


def check_archived(g, project, bound, transaction_id, input_manifest, previous):
    reference = bound.get('archivedPublish', {}).get(transaction_id)
    if not reference:
        return None
    g.ensure(g.digest(reference['path']) == reference['sha256'], 'Archived binding changed')
    permit = g.load(reference['path'])
    g.ensure(permit.get('schemaVersion') == 1 and permit.get('approval') and
             permit.get('transactionId') == transaction_id, 'Invalid archived publish approval')
    g.ensure(Path(permit['project']).resolve() == project, 'Wrong archived candidate')
    platform = g.load(project / 'ProjectSettings/FrameworkPlatform.json')
    identity = platform['buildRelease']['releaseTransaction']
    g.ensure({k: identity[k] for k in ('projectId', 'environment')} ==
             {k: bound[k] for k in ('projectId', 'environment')} and
             platform['bootstrapUrl'] == bound['bootstrapUrl'], 'Archived identity mismatch')
    ledger = g.load(Path(identity['stateRoot']) / 'transactions.json')
    g.ensure(ledger['identity'] == {**{k: identity[k] for k in ('projectId', 'environment')},
                                  'bootstrapUrl': platform['bootstrapUrl']}, 'Wrong shared ledger')
    tx = next((t for t in ledger['transactions'] if t['id'] == transaction_id), {})
    g.ensure(tx.get('state') in ('registered', 'frozen', 'running') and
             tx.get('intent') == 'publish' and tx.get('buildKind') == 'none',
             'Archived mode requires live publish-only transaction')
    origin = next((t for t in ledger['transactions'] if t['id'] == permit['originTransaction']), {})
    proof_entry = origin.get('steps', {}).get('archive', {})
    g.ensure(origin.get('state') == 'delivered-pending-acceptance' and proof_entry,
             'Original completed archive transaction missing')
    proof_path = Path(proof_entry['evidence'])
    g.ensure(g.digest(proof_path) == proof_entry['sha256'] == permit['archiveProofSha256'],
             'Original archive proof changed')
    proof = g.load(proof_path)
    g.ensure(proof['transactionId'] == origin['id'], 'Archive origin mismatch')
    proof_files = {str(Path(r['path']).resolve()): r['sha256'] for r in proof['files']}
    for entry in permit['archives']:
        path = Path(entry['path']).resolve()
        g.ensure(proof_files.get(str(path)) == entry['sha256'] == g.digest(path),
                 'Original archive changed: ' + str(path))
    for entry in permit.get('artifacts', []):
        path = Path(entry['path']).resolve()
        g.ensure(proof_files.get(str(path)) == entry['sha256'] == g.digest(path),
                 'Built artifact changed: ' + str(path))
    # The administrator-reviewed complete inventory is pinned outside candidate scopes.
    # Its source/generated hashes must be derived from the original immutable archives.
    inventory_path = Path(permit['inventory'])
    g.ensure(g.digest(inventory_path) == permit['inventorySha256'], 'Archived inventory changed')
    inventory = g.load(inventory_path)
    g.ensure(Path(inventory['project']).resolve() == project and
             set(inventory['scopes']) >= {'Assets', 'Packages', 'ProjectSettings', 'Tools', 'Library/AIUI'},
             'Incomplete archived inventory scopes')
    g.ensure(not inventory.get('excludes'), 'Archived inventory must not exclude inputs')
    expected = {r['path']: r['sha256'] for r in inventory['files']}
    g.ensure(len(expected) == len(inventory['files']), 'Duplicate inventory entries')
    actual = {}
    for scope in inventory['scopes']:
        root = (project / scope).resolve()
        g.ensure(root.is_relative_to(project) and root != project, 'Unsafe archived scope')
        for f in root.rglob('*'):
            if not f.is_file() or '__pycache__' in f.parts:
                continue
            g.ensure(f.resolve().is_relative_to(project), 'Archived input escapes project')
            actual[f.relative_to(project).as_posix()] = g.digest(f)
    g.ensure(actual == expected, 'Archived input added/deleted/changed')
    import zipfile
    archived = {}
    for entry in permit['archives']:
        with zipfile.ZipFile(entry['path']) as z:
            for name in z.namelist():
                if name.endswith('/'):
                    continue
                target = (project / name).resolve()
                g.ensure(target.is_relative_to(project) and target != project, 'Unsafe archive member')
                archived[name] = hashlib.sha256(z.read(name)).hexdigest()
    g.ensure(all(expected.get(n) == h for n, h in archived.items()),
             'Candidate differs from source/generated archive')
    additions = set(expected) - set(archived)
    g.ensure(additions == set(permit.get('supplements', {})) and
             all(expected[n] == permit['supplements'][n] for n in additions),
             'Unapproved archive supplement')
    g.ensure(all(n.startswith(('Assets/Editor/', 'Assets/HybridCLRGenerate/')) for n in additions),
             'Runtime additions are not allowed')
    required = g.dependencies(project)
    g.ensure(all(n in expected for n in required), 'Archived governance dependencies missing')
    if input_manifest:
        declared = {r['path']: r['sha256'] for r in g.load(input_manifest)['files']}
        g.ensure(all(declared.get(n) == expected[n] for n in required), 'Frozen governance incomplete')
    state = g.load(project / 'Library/AIUI/hotupdate-build-state.json')
    g.ensure((state['baseVersion'], state['release']) == (permit['base'], permit['release']),
             'Archived Base/Content mismatch')
    # Every entry point still checks candidate resource transactions; unrelated working
    # copies cannot mutate this pinned candidate. The production Journal remains shared.
    g.unfinished(project, Path(bound['journalRoot']))
    tools = {f.name: g.digest(f) for f in Path(g.__file__).parent.glob('*.py')}
    key = hashlib.sha256(json.dumps({'permit': reference, 'inventory': actual,
        'binding': bound, 'tools': tools}, sort_keys=True).encode()).hexdigest()
    reused = g.reusable(previous, key)
    if reused:
        return reused
    output = Path(bound['evidenceRoot']) / ('archived-publish-' + uuid.uuid4().hex)
    output.mkdir(parents=True)
    report_path = output / 'candidate.json'
    report = g.audit(project, bound, report_path)
    g.unfinished(project, Path(bound['journalRoot']))
    receipt = {'mode': 'immutable-archived-publish', 'transactionId': transaction_id,
        'archiveProofSha256': permit['archiveProofSha256'], 'reuseKey': key,
        'sourceProject': str(project), 'candidateProject': str(project),
        'sourceReport': str(report_path), 'candidateReport': str(report_path),
        'reportHashes': {n: g.digest(report_path) for n in ('sourceReport', 'candidateReport')},
        'candidateLegacy': len(report['legacy']), 'warnings': len(report['warnings'])}
    path = output / 'preflight.json'
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    return str(path)
