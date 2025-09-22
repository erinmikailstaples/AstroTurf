#!/usr/bin/env bash
set -euo pipefail

# Astroturf: make a random, silly grass-themed change and emit a commit message
# This script intentionally confines most edits to the .astroturf/ sandbox
# to avoid disrupting real project files, except for a couple opt-in gags
# like README.md emoji sprinkles.

ROOT_DIR="$(pwd)"
ASTRO_DIR=".astroturf"
mkdir -p "$ASTRO_DIR"

now_iso() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
rand_n() { # rand_n N -> 0..N-1
  local n="$1"
  echo $(( RANDOM % n ))
}

ensure_file() {
  local path="$1"
  if [ ! -f "$path" ]; then
    mkdir -p "$(dirname "$path")"
    printf "# Managed by astroturf\n" > "$path"
  fi
}

append_line() {
  local path="$1"; shift
  printf "%s\n" "$*" >> "$path"
}

write_file() {
  local path="$1"; shift
  printf "%s\n" "$*" > "$path"
}

# Actions
add_green_square() {
  local f="$ASTRO_DIR/green_square_$(date -u +%Y-%m-%d).txt"
  append_line "$f" "🟩 $(now_iso)"
  COMMIT_MSG="add: more green squares"
}

update_fixed_nothing() {
  local f="$ASTRO_DIR/streak.log"
  append_line "$f" "fixed nothing, streak intact @ $(now_iso)"
  COMMIT_MSG="update: fixed nothing, but streak intact"
}

chore_watered_lawn() {
  local f="lawn.txt"
  append_line "$f" "watering: keep it green @ $(now_iso)"
  COMMIT_MSG="chore: watered the lawn"
}

feat_synthetic_turf() {
  local f="fake_grass.md"
  write_file "$f" "## Synthetic Turf\n\nAstroTurf engaged.\n\n```
  _   _           _         _              
 /_\
( ) ( )  _   _  | |_  _ _ (_) ___  _ _    
/_/ \_\ | | | | |  _|| '_|| |/ _ \| ' \   
         \_,_|   \__||_|  |_|\___/|_||_|  
```
\nKeep it green."
  COMMIT_MSG="feat: added synthetic turf"
}

refactor_shuffled_whitespace() {
  local f="$ASTRO_DIR/whitespace.txt"
  ensure_file "$f"
  # Shuffle spaces by appending random spaces
  local spaces=""
  local count=$(( (RANDOM % 8) + 1 ))
  for _ in $(seq 1 $count); do spaces+=" "; done
  append_line "$f" "shuffled${spaces}whitespace"
  COMMIT_MSG="refactor: shuffled whitespace"
}

mow_trimmed_unused_lines() {
  local f="$ASTRO_DIR/grass.txt"
  ensure_file "$f"
  # Remove a trailing space or add if none, to ensure a change
  if tail -n1 "$f" | grep -qE " $"; then
    sed -i 's/[[:space:]]*$//' "$f"
  else
    sed -i '$s/$/ /' "$f" || true
  fi
  COMMIT_MSG="mow: trimmed unused lines"
}

fertilize_boosted_growth() {
  local f="README.md"
  if [ ! -f "$f" ]; then
    write_file "$f" "# README\n\nSprinkled by astroturf $(now_iso)"
  fi
  append_line "$f" "🌱"
  COMMIT_MSG="fertilize: boosted growth"
}

weed_removed_one_todo() {
  local f="$ASTRO_DIR/todos.txt"
  ensure_file "$f"
  if grep -q "TODO:" "$f"; then
    sed -i '0,/TODO:/s//DONE:/' "$f"
  else
    append_line "$f" "TODO: remove one weed @ $(now_iso)"
  fi
  COMMIT_MSG="weed: removed one TODO"
}

watering_keep_it_green() {
  local f="lawn.txt"
  append_line "$f" "watering @ $(now_iso)"
  COMMIT_MSG="watering: keep it green"
}

docs_pointless_commit() {
  local f="ASTROTURF.md"
  write_file "$f" "# This commit is pointless\n\nAstroturf exists to satirize green-square worship.\n\n- It makes noise.\n- It changes nothing.\n- It keeps the lawn green.\n\nTimestamp: $(now_iso)\n"
  COMMIT_MSG="docs: explain why this commit is pointless"
}

haiku_random() {
  local f="$ASTRO_DIR/haiku.txt"
  local h1=("Fake grass still lush" "Squares glow without substance" "Morning dew, not real")
  local h2=("Streaks tend plastic heavens" "Commits for their own sake" "Pixels praise the grid")
  local h3=("Astro hearts rejoice" "Silence in the codebase" "Green is guaranteed")
  append_line "$f" "${h1[$(rand_n ${#h1[@]})]}"
  append_line "$f" "${h2[$(rand_n ${#h2[@]})]}"
  append_line "$f" "${h3[$(rand_n ${#h3[@]})]}"
  append_line "$f" "---"
  COMMIT_MSG="commit: for the metric, not the code"
}

grid_art() {
  local f="grid.txt"
  local size=$(( (RANDOM % 6) + 5 ))
  {
    echo "# Green grid $(now_iso)"
    for _ in $(seq 1 $size); do
      line=""
      for _ in $(seq 1 $size); do line+="🟩"; done
      echo "$line"
    done
  } > "$f"
  COMMIT_MSG="meta: square worship ritual complete"
}

json_square_green() {
  local f="$ASTRO_DIR/square.json"
  local lush=$(( (RANDOM % 30) + 70 ))
  cat > "$f" <<JSON
{
  "square": "still green",
  "lushness_percent": $lush,
  "timestamp": "$(now_iso)",
  "ritual": true
}
JSON
  COMMIT_MSG="chore: square still green"
}

growth_report() {
  local f="$ASTRO_DIR/growth.md"
  local lush=$(( (RANDOM % 30) + 70 ))
  local weeds=$(( RANDOM % 5 ))
  append_line "$f" "## Growth report $(now_iso)"
  append_line "$f" "- lushness: ${lush}%"
  append_line "$f" "- weeds removed: ${weeds}"
  append_line "$f" "- hydration: optimal"
  COMMIT_MSG="chore: growth report updated (99% lushness)"
}

meta_anxiety_fix() {
  local f="$ASTRO_DIR/anxiety.txt"
  append_line "$f" "Feeling better now that streak survived @ $(now_iso)"
  COMMIT_MSG="fix: my anxiety about losing the streak"
}

pick_and_run() {
  local actions=( \
    add_green_square \
    update_fixed_nothing \
    chore_watered_lawn \
    feat_synthetic_turf \
    refactor_shuffled_whitespace \
    mow_trimmed_unused_lines \
    fertilize_boosted_growth \
    weed_removed_one_todo \
    watering_keep_it_green \
    docs_pointless_commit \
    haiku_random \
    grid_art \
    json_square_green \
    growth_report \
    meta_anxiety_fix \
  )
  local idx=$(rand_n ${#actions[@]})
  local chosen="${actions[$idx]}"
  echo "Astroturf chose: $chosen"
  $chosen
}

COMMIT_MSG="meta: astroturf did something green"
pick_and_run

# Emit commit message for the composite action output
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  echo "commit_message=$COMMIT_MSG" >> "$GITHUB_OUTPUT"
fi