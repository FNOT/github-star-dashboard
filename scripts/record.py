"""Record current star counts into data/history.json.

Run by the GitHub Actions workflow every 10 minutes. A point is appended for a
repo only when its star count changed, so the file (and the commit history)
stays small. Uses GITHUB_TOKEN when present for a higher search rate limit.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS_FILE = os.path.join(ROOT, "repos.json")
HISTORY_FILE = os.path.join(ROOT, "data", "history.json")


def fetch_stars(repos):
    q = " ".join("repo:" + r["repo"] for r in repos)
    url = "https://api.github.com/search/repositories?per_page=100&q=" + urllib.parse.quote(q)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "star-dashboard-recorder"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as res:
        data = json.load(res)
    return {item["full_name"].lower(): item["stargazers_count"] for item in data["items"]}


def main():
    with open(REPOS_FILE, encoding="utf-8") as f:
        repos = json.load(f)
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = {"repos": {}}

    stars = fetch_stars(repos)
    now = int(time.time() * 1000)
    changed = []
    for r in repos:
        key = r["repo"].lower()
        value = stars.get(key)
        if value is None:
            print(f"warning: {r['repo']} not found in search results", file=sys.stderr)
            continue
        points = history["repos"].setdefault(key, [])
        if not points or points[-1][1] != value:
            points.append([now, value])
            changed.append(f"{r['repo']}={value}")

    if changed:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        print("changed: " + ", ".join(changed))
    else:
        print("no change")


if __name__ == "__main__":
    main()
