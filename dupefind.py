#!/usr/bin/env python3
"""dupefind: find duplicate files (size grouping, then sha256)."""
import argparse
import fnmatch
import hashlib
import json
import os
import shlex
import sys


def load_patterns(root):
    path = os.path.join(root, ".gitignore")
    pats = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(("#", "!")):
                    pats.append(line)
    return pats


def ignored(rel, is_dir, pats):
    parts = rel.split("/")
    for pat in pats:
        dir_only = pat.endswith("/")
        p = pat.rstrip("/")
        anchored = p.startswith("/") or "/" in p
        p = p.lstrip("/")
        if anchored:
            # match the path or any of its parent prefixes
            for i in range(1, len(parts) + 1):
                if i < len(parts) or is_dir or not dir_only:
                    if fnmatch.fnmatchcase("/".join(parts[:i]), p):
                        return True
        else:
            for i, part in enumerate(parts):
                last = i == len(parts) - 1
                if dir_only and last and not is_dir:
                    continue
                if fnmatch.fnmatchcase(part, p):
                    return True
    return False


def walk(root, pats):
    for dp, dns, fns in os.walk(root):
        rel_dir = os.path.relpath(dp, root)
        rel_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")
        dns[:] = sorted(d for d in dns if not ignored(
            (rel_dir + "/" + d).lstrip("/"), True, pats) and d != ".git")
        for fn in sorted(fns):
            rel = (rel_dir + "/" + fn).lstrip("/")
            full = os.path.join(dp, fn)
            if os.path.islink(full) or ignored(rel, False, pats):
                continue
            yield full


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_dupes(root, min_size=1):
    pats = load_patterns(root)
    by_size = {}
    for p in walk(root, pats):
        try:
            size = os.path.getsize(p)
        except OSError:
            continue
        if size >= min_size:
            by_size.setdefault(size, []).append(p)
    groups = []
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        by_hash = {}
        for p in paths:
            try:
                by_hash.setdefault(sha256(p), []).append(p)
            except OSError:
                pass
        for h, ps in by_hash.items():
            if len(ps) > 1:
                groups.append({"sha256": h, "size": size, "files": sorted(ps)})
    groups.sort(key=lambda g: (-g["size"], g["files"][0]))
    return groups


def main(argv=None):
    ap = argparse.ArgumentParser(description="Find duplicate files.")
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--min-size", type=int, default=1, metavar="N",
                    help="ignore files smaller than N bytes (default 1)")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--delete-hint", action="store_true",
                    help="print rm commands for all but the first of each group (never deletes)")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.root):
        print("not a directory: " + a.root, file=sys.stderr)
        return 2
    groups = find_dupes(a.root, a.min_size)
    if a.json:
        print(json.dumps(groups, indent=2))
    elif a.delete_hint:
        for g in groups:
            print("# keep " + g["files"][0])
            for p in g["files"][1:]:
                print("rm -- " + shlex.quote(p))
    else:
        for g in groups:
            print("%s  %d bytes" % (g["sha256"][:12], g["size"]))
            for p in g["files"]:
                print("  " + p)
        if not groups:
            print("no duplicates found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
