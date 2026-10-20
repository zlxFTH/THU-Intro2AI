"""Compare COMMITTED Git trees against a teacher-owned release manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ALLOWED = {"agent.py", "alpha_beta_agent.py", "reflection.md"}
MAX_SOURCE = 128 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_entries(entries, manifest):
    """entries: path -> {mode, data: bytes}; manifest is trusted at the teacher."""
    errors = []
    expected = manifest["files"]
    for path in sorted(set(entries) | set(expected)):
        item = entries.get(path)
        if item is not None and item["mode"] != "100644":
            errors.append(f"{path}: only regular non-executable files are allowed")
        if path in ALLOWED:
            if item is None:
                errors.append(f"{path}: required file missing")
            elif len(item["data"]) > MAX_SOURCE:
                errors.append(f"{path}: exceeds 128 KiB")
            continue
        if path not in expected:
            errors.append(f"{path}: added protected file")
        elif item is None:
            errors.append(f"{path}: deleted protected file")
        elif item["mode"] != expected[path]["mode"] or sha(item["data"]) != expected[path]["sha256"]:
            errors.append(f"{path}: changed protected file")
    return errors


def git_entries(repo, revision="HEAD"):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args])
    commit = git("rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    entries = {}
    for record in git("ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
        if not record:
            continue
        info, path = record.split(b"\t", 1)
        mode, kind, oid = info.decode().split()
        path = path.decode("utf-8")
        data = git("cat-file", "blob", oid) if kind == "blob" else b""
        entries[path] = {"mode": mode, "data": data}
    return commit, entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--manifest", default=".starter-manifest.json")
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    commit, entries = git_entries(args.repo, args.revision)
    # The embedded manifest cannot hash itself. The teacher's external manifest DOES.
    if ".starter-manifest.json" not in manifest["files"]:
        entries.pop(".starter-manifest.json", None)
    errors = validate_entries(entries, manifest)
    print(json.dumps({"commit": commit, "ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()

