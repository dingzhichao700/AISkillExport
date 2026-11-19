"""Validate a narrowly approved content-only fork of an immutable source archive."""
from pathlib import Path
import json


def bind_content(g, project, bound, transaction_id, input_manifest):
    ref = bound['pinnedContent'][transaction_id]
    g.ensure(g.digest(ref['path']) == ref['sha256'], 'Pinned content binding changed')
    pin = g.load(ref['path'])
    g.ensure(pin.get('approval') and pin.get('transactionId') == transaction_id and
             Path(pin['project']).resolve() == project, 'Wrong pinned content request/project')
    platform = g.load(project / 'ProjectSettings/FrameworkPlatform.json')
    identity = platform['buildRelease']['releaseTransaction']
    expected_identity = {k: identity[k] for k in ('projectId', 'environment')}
    expected_identity['bootstrapUrl'] = platform['bootstrapUrl']
    g.ensure(expected_identity == {k: bound[k] for k in expected_identity}, 'Wrong content identity')
    ledger = g.load(Path(identity['stateRoot']) / 'transactions.json')
    g.ensure(ledger['identity'] == expected_identity, 'Wrong shared content ledger')
    tx = next((t for t in ledger['transactions'] if t['id'] == transaction_id), {})
    g.ensure(tx.get('state') in ('registered','frozen','running') and
             tx.get('intent') in ('content','build-publish') and tx.get('buildKind') == 'content',
             'Pinned mode requires a live content-only transaction')
    origin = next((t for t in ledger['transactions'] if t['id'] == pin['originTransaction']), {})
    proof = origin.get('steps', {}).get('archive', {})
    g.ensure(origin.get('state') == 'delivered-pending-acceptance' and proof and
             g.digest(proof['evidence']) == proof['sha256'] == pin['archiveProofSha256'],
             'Original content archive proof changed')
    rows = {str(Path(r['path']).resolve()):r['sha256'] for r in g.load(proof['evidence'])['files']}
    original = Path(pin['originalInput']).resolve()
    g.ensure(rows.get(str(original)) == g.digest(original), 'Original source manifest changed')
    manifest = Path(pin['inputManifest']).resolve()
    g.ensure(not input_manifest or Path(input_manifest).resolve() == manifest, 'Wrong content manifest')
    g.ensure(g.digest(manifest) == pin['inputSha256'], 'Pinned input manifest changed')
    # Reuse the normal complete source addition/deletion/hash validator, no custom scope.
    from release_transaction import verify_input
    current = verify_input(manifest, pin['inputSha256'], project)
    old = g.load(original)
    g.ensure(set(current['scopes']) == set(old['scopes']) >= {'Assets','Tools','Packages','ProjectSettings'}
             and current['excludes'] == old['excludes'], 'Content scopes/exclusions changed')
    before = {r['path']:r['sha256'] for r in old['files']}
    after = {r['path']:r['sha256'] for r in current['files']}
    patches = pin['patches']
    g.ensure(patches and all(n.startswith('Assets/Scripts/') and n.endswith('.cs') for n in patches),
             'Only reviewed runtime source patches allowed')
    for name, patch in patches.items():
        g.ensure(before.get(name) == patch['before'] and after.get(name) == patch['after'],
                 'Content patch differs from approved change')
    additions = pin.get('editorSupplements', {})
    g.ensure(all(n.startswith('Assets/Editor/') for n in additions) and not (set(additions)&set(before)),
             'Invalid Editor supplement')
    expected = {**before, **{n:p['after'] for n,p in patches.items()}, **additions}
    g.ensure(after == expected, 'Unapproved source/resource delta')
    for n,h in pin['protected'].items():
        f = (project/n).resolve()
        g.ensure(f.is_relative_to(project) and f.is_file() and g.digest(f)==h,
                 'Base/AOT/bridge input changed: '+n)
    state = g.load(project/'Library/AIUI/hotupdate-build-state.json')
    g.ensure(state['baseVersion'] == pin['base'], 'Content attempted to change base')
    # Preserve the original resource journal and check both actual participating roots.
    g.unfinished(Path(bound['sourceProject']).resolve(), Path(bound['journalRoot']))
    g.unfinished(project, Path(bound['journalRoot']))
    return {**bound, 'sourceProject': str(project)}
