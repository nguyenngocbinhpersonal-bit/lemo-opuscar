---
name: opencut
description: >-
  OpenCut, the open-source browser/desktop video editor, as the last-mile timeline editor for delivered films: what it
  is, its current rewrite status, how to run it locally (proto + moon), what hand edits it suits (trims, reorders,
  overlays, manual review), and how to keep loudness and colour intact after re-export. Use when the user names OpenCut
  or wants to hand-edit a rendered film on a timeline instead of changing the code.
---

# OpenCut around a Lemo-Opuscar film

OpenCut (MIT, https://github.com/OpenCut-app/OpenCut) is a free timeline video editor for web, desktop and mobile. In
October 2026 the project is being rewritten from the ground up (Rust core, one codebase for browser, desktop and
mobile, an Editor API, plugins, an MCP server for agents, a headless mode for batch rendering). Until that lands:

- the **classic** editor is the one to use today: https://opencut.app in the browser, source at
  https://github.com/opencut-app/opencut-classic;
- the rewrite lives at https://new.opencut.app while it matures.

Films in this library are produced from code (`build.sh` → `mux.sh` → `<name>.mp4`). OpenCut is not part of that
pipeline; it is where a human makes a quick manual cut when changing the code is not worth it.

## Good uses

| Need | Do it in OpenCut | Or better, in code |
|---|---|---|
| Trim the head or tail of a delivered film | yes | change `window.DUR` or the timeline, rebuild |
| Reorder two finished films into one reel | yes | `ffmpeg -f concat` (see the `ffmpeg` skill) |
| A one-off overlay (client logo, disclaimer) for one delivery | yes | a layer in `render(t)` keeps every version consistent |
| Review with a client on a scrub-able timeline | yes | stills from `still.mjs` and a contact sheet |
| Change pacing, text, voice, colour | no | that is the film's code and treatment |

## Running it locally (rewrite)

From the README: install `proto` (https://moonrepo.dev/proto), then in the repo root `proto use` (installs the pinned
toolchain), `moon run web:dev` (http://localhost:5173), `moon run api:dev` (:8787), `moon run desktop:dev`. These are
the user's tools to install; do not run the install scripts yourself. The classic editor runs in any modern browser
with no install.

## After an export

OpenCut re-encodes. Before delivering its output:

```sh
ffmpeg -hide_banner -i export.mp4 -af ebur128=peak=true -f null -         # loudness: aim for −14 LUFS, peak ≤ −1 dB
ffprobe -v error -show_entries stream=codec_name,pix_fmt,r_frame_rate,color_range,color_space -of default=nw=1 export.mp4
```

If loudness drifted, normalise the audio again (two-pass `loudnorm`, as `core/render/mux.sh` does) and re-mux with
`-c:v copy`. Keep the frame rate the film was rendered at; keep `yuv420p`.

## Pitfalls

- Browser editors keep projects in the browser's storage: export the project file or the final mp4 before closing.
- Hand edits are not reproducible: note them in the film's `PRODUCTION_LOG` or delivery note so the next version from
  code can include them.
- Upstream is not taking outside contributions during the rewrite; report problems on their Discord or issues.
