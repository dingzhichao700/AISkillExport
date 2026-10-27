"""Stage, activate and verify a validated WeChat release on public-read COS.

Credentials are supplied only through an existing COSCLI config file.
Run a single publisher per project; this is not a distributed locking service.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from validate_release import inside, read, require, validate


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
    receipt = {"action": args.action, "baseVersion": base, "release": release, "publicRoot": public, "files": []}
    for key in sorted(paths):
        path = inside(root, key)
        data = path.read_bytes()
        remote = fetch(public + key)
        if remote is None and args.action == "stage":
            upload(args, deployment, key, path, True)
            remote = fetch(public + key)
        require(remote is not None and digest(remote) == digest(data), "Missing or mismatched immutable resource: " + key)
        receipt["files"].append({"key": key, "sha256": digest(data), "bytes": len(data)})
        print("Verified " + key, flush=True)
    if args.action in ("activate", "verify"):
        current_key = base + "/current.json"
        current = inside(root, folder + "manifest.json").read_bytes()
        if args.action == "activate":
            upload(args, deployment, current_key, inside(root, current_key), False)
        remote_current = fetch(public + current_key)
        require(remote_current is not None and json.loads(remote_current) == json.loads(current), "Remote current mismatch")
        remote_boot = fetch(public + "bootstrap.json")
        if args.action == "activate":
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
    output = project.parent / "build" / ("cos-" + args.action + "-" + base + "-" + release + ".json")
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"receipt": str(output), "filesVerified": len(paths), "pointersVerified": receipt.get("pointersVerified", False)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--action", choices=("stage", "activate", "verify"), required=True)
    parser.add_argument("--coscli", required=True)
    parser.add_argument("--cos-config", required=True)
    arguments = parser.parse_args()
    lock = Path(arguments.project).resolve().parent / "build" / ".cos-publish.lock"
    try:
        with lock.open("x"):
            pass
    except FileExistsError:
        parser.exit(1, "Publisher lock exists; inspect the active publisher before retrying.\n")
    try:
        execute(arguments)
    finally:
        lock.unlink()
