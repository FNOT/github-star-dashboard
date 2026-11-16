"""Merge star histories: python scripts/merge_history.py TARGET SOURCE [SOURCE ...]

Each file is either {"repos": {key: [[ms, stars], ...]}, "coverage": [[from, to], ...]}
or a bare {key: [...]} (the format the dashboard used to keep in localStorage).
Points are unioned, sorted by time, and consecutive repeats of the same value are
dropped; coverage intervals are unioned. TARGET is rewritten in place. Used by the
workflow so a push never fails on a conflict.
"""
import json
import sys

GAP_MS = 5 * 60 * 1000  # must match GAP in index.html


def read(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}, []
    if "repos" in data:
        return data["repos"], data.get("coverage", [])
    return data, []


def main():
    target, *sources = sys.argv[1:]
    merged, coverage = read(target)
    for src in sources:
        repos, cov = read(src)
        coverage = coverage + cov
        for key, points in repos.items():
            merged.setdefault(key.lower(), []).extend(points)

    for key, points in merged.items():
        points.sort(key=lambda p: p[0])
        out = []
        for p in points:
            if not out or out[-1][1] != p[1]:
                out.append(p)
        merged[key] = out

    cov_out = []
    for c in sorted(coverage, key=lambda c: c[0]):
        if cov_out and c[0] - cov_out[-1][1] <= GAP_MS:
            cov_out[-1][1] = max(cov_out[-1][1], c[1])
        else:
            cov_out.append(list(c))

    with open(target, "w", encoding="utf-8") as f:
        json.dump({"repos": merged, "coverage": cov_out}, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


if __name__ == "__main__":
    main()
