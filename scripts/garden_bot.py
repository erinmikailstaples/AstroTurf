#!/usr/bin/env python3

import json
import os
import random
import re
import sys
from datetime import datetime, timezone
import html


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
    margin_x, margin_y = 20, 20

    # Color based on health
    lush = int(health.get("lushnessPercent", 50))
    green = clamp(int(100 + lush * 1.5), 0, 255)
    grass = f"rgb(30,{green},60)"

    def wrap_text_to_width(text: str, max_chars: int) -> list[str]:
        wrapped: list[str] = []
        for original_line in (text or "").splitlines():
            if len(original_line) <= max_chars:
                wrapped.append(original_line)
                continue
            # rough character-based wrap that works predictably in SVG
            start = 0
            while start < len(original_line):
                wrapped.append(original_line[start : start + max_chars])
                start += max_chars
        return wrapped or [""]

    # Build responsive SVG with richer scene
    content_width = width - 2 * margin_x - 160  # bubble width
    approx_char_px = 9  # 16px monospace ~ 9px per character
    max_chars = max(24, int(content_width / approx_char_px))
    wrapped_lines = wrap_text_to_width(story, max_chars)[:8]

    hour = datetime.utcnow().hour
    is_day = 6 <= hour <= 18

    svg_lines = [
        # width=100% for responsiveness; height auto; keep viewBox for scaling
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' width='100%' height='auto' preserveAspectRatio='xMidYMid meet' role='img' aria-label='Silly Garden status'>",
        "<defs>",
        "  <linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'>",
        "    <stop offset='0%' stop-color='#87CEEB' />",
        "    <stop offset='100%' stop-color='#E0F7FA' />",
        "  </linearGradient>",
        "  <linearGradient id='hill' x1='0' y1='0' x2='0' y2='1'>",
        "    <stop offset='0%' stop-color='rgba(20,120,40,0.95)' />",
        "    <stop offset='100%' stop-color='rgba(10,80,30,0.95)' />",
        "  </linearGradient>",
        "  <filter id='ds' x='-10%' y='-10%' width='120%' height='120%'>",
        "    <feDropShadow dx='0' dy='2' stdDeviation='3' flood-color='rgba(0,0,0,0.25)' />",
        "  </filter>",
        "  <style><![CDATA[\n      .label { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; fill: #263238; }\n      .card { fill: rgba(255,255,255,0.9); }\n      svg { max-width: 100%; height: auto; }\n    ]]></style>",
        "</defs>",
        "<rect x='0' y='0' width='800' height='200' fill='url(#sky)' />",
        f"<rect x='0' y='200' width='800' height='120' fill='{grass}' />",
    ]

    # Sun/moon and sky details
    if is_day:
        svg_lines.append("<circle cx='80' cy='60' r='28' fill='#FFD54F' opacity='0.95' />")
        # a couple clouds
        svg_lines.append("<g fill='white' opacity='0.9'>\n  <ellipse cx='260' cy='70' rx='36' ry='18'/>\n  <ellipse cx='285' cy='70' rx='24' ry='14'/>\n  <ellipse cx='240' cy='70' rx='24' ry='14'/>\n</g>")
        svg_lines.append("<g fill='white' opacity='0.85'>\n  <ellipse cx='560' cy='50' rx='30' ry='15'/>\n  <ellipse cx='585' cy='50' rx='20' ry='12'/>\n  <ellipse cx='540' cy='50' rx='20' ry='12'/>\n</g>")
    else:
        svg_lines.append("<circle cx='80' cy='60' r='22' fill='#ECEFF1' opacity='0.95' />")
        # stars
        random.seed(42)
        star_points = []
        for _ in range(25):
            sx = random.randint(120, 780)
            sy = random.randint(20, 140)
            star_points.append(f"<circle cx='{sx}' cy='{sy}' r='1.8' fill='white' opacity='0.9' />")
        svg_lines.extend(star_points)

    # Distant rolling hills for depth
    svg_lines.append("<path d='M0,190 C120,150 220,220 360,190 C500,160 620,210 800,180 L800,200 L0,200 Z' fill='url(#hill)' opacity='0.25' />")
    svg_lines.append("<path d='M0,205 C160,175 260,230 420,205 C580,180 660,220 800,200 L800,220 L0,220 Z' fill='url(#hill)' opacity='0.35' />")

    # Add blades of grass based on lushness
    random.seed(health.get("lawnHealthIndex", 50))
    for x in range(0, width, 10):
        blade_h = random.randint(10, 10 + lush // 2)
        svg_lines.append(
            f"<path d='M{x},320 q5,-{blade_h} 0,-{blade_h*2}' stroke='rgba(20,80,20,0.6)' stroke-width='2' fill='none' />"
        )

    # Flowers for seeds and thistles for weeds near the foreground
    seeds = health.get("seeds", {}).get("count", 0)
    weeds = health.get("weeds", {}).get("count", 0)
    for i in range(min(12, seeds)):
        fx = 120 + i * 50
        svg_lines.append(
            f"<g transform='translate({fx},270)'>\n  <line x1='0' y1='0' x2='0' y2='40' stroke='#2e7d32' stroke-width='2'/>\n  <circle cx='0' cy='0' r='6' fill='#ff6f61'/>\n  <circle cx='-6' cy='-3' r='4' fill='#ffd166'/>\n  <circle cx='6' cy='-3' r='4' fill='#ffd166'/>\n</g>"
        )
    for i in range(min(12, weeds)):
        wx = 140 + i * 50
        svg_lines.append(
            f"<g transform='translate({wx},300)'>\n  <path d='M0,0 q-6,-16 0,-32 q6,16 0,32' fill='none' stroke='#6d4c41' stroke-width='2'/>\n  <circle cx='0' cy='-32' r='5' fill='#8e24aa'/>\n</g>"
        )

    # Text bubble with wrapping using foreignObject and fallback <text> tspans
    bubble_x, bubble_y = 160, 20
    bubble_w, bubble_h = 600, 180
    svg_lines.append(
        f"<rect x='{bubble_x}' y='{bubble_y}' rx='10' ry='10' width='{bubble_w}' height='{bubble_h}' class='card' filter='url(#ds)' />"
    )

    # Prefer foreignObject for natural wrapping
    html_story = "<br/>".join(html.escape(line) for line in story.splitlines())
    svg_lines.append("<switch>")
    svg_lines.append(
        f"  <foreignObject x='{bubble_x + 16}' y='{bubble_y + 14}' width='{bubble_w - 32}' height='{bubble_h - 28}' requiredExtensions='http://www.w3.org/1999/xhtml'>\n    <div xmlns='http://www.w3.org/1999/xhtml' style='font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, \"Liberation Mono\", monospace; font-size:16px; line-height:1.35; color:#263238; word-wrap:break-word; overflow:hidden'>{html_story}</div>\n  </foreignObject>"
    )
    # Fallback for renderers without foreignObject support
    svg_lines.append("  <g>")
    text_y = bubble_y + 24
    for idx, line in enumerate(wrapped_lines):
        y = text_y + idx * 22
        safe = html.escape(line)
        svg_lines.append(
            f"    <text x='{bubble_x + 20}' y='{y}' class='label' font-size='16'>{safe}</text>"
        )
    svg_lines.append("  </g>")
    svg_lines.append("</switch>")

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

