"""Read-only validation of a project-configured WeChat candidate or historical release."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inside(root, relative):
    require(isinstance(relative, str) and relative and "\\" not in relative,
            "Invalid relative resource path")
    require(all(p not in ("", ".", "..") for p in relative.split("/")),
            "Noncanonical resource path")
    target = (root / relative).resolve()
    require(target.is_relative_to(root.resolve()), "Resource escapes configured root")
    return target


def validate(project, published=False, base_version=None, release=None):
    project = Path(project).resolve()
    config = read(project / "ProjectSettings/FrameworkPlatform.json")
    require(config.get("platform") == "WeChat", "Only WeChat is supported")
    require(bool(base_version) == bool(release), "Specify both base version and release")
    state = read(project / "Library/AIUI/hotupdate-build-state.json") if not base_version else None
    base_version = base_version or state["baseVersion"]
    release = release or state["release"]
    for value in (base_version, release):
        require(bool(re.fullmatch(r"[A-Za-z0-9_-]+", value)), "Unsafe version identifier")
    root = Path(config["cdnRoot"])
    require(root.is_absolute(), "cdnRoot must be absolute")
    base = inside(root, base_version)
    folder = inside(base, "releases/" + release)
    manifest = read(folder / "manifest.json")
    require(manifest["baseVersion"] == base_version and manifest["release"] == release,
            "Manifest version mismatch")
    require(manifest["resourceRoot"] == f"releases/{release}/" and manifest["bundleRoot"] == "bundles/",
            "Manifest directory contract mismatch")
    if state:
        require(state == manifest, "Build state does not match candidate")
    for key in ("aot", "assemblies"):
        values = manifest.get(key)
        require(isinstance(values, list) and all(isinstance(x, str) and re.fullmatch(r"[\w.-]+\.dll", x) for x in values), "Invalid assembly list")
        require(len(values) == len(set(values)), "Duplicate assembly entries")
    require(bool(manifest["assemblies"]), "Empty business assembly list")
    options = config.get("buildRelease", {})
    boot_path = options.get("bootConfigAsset", "Assets/Resources/GameFrameworkHotUpdateBase.txt")
    boot = read(inside(project, boot_path))
    require(boot["baseVersion"] == base_version, "Candidate does not match installed base inputs")
    require(boot["bootstrapUrl"] == config["bootstrapUrl"], "Base URL differs from project config; rebuild base or correct config")
    settings = read(folder / "settings.json")
    locations = settings.get("m_CatalogLocations", [])
    require(settings.get("m_DisableCatalogUpdateOnStart") and len(locations) == 1,
            "Catalog update policy mismatch")
    require(not locations[0].get("m_Dependencies") and locations[0]["m_InternalId"] == "{UnityEngine.AddressableAssets.Addressables.RuntimePath}/catalog.json",
            "Catalog must use versioned RuntimePath without hash dependencies")
    catalog = read(folder / "catalog.json")
    prefix = options.get("bundleVirtualRoot", "http://framework-content.invalid/")
    require(prefix.endswith("/"), "Virtual root must end in slash")
    bundles = set()
    checked_hashes = 0
    for identity in catalog["m_InternalIds"]:
        if not identity.endswith(".bundle"):
            continue
        require(identity.startswith(prefix), "Unexpected or local Bundle root: " + identity)
        relative = identity[len(prefix):]
        require(bool(re.search(r"_[0-9a-f]{16,64}\.bundle$", relative)), "Bundle name lacks hash")
        target = inside(base / "bundles", relative)
        require(target.is_file() and target.stat().st_size > 0, "Missing or empty Bundle: " + relative)
        source = inside(project / "ServerData/WebGL", relative)
        if source.is_file():
            require(hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(target.read_bytes()).digest(),
                    "Same-name Bundle content differs: " + relative)
            checked_hashes += 1
        bundles.add(relative)
    require(bool(bundles), "Catalog references no remote Bundles")
    if published:
        require(read(base / "current.json") == manifest, "Current pointer selects another candidate")
        entries = [e for e in read(root / "bootstrap.json")["bases"] if e["baseVersion"] == base_version]
        require(len(entries) == 1 and entries[0]["manifestUrl"] == base_version + "/current.json",
                "Bootstrap mapping is missing, duplicated or unexpected")
    return {"baseVersion": base_version, "release": release, "bundles": len(bundles),
            "sourceHashesCompared": checked_hashes, "publishedPointerChecked": published,
            "remoteDeploymentChecked": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--published", action="store_true")
    parser.add_argument("--base-version")
    parser.add_argument("--release")
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.project, args.published, args.base_version, args.release), ensure_ascii=False))
    except (ValueError, KeyError, OSError, TypeError) as error:
        parser.exit(1, "Release validation failed: " + str(error) + "\n")
