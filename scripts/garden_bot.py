#!/usr/bin/env python3

import json
import os
import random
import re
import sys
from datetime import datetime, timezone


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LAWN_JSON = os.path.join(REPO_ROOT, "lawn-health.json")
GARDEN_MD = os.path.join(REPO_ROOT, "garden.md")
GARDEN_SVG = os.path.join(REPO_ROOT, "garden.svg")
SEEDLINGS_DIR = os.path.join(REPO_ROOT, "seedlings")
WEEDS_DIR = os.path.join(REPO_ROOT, "weeds")


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def parse_issue_pr_context() -> dict:
    # These env vars exist in GitHub Actions context; locally we default
    event_name = os.environ.get("GITHUB_EVENT_NAME", "manual")
    ref_name = os.environ.get("GITHUB_REF_NAME", "local")
    # Try extract number from branch names like refs/pull/123/merge or PR-123
    pr_match = re.search(r"(pull|PR)[^0-9]*([0-9]+)", ref_name or "")
    ctx = {
        "event": event_name,
        "ref_name": ref_name,
        "id": pr_match.group(2) if pr_match else None,
    }
    return ctx


def whimsical_sentence(seed_or_weed: str, identifier: str | None) -> str:
    fertilizer = [
        "Needs more sunlight (a.k.a. documentation)",
        "Consider composting legacy code",
        "Water with tests twice daily",
        "Beware of aphids: flaky specs",
        "Mulch with design discussions",
    ]
    growth = [
        "sprouting probability: {}%".format(random.randint(5, 95)),
        "photosynthesis throughput nominal",
        "rooting depth increasing",
        "waiting for bees (reviewers)",
        "may die in review drought",
    ]
    if seed_or_weed == "seed":
        prefix = f"🌱 A new seed has been planted: PR #{identifier}" if identifier else "🌱 A new seed has been planted"
    else:
        prefix = f"🌾 A new weed has appeared: Issue #{identifier}" if identifier else "🌾 A new weed has appeared"
    return f"{prefix}. {random.choice(fertilizer)}; {random.choice(growth)}."


def update_lawn_health(health: dict, event: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    health = dict(health or {})
    # initialize some fields if missing
    health.setdefault("lawnHealthIndex", 70)
    health.setdefault("lushnessPercent", 60)
    health.setdefault("weeds", {"count": 0})
    health.setdefault("seeds", {"count": 0, "sprouting": 0, "failed": 0})

    if event == "issues_opened":
        health["weeds"]["count"] = health["weeds"].get("count", 0) + 1
        health["lushnessPercent"] = clamp(health["lushnessPercent"] - random.randint(1, 5), 0, 100)
        health["lawnHealthIndex"] = clamp(health["lawnHealthIndex"] - random.randint(1, 4), 0, 100)
    elif event == "issues_closed":
        health["weeds"]["count"] = max(0, health["weeds"].get("count", 0) - 1)
        health["lushnessPercent"] = clamp(health["lushnessPercent"] + random.randint(1, 4), 0, 100)
        health["lawnHealthIndex"] = clamp(health["lawnHealthIndex"] + random.randint(1, 3), 0, 100)
    elif event == "pull_request_opened":
        health["seeds"]["count"] = health["seeds"].get("count", 0) + 1
        health["seeds"]["sprouting"] = health["seeds"].get("sprouting", 0) + 1
        health["lawnHealthIndex"] = clamp(health["lawnHealthIndex"] + random.randint(0, 2), 0, 100)
    elif event == "pull_request_closed":
        # Randomly consider merged or declined effect
        merged = random.random() < 0.6
        if merged:
            health["lawnHealthIndex"] = clamp(health["lawnHealthIndex"] + random.randint(2, 6), 0, 100)
            health["lushnessPercent"] = clamp(health["lushnessPercent"] + random.randint(2, 5), 0, 100)
            health["seeds"]["sprouting"] = max(0, health["seeds"].get("sprouting", 0) - 1)
        else:
            health["seeds"]["failed"] = health["seeds"].get("failed", 0) + 1
            health["seeds"]["sprouting"] = max(0, health["seeds"].get("sprouting", 0) - 1)
            health["lawnHealthIndex"] = clamp(health["lawnHealthIndex"] - random.randint(0, 3), 0, 100)

    # seasonal drift on schedule/manual runs
    if event in ("schedule", "push", "manual"):
        drift = random.randint(-1, 1)
        health["lawnHealthIndex"] = clamp(health["lawnHealthIndex"] + drift, 0, 100)

    health["lastUpdated"] = now
    return health


def ensure_dirs() -> None:
    os.makedirs(SEEDLINGS_DIR, exist_ok=True)
    os.makedirs(WEEDS_DIR, exist_ok=True)


def write_seed_or_weed_file(kind: str, identifier: str | None, title: str) -> None:
    ensure_dirs()
    safe_title = re.sub(r"[^a-zA-Z0-9._-]+", "-", title).strip("-") or kind
    if kind == "seed":
        filename = os.path.join(SEEDLINGS_DIR, f"seed-{identifier or 'x'}.txt")
    else:
        filename = os.path.join(WEEDS_DIR, f"weed-{identifier or 'x'}.txt")
    body = f"{title}\n{datetime.utcnow().isoformat()}Z\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(body)


def build_story(health: dict, recent_line: str | None) -> str:
    weeds = health.get("weeds", {}).get("count", 0)
    seeds = health.get("seeds", {}).get("count", 0)
    lush = health.get("lushnessPercent", 0)
    lhi = health.get("lawnHealthIndex", 0)

    commentary = []
    if weeds > seeds + 3:
        commentary.append("Your repo is overgrown. Consider mowing (aka triage).")
    if seeds == 0:
        commentary.append("No seeds in sight. The lawn is barren.")
    if recent_line:
        commentary.append(recent_line)

    # Always include a one-liner narrative summary
    summary = f"Lawn Health Index {lhi}/100, lushness {lush}%. Seeds: {seeds}, Weeds: {weeds}."
    return "\n".join([summary] + commentary)


def generate_svg(health: dict, story: str) -> str:
    width, height = 800, 320
    # Color based on health
    lush = int(health.get("lushnessPercent", 50))
    green = clamp(int(100 + lush * 1.5), 0, 255)
    bg = f"rgb(30,{green},60)"

    # Build simple SVG with gradient sky and text narrative
    lines = story.splitlines()
    text_y = 40
    svg_lines = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        "<defs>",
        "  <linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'>",
        "    <stop offset='0%' stop-color='#87CEEB' />",
        "    <stop offset='100%' stop-color='#E0F7FA' />",
        "  </linearGradient>",
        "</defs>",
        "<rect x='0' y='0' width='800' height='200' fill='url(#sky)' />",
        f"<rect x='0' y='200' width='800' height='120' fill='{bg}' />",
    ]

    # draw simple sun/moon depending on time
    hour = datetime.utcnow().hour
    if 6 <= hour <= 18:
        svg_lines.append("<circle cx='80' cy='60' r='28' fill='#FFD54F' opacity='0.9' />")
    else:
        svg_lines.append("<circle cx='80' cy='60' r='22' fill='#ECEFF1' opacity='0.9' />")

    # Add blades of grass based on lushness
    random.seed(health.get("lawnHealthIndex", 50))
    for x in range(0, width, 10):
        h = random.randint(10, 10 + lush // 2)
        svg_lines.append(
            f"<path d='M{x},320 q5,-{h} 0,-{h*2}' stroke='rgba(20,80,20,0.6)' stroke-width='2' fill='none' />"
        )

    # Text background
    svg_lines.append("<rect x='160' y='20' rx='8' ry='8' width='600' height='160' fill='rgba(255,255,255,0.85)' />")
    for idx, line in enumerate(lines[:6]):
        y = text_y + idx * 24
        svg_lines.append(
            f"<text x='180' y='{y}' font-family='monospace' font-size='16' fill='#263238'>{line}</text>"
        )

    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


def update_garden_md(story: str) -> None:
    # Ensure garden.md always displays the current SVG and a brief story
    md = [
        "# The Silly Garden",
        "",
        "![Garden Status](garden.svg)",
        "",
        "```",  # plain fenced block for story text
        story,
        "```",
        "",
        "(Auto-updated by garden-bot)",
        "",
    ]
    with open(GARDEN_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


def main() -> int:
    ctx = parse_issue_pr_context()
    gh_event = ctx["event"]

    # Map GH event to our internal types for light logic
    event_key = {
        "schedule": "schedule",
        "push": "push",
        "issues": "issues_opened",   # default; GH provides types but we keep it simple
        "pull_request": "pull_request_opened",
        "manual": "manual",
    }.get(gh_event, "manual")

    health = load_json(LAWN_JSON)

    recent_line = None
    title_hint = ""
    if event_key.startswith("pull_request"):
        recent_line = whimsical_sentence("seed", ctx.get("id"))
        title_hint = f"PR #{ctx.get('id') or 'x'} Title"
        write_seed_or_weed_file("seed", ctx.get("id"), title_hint)
    elif event_key.startswith("issues"):
        recent_line = whimsical_sentence("weed", ctx.get("id"))
        title_hint = f"Issue #{ctx.get('id') or 'x'} Title"
        write_seed_or_weed_file("weed", ctx.get("id"), title_hint)

    health = update_lawn_health(health, event_key)
    save_json(LAWN_JSON, health)

    story = build_story(health, recent_line)
    svg = generate_svg(health, story)
    with open(GARDEN_SVG, "w", encoding="utf-8") as f:
        f.write(svg)

    update_garden_md(story)
    return 0


if __name__ == "__main__":
    sys.exit(main())

