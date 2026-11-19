#!/usr/bin/env python3
"""Read-only contract/asset audit. Does not generate art or open/mutate Unity."""
import argparse, hashlib, json, math, re, struct, sys
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def resolve(value, contract_dir, binding):
    if not isinstance(value, str) or not value:
        raise ValueError('missing path')
    for prefix, key in [('project:', 'unityProjectRoot'), ('workspace:', 'workspaceRoot')]:
        if value.startswith(prefix):
            if not binding.get(key):
                raise ValueError('binding missing ' + key)
            return Path(binding[key]) / value[len(prefix):].lstrip('/\\')
    p = Path(value)
    return p if p.is_absolute() else contract_dir / p


def finite(values):
    return isinstance(values, list) and all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in values)


def prefab_blocks(text):
    return re.split(r'^--- !u!\d+ &', text, flags=re.M)[1:]


def audit(contract_path, binding_path=None):
    contract_path = Path(contract_path).resolve()
    c = load(contract_path)
    binding = load(binding_path) if binding_path else {}
    errors, checks, limitations = [], [], []
    observed = {}

    def check(ok, description):
        (checks if ok else errors).append(description)
        return bool(ok)

    def path(value, label):
        try:
            p = resolve(value, contract_path.parent, binding)
            return p if check(p.is_file(), label + ': file exists') else None
        except (ValueError, TypeError) as exc:
            errors.append(label + ': ' + str(exc))
            return None

    check(c.get('schemaVersion') == 1, 'supported contract schema')
    if binding_path:
        check(binding.get('schemaVersion') == 1, 'supported binding schema')
        for v in binding.get('authorityPaths', []):
            path(v, 'project authority')
    source = c.get('source') or {}
    anchor = c.get('anchor') or {}
    check(source.get('appearanceConfirmed') is True, 'appearance declared confirmed')
    path(source.get('approvalEvidence'), 'appearance approval evidence')
    check(anchor.get('confirmed') is True, 'semantic anchor declared confirmed')
    path(anchor.get('approvalEvidence'), 'anchor approval evidence')
    limitations.append('Approval flags and evidence existence do not prove human approval; read the source decision and scope.')
    image_path = path(source.get('path'), 'source image')
    canvas = source.get('canvasPx')
    valid_canvas = finite(canvas) and len(canvas) == 2 and all(x > 0 and int(x) == x for x in canvas)
    check(valid_canvas, 'positive declared source canvas')
    if image_path:
        data = image_path.read_bytes()
        observed['sourceSha256'] = hashlib.sha256(data).hexdigest()
        if source.get('sha256'):
            check(source['sha256'].lower() == observed['sourceSha256'], 'source hash matches declared baseline')
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            observed['sourceCanvasPx'] = list(struct.unpack('>II', data[16:24]))
            check(valid_canvas and canvas == observed['sourceCanvasPx'], 'source dimensions match actual PNG header')
            try:
                from PIL import Image
                with Image.open(image_path) as im:
                    alpha = im.convert('RGBA').getchannel('A')
                    observed['alphaBounds'] = alpha.getbbox()
                    observed['transparentCorners'] = all(alpha.getpixel(p) == 0 for p in [(0, 0), (im.width-1, 0), (0, im.height-1), (im.width-1, im.height-1)])
                    observed['alphaExtrema'] = alpha.getextrema()
                # Transparency is recorded, not required for every approved silhouette/source workflow.
            except ImportError:
                limitations.append('Pillow unavailable: PNG header inspected, visible bounds/alpha not inspected.')
        else:
            limitations.append('Non-PNG source: inspect dimensions/alpha with its native tool; script does not certify them.')
    pixels, normalized = anchor.get('pixels'), anchor.get('normalized')
    if check(valid_canvas and finite(pixels) and len(pixels) == 2 and finite(normalized) and len(normalized) == 2, 'anchor numeric fields present'):
        space = anchor.get('coordinateSpace')
        check(space in ['continuous-bottom-left', 'continuous-top-left'], 'explicit supported continuous anchor space')
        if space in ['continuous-bottom-left', 'continuous-top-left']:
            bottom_y = pixels[1] if space == 'continuous-bottom-left' else canvas[1] - pixels[1]
            derived = [pixels[0] / canvas[0], bottom_y / canvas[1]]
            check(all(abs(x-y) <= 1e-6 for x, y in zip(derived, normalized)), 'anchor pixel/normalized conversion matches')
            # Off-canvas pivots can be valid; do not impose an arbitrary range.
    scope = c.get('changeScope')
    valid_scope = scope in ['new-character', 'retarget', 'timing-only', 'fx-only', 'integration-only']
    check(valid_scope, 'known change scope')
    existing = c.get('existingRig')
    existing_path = path(existing, 'existing rig') if existing else None
    if scope in ['timing-only', 'fx-only', 'integration-only']:
        check(existing_path is not None, 'incremental task has an existing rig')
        route = 'existing-rig'
    else:
        layered = {'occlusion-change', 'rigid-part-motion', 'large-articulation', 'independent-part-motion'}
        route = 'layered' if layered.intersection(c.get('motionRequirements') or []) else 'single-image'
    observed['route'] = route
    observed['preserveBodyMotion'] = scope == 'fx-only'
    actions = c.get('actions')
    if check(isinstance(actions, list) and len(actions) > 0, 'explicit action list'):
        ids = [a.get('id') for a in actions]
        check(all(isinstance(i, str) and i for i in ids) and len(set(ids)) == len(ids), 'unique action IDs')
        for a in actions:
            duration = a.get('durationMs')
            check(isinstance(duration, (int, float)) and not isinstance(duration, bool) and math.isfinite(duration) and duration > 0, 'positive duration: ' + str(a.get('id')))
            check(isinstance(a.get('loop'), bool), 'explicit loop mode: ' + str(a.get('id')))
    for item in c.get('prefabChecks') or []:
        p = path(item.get('path'), 'prefab evidence')
        if not p:
            continue
        text = p.read_text(encoding='utf-8-sig')
        blocks = prefab_blocks(text)
        names = set(re.findall(r'^  m_Name: (.+)$', text, flags=re.M))
        check(set(item.get('requiredNames') or []).issubset(names), 'declared prefab names exist')
        parents = item.get('boneParents') or {}
        game_names, transforms = {}, {}
        for block in blocks:
            fileid = block.splitlines()[0]
            name = re.search(r'^  m_Name: (.+)$', block, flags=re.M)
            if name:
                game_names[fileid] = name.group(1)
            if '\nTransform:' in block:
                go = re.search(r'm_GameObject: \{fileID: (\d+)\}', block)
                parent = re.search(r'm_Father: \{fileID: (\d+)\}', block)
                if go and parent:
                    transforms[fileid] = (go.group(1), parent.group(1))
        actual_parents = {game_names.get(go): game_names.get(transforms.get(parent, ('', ''))[0]) for go, parent in transforms.values()}
        for child, parent in parents.items():
            check(actual_parents.get(child) == parent, 'prefab parent mapping: ' + child)
        selected = text
        if item.get('scriptPath'):
            script_path = path(item['scriptPath'], 'prefab parameter script')
            selected = ''
            if script_path:
                meta = script_path.with_suffix(script_path.suffix + '.meta')
                guid = re.search(r'^guid: (\w+)', meta.read_text(encoding='utf8'), flags=re.M) if meta.exists() else None
                selected = '\n'.join(b for b in blocks if guid and ('guid: ' + guid.group(1)) in b)
            check(bool(selected), 'selected serialized MonoBehaviour exists')
        for key, expected in (item.get('fields') or {}).items():
            values = re.findall(r'^  ' + re.escape(key) + r': ([-+\d.eE]+)\s*$', selected, flags=re.M)
            ok = len(values) == 1 and math.isfinite(float(values[0])) and math.isclose(float(values[0]), expected, rel_tol=1e-6, abs_tol=1e-6)
            check(ok, 'serialized parameter baseline: ' + key)
    snapshot = c.get('rigSnapshot')
    if snapshot:
        p = path(snapshot, 'rig snapshot')
        if p:
            rig = load(p)
            bones, vertices = rig.get('bones') or [], rig.get('vertices') or []
            check(len(bones) > 0, 'rig snapshot has bones')
            for i, bone in enumerate(bones):
                parent = bone.get('parent')
                check(isinstance(parent, int) and not isinstance(parent, bool) and -1 <= parent < len(bones) and parent != i, 'valid parent index: ' + str(i))
                seen, cursor = set(), i
                while isinstance(cursor, int) and 0 <= cursor < len(bones) and cursor not in seen:
                    seen.add(cursor); cursor = bones[cursor].get('parent')
                check(cursor not in seen, 'acyclic bone chain: ' + str(i))
            check(len(vertices) > 0, 'rig snapshot has vertices')
            for i, vertex in enumerate(vertices):
                check(finite(vertex.get('position')), 'finite vertex position: ' + str(i))
                weights = vertex.get('weights') or []
                ok = bool(weights) and all(isinstance(v.get('bone'), int) and not isinstance(v['bone'], bool) and 0 <= v['bone'] < len(bones) and isinstance(v.get('weight'), (int, float)) and math.isfinite(v['weight']) and v['weight'] >= 0 for v in weights)
                check(ok and math.isclose(sum(v['weight'] for v in weights), 1, abs_tol=1e-5), 'normalized valid vertex weights: ' + str(i))
            for triangle in rig.get('triangles') or []:
                check(len(triangle) == 3 and all(isinstance(v, int) and 0 <= v < len(vertices) for v in triangle) and len(set(triangle)) == 3, 'valid triangle indices')
    else:
        limitations.append('No rig snapshot supplied: mesh topology, weight values and native deformation are NOT verified.')
    for item in c.get('evidence') or []:
        p = path(item.get('path'), 'historical evidence')
        if p and 'expectedStatus' in item:
            e = load(p)
            check(e.get('status') == item['expectedStatus'], 'historical evidence status matches declaration')
            if item.get('requireEmptyError'):
                check(not e.get('error'), 'historical evidence has no recorded error')
    limitations.append('This read-only audit does not execute Unity, replay motion, establish visual acceptance or authorize new work.')
    return {'status': 'passed' if not errors else 'blocked', 'contract': str(contract_path), 'observed': observed, 'checks': checks, 'errors': errors, 'limitations': limitations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True)
    parser.add_argument('--binding')
    parser.add_argument('--output', help='Optional explicit report destination; otherwise stdout only')
    args = parser.parse_args()
    try:
        result = audit(args.contract, args.binding)
    except (ValueError, OSError, TypeError, KeyError, struct.error) as exc:
        result = {'status': 'blocked', 'errors': [str(exc)]}
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        target = Path(args.output); target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text, encoding='utf8')
    print(text)
    return 0 if result['status'] == 'passed' else 2


if __name__ == '__main__':
    sys.exit(main())
