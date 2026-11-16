"""Merge star histories: python scripts/merge_history.py TARGET SOURCE [SOURCE ...]

Each file is either {"repos": {key: [[ms, stars], ...]}} or a bare {key: [...]}
(the format the dashboard used to keep in localStorage). Points are unioned,
sorted by time, and consecutive repeats of the same value are dropped. TARGET
is rewritten in place. Used by the workflow so a push never fails on a conflict.
"""
import json
import sys


def read(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("repos", data) if isinstance(data, dict) else {}


def main():
    target, *sources = sys.argv[1:]
    merged = read(target)
    for src in sources:
        for key, points in read(src).items():
            merged.setdefault(key.lower(), []).extend(points)
    for key, points in merged.items():
        points.sort(key=lambda p: p[0])
        out = []
        for p in points:
            if not out or out[-1][1] != p[1]:
                out.append(p)
        merged[key] = out
    with open(target, "w", encoding="utf-8") as f:
        json.dump({"repos": merged}, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


if __name__ == "__main__":
    main()
