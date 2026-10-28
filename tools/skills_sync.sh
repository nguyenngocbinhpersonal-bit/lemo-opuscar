#!/bin/sh
# Refresh the third-party agent skills in .claude/skills/ from their upstream repositories.
#   sh tools/skills_sync.sh                 # all four upstreams
#   sh tools/skills_sync.sh pixijs remotion # only these
# Each upstream is cloned shallow and sparse into a temp folder, its skill folders are copied over the ones
# here (replacing them), and .claude/skills/UPSTREAM.txt records the commit and date. House-written skills
# (listed in .claude/skills/README.md) are never touched. Symlinks are dropped: they do not survive a Windows
# checkout, and every sibling skill is installed next to its router anyway.
set -e
LIB=$(cd "$(dirname "$0")/.." && pwd)
DEST="$LIB/.claude/skills"
LOG="$DEST/UPSTREAM.txt"
[ -d "$DEST" ] || { echo "skills_sync.sh: $DEST not found"; exit 1; }
command -v git >/dev/null || { echo "skills_sync.sh: git not found"; exit 1; }
TMP=$(mktemp -d 2>/dev/null || mktemp -d -t skills)
trap 'rm -rf "$TMP"' EXIT

fetch() {   # fetch <name> <url> <sparse dir>  → clone into $TMP/<name>, print "<name> <url> <commit> <date>"
  git -c core.longpaths=true clone -q --depth 1 --filter=blob:none --sparse "$2" "$TMP/$1"
  ( cd "$TMP/$1" && git config core.longpaths true && git sparse-checkout set "$3" >/dev/null 2>&1 )
  ( cd "$TMP/$1" && printf '%s %s %s %s\n' "$1" "$2" "$(git rev-parse --short=7 HEAD)" "$(git log -1 --format=%cs)" )
}
copy_skills() {   # copy_skills <folder holding one subfolder per skill>
  for d in "$1"/*/; do
    d=${d%/}; n=$(basename "$d")
    [ -f "$d/SKILL.md" ] || { echo "  skip $n (no SKILL.md)"; continue; }
    find "$d" -type l -exec rm -f {} + 2>/dev/null || true     # strip symlinks before copying (cp cannot recreate them)
    rm -rf "$DEST/$n"; cp -R "$d" "$DEST/$n"
    echo "  $n"
  done
}

WANT=${*:-"remotion hyperframes pixijs gl-transitions"}
[ -f "$LOG" ] || printf '# Upstream skills in this folder: name, repository, commit, commit date (written by tools/skills_sync.sh)\n' > "$LOG"
note() { grep -v "^$1 " "$LOG" > "$LOG.tmp" || true; printf '%s\n' "$2" >> "$LOG.tmp"; mv "$LOG.tmp" "$LOG"; }

for u in $WANT; do
  case "$u" in
    remotion)
      echo "remotion: packages/skills/skills (the same set as remotion-dev/skills)"
      L=$(fetch remotion https://github.com/remotion-dev/remotion packages/skills)
      copy_skills "$TMP/remotion/packages/skills/skills"
      # the router links its siblings through symlinks (./remotion-x/); point it at the installed siblings instead
      R="$DEST/remotion-best-practices/SKILL.md"
      [ -f "$R" ] && sed -i.bak -e 's#^\./remotion-#../remotion-#' -e 's#\([^.]\)\./remotion-#\1../remotion-#g' "$R" && rm -f "$R.bak"
      note remotion "$L" ;;
    hyperframes)
      echo "hyperframes: skills/"
      L=$(fetch hyperframes https://github.com/heygen-com/hyperframes skills)
      copy_skills "$TMP/hyperframes/skills"
      note hyperframes "$L" ;;
    pixijs)
      echo "pixijs: skills/"
      L=$(fetch pixijs https://github.com/pixijs/pixijs skills)
      copy_skills "$TMP/pixijs/skills"
      note pixijs "$L" ;;
    gl-transitions)
      echo "gl-transitions: skills/"
      L=$(fetch gl-transitions https://github.com/gl-transitions/gl-transitions skills)
      copy_skills "$TMP/gl-transitions/skills"
      note gl-transitions "$L" ;;
    *) echo "skills_sync.sh: unknown upstream '$u' (remotion, hyperframes, pixijs, gl-transitions)"; exit 1 ;;
  esac
done
echo "recorded in $LOG:"; grep -v '^#' "$LOG"
