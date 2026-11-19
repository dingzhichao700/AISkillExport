"""Stage, activate and verify a validated WeChat release on public-read COS.

Credentials are supplied only through an existing COSCLI config file.
Run a single publisher per project; this is not a distributed locking service.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from validate_release import inside, read, require, validate
from release_transaction import Journal, binding, verify_input
from remote_verify import trusted_stage, verify_files


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("Unexpected redirect from COS")


def fetch(url):
    request = urllib.request.Request(url + "?verification=" + uuid.uuid4().hex,
                                     headers={"Cache-Control": "no-cache"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=90) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def digest(data):
    return hashlib.sha256(data).hexdigest()


def merge_bootstrap(remote, local, base):
    result = dict(remote or local)
    entries = result.get("bases", [])
    require(len({e["baseVersion"] for e in entries}) == len(entries), "Duplicate remote bases")
    chosen = [e for e in local["bases"] if e["baseVersion"] == base]
    require(len(chosen) == 1, "Missing local base entry")
    result["bases"] = [e for e in entries if e["baseVersion"] != base] + chosen
    return result


def pointer_snapshot(public, base):
    boot = fetch(public + "bootstrap.json")
    keys = {base + "/current.json"}
    if boot:
        entries = json.loads(boot).get("bases", [])
        require(len({e["baseVersion"] for e in entries}) == len(entries), "Duplicate bootstrap bases")
        for entry in entries:
            key = entry["manifestUrl"]
            require(key == entry["baseVersion"] + "/current.json" and re.fullmatch(r"[A-Za-z0-9_-]+/current\.json", key), "Unsafe bootstrap pointer")
            keys.add(key)
    return {"bootstrap": digest(boot) if boot is not None else None,
            "currents": {k: digest(value) if (value := fetch(public + k)) is not None else None for k in sorted(keys)}}


def require_baseline(expected, actual):
    require(actual == expected, "Online baseline changed; refuse activation and re-review candidate")


def upload(args, deployment, key, path, immutable):
    command = [str(Path(args.coscli).resolve()), "cp", str(path),
               "cos://" + deployment["bucket"] + "/" + deployment["projectSubdirectory"] + "/" + key,
               "-c", str(Path(args.cos_config).resolve()), "--disable-log",
               "--process-log=false", "--fail-output=false", "--check-point=false",
               "--meta", "Cache-Control:" + ("public,max-age=31536000,immutable" if immutable else "no-cache,no-store,must-revalidate")]
    if immutable:
        command.append("--forbid-overwrite")
    completed = subprocess.run(command, capture_output=True)
    # Never echo CLI output: a future CLI may include configuration diagnostics.
    require(completed.returncode == 0, "COSCLI upload failed for " + key + " (exit " + str(completed.returncode) + ")")


def execute(args):
    project = Path(args.project).resolve()
    report = validate(project, published=args.action == "activate")
    config = read(project / "ProjectSettings/FrameworkPlatform.json")
    deployment = config["buildRelease"]["deployment"]
    require(deployment["kind"] == "cos", "Deployment is not COS")
    for key in ("bucket", "region", "projectSubdirectory"):
        require(bool(re.fullmatch(r"[A-Za-z0-9_-]+", deployment[key])), "Invalid " + key)
    public = "https://" + deployment["bucket"] + ".cos." + deployment["region"] + ".myqcloud.com/" + deployment["projectSubdirectory"] + "/"
    require(deployment["publicRoot"] == public and config["bootstrapUrl"] == public + "bootstrap.json", "COS URL/config mismatch")
    root = Path(config["cdnRoot"]).resolve()
    base, release = report["baseVersion"], report["release"]
    folder = base + "/releases/" + release + "/"
    paths = {folder + name for name in ("manifest.json", "settings.json", "catalog.json")}
    virtual = config.get("buildRelease", {}).get("bundleVirtualRoot", "http://framework-content.invalid/")
    for identity in read(inside(root, folder + "catalog.json"))["m_InternalIds"]:
        if identity.endswith(".bundle"):
            require(identity.startswith(virtual), "Unexpected bundle identity")
            paths.add(base + "/bundles/" + identity[len(virtual):])
    journal = None
    previous = {}
    if args.action in ("stage", "activate") and getattr(args, "transaction", None):
        root_state, identity = binding(project)
        journal = Journal(root_state, identity)
        with journal.edit() as state:
            tx = journal.tx(state, args.transaction, args.owner)
            require(tx.get("inFlight", {}).get("operationId") == args.operation, "Missing transaction operation")
            selection = {"baseVersion": base, "release": release, "resourcesSha256": digest(json.dumps({key: digest(inside(root, key).read_bytes()) for key in sorted(paths)}, sort_keys=True).encode())}
            if args.action == "stage":
                require("selection" not in tx or tx["selection"] == selection, "Candidate selection changed")
                tx["selection"] = selection
            else:
                require("stage" in tx["steps"] and tx.get("selection") == selection, "Candidate differs from verified staged transaction")
                previous = trusted_stage(tx['steps']['stage'], args.transaction, public, base, release)
            verify_input(tx["inputManifest"], tx["candidateSha256"], project)
            expected_baseline = tx["baseline"]
        if args.action == "activate":
            require_baseline(expected_baseline, pointer_snapshot(public, base))
    receipt = {"transactionId": getattr(args, "transaction", None), "action": args.action, "baseVersion": base, "release": release, "publicRoot": public, "files": []}
    for key in paths:
        inside(root, key)  # retain traversal checks before concurrent work
    receipt['files'], receipt['verificationStats'] = verify_files(
        paths, root, public, args.action,
        lambda key, path: upload(args, deployment, key, path, True), previous)
    print(json.dumps(receipt['verificationStats']), flush=True)
    if args.action in ("activate", "verify"):
        current_key = base + "/current.json"
        current = inside(root, folder + "manifest.json").read_bytes()
        if args.action == "activate":
            # Recheck after long immutable-resource verification, before first mutable write.
            if journal is not None:
                require_baseline(expected_baseline, pointer_snapshot(public, base))
            upload(args, deployment, current_key, inside(root, folder + "manifest.json"), False)
        remote_current = fetch(public + current_key)
        require(remote_current is not None and json.loads(remote_current) == json.loads(current), "Remote current mismatch")
        remote_boot = fetch(public + "bootstrap.json")
        if args.action == "activate":
            if journal is not None:
                expected_after_current = {"bootstrap": expected_baseline["bootstrap"], "currents": dict(expected_baseline["currents"])}
                expected_after_current["currents"][current_key] = digest(current)
                require_baseline(expected_after_current, pointer_snapshot(public, base))
            merged = merge_bootstrap(json.loads(remote_boot) if remote_boot else None, read(root / "bootstrap.json"), base)
            with tempfile.TemporaryDirectory(prefix="cos-pointer-") as temporary:
                pointer = Path(temporary) / "bootstrap.json"
                pointer.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
                upload(args, deployment, "bootstrap.json", pointer, False)
                remote_boot = fetch(public + "bootstrap.json")
                require(remote_boot is not None and json.loads(remote_boot) == merged, "Remote bootstrap mismatch")
                (root / "bootstrap.json").write_bytes(pointer.read_bytes())
        require(remote_boot is not None, "Missing bootstrap")
        entries = [e for e in json.loads(remote_boot)["bases"] if e["baseVersion"] == base]
        require(len(entries) == 1 and entries[0]["manifestUrl"] == current_key, "Remote base entry mismatch")
        receipt["pointersVerified"] = True
    output = receipt_path(project, args.action, base, release)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def receipt_path(project, action, base, release):
    require(action in ('stage', 'activate', 'verify'), 'Unsupported receipt action')
    require(all(re.fullmatch(r'[A-Za-z0-9_-]+', item) for item in (base, release)), 'Unsafe receipt version')
    return Path(project).resolve().parent / 'build' / 'archives' / base / 'content' / release / 'receipts' / ('cos-' + action + '-' + base + '-' + release + '.json')


def print_receipt(output):
    receipt = read(output)
    print(json.dumps({"receipt": str(output), "filesVerified": len(receipt["files"]), "pointersVerified": receipt.get("pointersVerified", False)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--action", choices=("stage", "activate", "verify", "snapshot"), required=True)
    parser.add_argument("--coscli")
    parser.add_argument("--cos-config")
    parser.add_argument("--transaction")
    parser.add_argument("--owner")
    parser.add_argument("--base")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.action == "snapshot":
        config = read(Path(args.project) / "ProjectSettings/FrameworkPlatform.json")
        require(args.base and re.fullmatch(r"[A-Za-z0-9_-]+", args.base), "Explicit base required")
        result = pointer_snapshot(config["buildRelease"]["deployment"]["publicRoot"], args.base)
        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result))
        return
    if args.action == "verify":
        print_receipt(execute(args))
        return
    require(args.coscli and args.cos_config, "Explicit COS paths required")
    config = read(Path(args.project) / "ProjectSettings/FrameworkPlatform.json")
    bound = "releaseTransaction" in config.get("buildRelease", {})
    journal = None
    args.operation = uuid.uuid4().hex
    if bound:
        require(args.transaction and args.owner, "Bound project mutations require transaction/owner")
        root, identity = binding(args.project)
        journal = Journal(root, identity)
        journal.begin(args.transaction, args.owner, args.action, args.operation, args.project, os.getpid())
    else:
        require(not args.transaction and not args.owner, "Explicit transaction requires project binding")
        from release_resource_gate import check as resource_preflight
        resource_preflight(args.project, phase=args.action)
    # Legacy lock remains a second guard against old publishers. A stale lock fails closed.
    lock = Path(args.project).resolve().parent / "build" / ".cos-publish.lock"
    acquired = False
    try:
        with lock.open("x", encoding="utf-8") as stream:
            json.dump({"transaction": args.transaction, "operation": args.operation}, stream)
        acquired = True
        output = execute(args)
        if journal is not None:
            journal.finish(args.transaction, args.owner, args.operation, output)
        print_receipt(output)
    except BaseException:
        if journal is not None:
            journal.fail(args.transaction, args.owner, args.operation)
        raise
    finally:
        if acquired:
            lock.unlink()


if __name__ == "__main__":
    main()
