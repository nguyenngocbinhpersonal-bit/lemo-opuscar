# Third-party tool skills

One agent skill per tool of the "20 open-source skills for video" toolkit (@hzxuang on X, 27 Oct 2026:
https://x.com/hzxuang/status/2114993119460507954), installed here so an agent working in this clone has each tool at
hand when a film calls for it. Claude Code discovers every `.claude/skills/<name>/SKILL.md` automatically; the film
pipeline itself (`core/`, `styles/`, the guides) is unchanged.

Two kinds of skill:

- **Upstream**: copied as published in the tool's own repository, without edits (one exception below).
  `sh tools/skills_sync.sh [name …]` refreshes them and `UPSTREAM.txt` records the commit and date of each copy.
- **House**: written for this library. Each says how the tool fits the page contract (`window.render(t)` drawn from `t`
  alone, TECHNIQUE.md §2), how to install it pinned into the project folder (never into `$LIB`), the API that matters
  for a film, and the pitfalls. Versions are those current on 2026-10-28.

| # | Tool | Role | Skill(s) | Origin | Licence of the tool |
|---|---|---|---|---|---|
| 01 | Remotion | React video engine | `remotion-best-practices` (router), `remotion-create`, `-markup`, `-render`, `-studio`, `-captions`, `-multimedia`, `-maps`, `-interactivity`, `-saas`, `-docs`, `-upgrade` | upstream: remotion-dev/remotion `packages/skills/skills` (the set `npx skills add remotion-dev/skills` installs) | Remotion licence (free for individuals and small teams; see remotion.dev) |
| 02 | HyperFrames | HTML to video renderer | `hyperframes` (read first), `hyperframes-cli`, `hyperframes-registry`, `media-use`, `remotion-to-hyperframes`, `slideshow`, `figma` | upstream: heygen-com/hyperframes `skills/` | Apache-2.0 |
| 03 | Anime.js | timeline orchestration | `animejs` | house | MIT |
| 04 | React Spring | spring animation | `react-spring` | house (upstream `.claude/skills` holds only spec-kit workflow skills) | MIT |
| 05 | PixiJS | GPU-driven 2D graphics | `pixijs` (router) + 25 `pixijs-*` topic skills | upstream: pixijs/pixijs `skills/` | MIT |
| 06 | p5.js | generative visuals | `p5js` | house | LGPL-2.1 |
| 07 | Paper.js | vector paths | `paperjs` | house | MIT |
| 08 | Matter.js | 2D physics | `matterjs` | house | MIT |
| 09 | Three.js | 3D scenes | `threejs` | house (the library ships r170 and `core/three/post.js`) | MIT |
| 10 | Rapier | 3D collision | `rapier` | house | Apache-2.0 |
| 11 | OGL | custom shaders | `ogl` | house | MIT |
| 12 | tsParticles | particle effects | `tsparticles` | house (upstream `.agents/skills` holds only monorepo/CI skills) | MIT |
| 13 | glTF Transform | 3D asset optimisation | `gltf-transform` | house | MIT |
| 14 | GL Transitions | shader transitions | `gl-transitions` | upstream: gl-transitions/gl-transitions `skills/` | MIT |
| 15 | OBS Studio | screen capture | `obs-studio` | house | GPL-2.0 |
| 16 | Chatterbox | voice-over, voice cloning | `chatterbox` | house | MIT (outputs carry a PerTh watermark) |
| 17 | Tone.js | synthesisers and sound effects | `tonejs` | house | MIT |
| 18 | faster-whisper | subtitle transcription | `faster-whisper` | house (already used by `core/tts/asr_check.py`) | MIT |
| 19 | OpenCut | timeline editing | `opencut` | house | MIT |
| 20 | FFmpeg | encoding and delivery | `ffmpeg` | house (already used by `core/render/mux.sh`, `video.mjs`) | LGPL-2.1+ / GPL |

The one edit to an upstream copy: Remotion's router links its sibling skills through symlinks (`./remotion-x/`), which
do not survive a Windows checkout; `skills_sync.sh` drops the symlinks and points the links at the installed siblings
(`../remotion-x/`). Every other upstream file is byte-identical to its source commit.

## Using them

- The house skills assume the library conventions: a film lives in `films/<name>/` (or the user's folder in skill
  mode), packages go into that folder's `node_modules` or a private venv, pages reach the library with absolute URLs
  (`/core/lib.js`, `/node_modules/three/…`) and their own packages with relative ones (`./node_modules/…`).
- Physics, particle and tween libraries are real-time by design; the house skills each show the bake-or-seek pattern
  that makes any frame renderable alone, in any order, by any worker.
- Voice: Chatterbox has no Vietnamese; `core/tts/tts_zh.py` (edge-tts) stays the route for `vi-VN`.
- A session may also carry a `remotion` plugin with the same twelve skills; the duplicates are harmless.
- `agent-reach/` in this folder is a separate internet-research skill, not part of this toolkit.

## Refreshing

```sh
sh tools/skills_sync.sh                     # all four upstreams
sh tools/skills_sync.sh pixijs hyperframes  # some
```

Run from the library root. Needs git; on Windows it sets `core.longpaths` for the clone. House skills are never
touched; when a tool gains an official skill upstream, add it to the script and retire the house file.

Each skill's description is loaded into every session; keep descriptions to a few lines when editing.
