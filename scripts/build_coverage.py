"""Build web/coverage.json from the collected knowledge/ content.

Summarizes content reach — per-agency document counts and a focus breakdown for one
agency (default human-resources: types + sample titles) — so the demo landing page can
display what's actually been collected. Run from repo root:

    .venv/bin/python scripts/build_coverage.py [--focus human-resources]
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = ROOT / "knowledge"
AGENCIES_MD = ROOT / "agencies.md"
OUT = ROOT / "web" / "coverage.json"


def parse_agencies() -> dict:
    """folder -> {name, url} from the agencies.md table."""
    mapping = {}
    if not AGENCIES_MD.exists():
        return mapping
    for line in AGENCIES_MD.read_text(encoding="utf-8", errors="replace").splitlines():
        cells = [c.strip() for c in line.split("|")]
        # table rows look like: | Name | https://url | folder |
        if len(cells) >= 5 and cells[2].startswith("http"):
            name, url, folder = cells[1], cells[2], cells[3]
            if folder and folder.lower() != "folder":
                mapping[folder] = {"name": name, "url": url}
    return mapping


def md_files(agency_dir: Path):
    return [p for p in agency_dir.glob("*.md") if p.name.lower() != "readme.md"]


def read_frontmatter(path: Path) -> dict:
    fm = {}
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            if f.readline().strip() != "---":
                return fm
            for _ in range(15):
                line = f.readline()
                if line.strip() == "---" or not line:
                    break
                m = re.match(r"(\w+):\s*(.*)", line)
                if m:
                    fm[m.group(1).lower()] = m.group(2).strip()
    except Exception:
        pass
    return fm


def _is_descriptive(title: str) -> bool:
    """Keep human-readable titles; drop filename stubs, codes, bare numbers."""
    if not (10 <= len(title) <= 90):
        return False
    if len(title.split()) < 2:
        return False
    if not any(c.isalpha() for c in title):
        return False
    return True


def focus_breakdown(agency_dir: Path, max_titles: int = 15) -> dict:
    types: dict = {}
    titles = []
    seen = set()
    for p in md_files(agency_dir):
        fm = read_frontmatter(p)
        t = (fm.get("type") or "HTML").upper()
        types[t] = types.get(t, 0) + 1
        title = (fm.get("title") or "").strip()
        key = title.lower()
        if _is_descriptive(title) and key not in seen:
            seen.add(key)
            titles.append(title)
    # spread across the meaningful titles for variety rather than taking the first N
    if len(titles) > max_titles:
        step = len(titles) / max_titles
        titles = [titles[int(i * step)] for i in range(max_titles)]
    return {"types": types, "sample_titles": titles}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--focus", default="human-resources")
    args = ap.parse_args()

    meta = parse_agencies()
    agencies = []
    for d in sorted(KNOWLEDGE.iterdir()):
        if not d.is_dir():
            continue
        count = len(md_files(d))
        if count == 0:
            continue
        info = meta.get(d.name, {})
        agencies.append(
            {
                "folder": d.name,
                "name": info.get("name") or d.name.replace("-", " ").title(),
                "url": info.get("url", ""),
                "doc_count": count,
            }
        )
    agencies.sort(key=lambda a: a["doc_count"], reverse=True)

    payload = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "total_docs": sum(a["doc_count"] for a in agencies),
        "agency_count": len(agencies),
        "agencies": agencies,
    }

    focus_dir = KNOWLEDGE / args.focus
    if focus_dir.is_dir():
        f = focus_breakdown(focus_dir)
        info = meta.get(args.focus, {})
        payload["focus"] = {
            "folder": args.focus,
            "name": info.get("name") or args.focus.replace("-", " ").title(),
            "url": info.get("url", ""),
            "doc_count": len(md_files(focus_dir)),
            "types": f["types"],
            "sample_titles": f["sample_titles"],
        }

    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: {payload['total_docs']} docs across "
          f"{payload['agency_count']} agencies; focus={args.focus} "
          f"({payload.get('focus', {}).get('doc_count', 0)} docs)")


if __name__ == "__main__":
    main()
