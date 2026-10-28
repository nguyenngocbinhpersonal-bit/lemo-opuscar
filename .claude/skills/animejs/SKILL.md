---
name: animejs
description: >-
  Anime.js v4 (animejs) for timeline orchestration in a code-rendered film: animate(), createTimeline(), stagger(),
  keyframes, SVG line drawing, morphing and motion paths, driven deterministically by seeking the timeline to the
  frame's time instead of letting it play. Use when the user names anime.js / animejs, wants staggered or keyframed
  motion of DOM, SVG or plain JS objects, or asks for a tween timeline inside window.render(t).
---

# Anime.js v4 in a Lemo-Opuscar film

Anime.js (MIT, https://github.com/juliangarnier/anime, docs https://animejs.com/documentation) tweens CSS, SVG and plain
JavaScript object properties on a timeline with easings, keyframes and staggers. v4 (4.5.0 when this was written) is
ES modules only. The v3 API (`anime({ targets })`, `anime.timeline()`) is gone; the migration guide is on the repo wiki.

## Install, in the project folder (never into `$LIB`)

```sh
cd films/<name> && npm i --no-audit --no-fund animejs@4.5.0
```

```html
<script type="importmap">{"imports":{"animejs":"./node_modules/animejs/dist/modules/index.js"}}</script>
```

## The one rule: seek, never play

Autoplay ticks from the wall clock. The page contract (TECHNIQUE.md §2) wants frame `t` drawn from `t` alone, by any
worker, in any order. So every animation is created with `autoplay: false`, lives on one timeline, and `window.render(t)`
seeks it:

```js
import { createTimeline, stagger, svg, utils } from 'animejs';

const state = { x: 0, y: 0, alpha: 0 };                       // plain objects tween like elements
const tl = createTimeline({ autoplay: false, defaults: { ease: 'inOutQuad', duration: 800 } });
tl.add(state, { x: 640, alpha: 1 }, 0)                         // third argument: position on the timeline, ms
  .add('.title span', { y: [40, 0], opacity: [0, 1], delay: stagger(60) }, 400)
  .add(state, { y: 200 }, '<<+=200');                           // relative positions as in the docs

window.DUR = tl.duration / 1000;
window.render = (t) => { tl.seek(t * 1000); draw(state); };   // draw() paints the canvas from state
window.READY = true;
```

- `seek(time)` is absolute (milliseconds; `engine.timeUnit = 's'` switches the whole engine to seconds) and renders at
  once, forwards or backwards. Nothing else may move time: no `play()`, no `createTimer()` callbacks, no `onUpdate`
  side effects that accumulate.
- Mixed targets are fine: tween a plain object and read it in a canvas `draw`, or tween DOM text and let the
  screenshot capture it. DOM text still needs `window.TEXTS(t)` for `readcheck.mjs`.
- `utils.random()` is unseeded. Random values come from `mulberry` / `hash` in `/core/lib.js`, computed once at load.
- `loop: true` and `alternate: true` wrap the seek position; `tl.duration` is one loop, so set `window.DUR` yourself.

## What it is good at here

| Need | API |
|---|---|
| Letters or shapes arriving one after another | `delay: stagger(50, { from: 'center', grid: [cols, rows] })` |
| Several beats on one property | keyframes: `x: [{ to: 100, duration: 400 }, { to: 0, ease: 'outBounce' }]` |
| A line that draws itself (one-line drawing, pen & wash, blueprint) | `svg.createDrawable('path')` then tween `draw: ['0 0', '0 1']` |
| One shape becoming another | `svg.morphTo(targetPath)` (same number of points helps) |
| An object following a path | `const { translateX, translateY, rotate } = svg.createMotionPath(path)` as tween values |
| Reading or setting values outside a tween | `utils.get(el, 'x')`, `utils.set(el, { x: 10 })`, `utils.$('.sel')` |
| Spring feel | `ease: createSpring({ mass, stiffness, damping })` from `animejs` (a time-based easing, so seeking stays exact) |

Easings are strings (`'inOutQuint'`, `'outElastic(1, .5)'`, `'steps(4)'`, `'cubicBezier(.4,0,.2,1)'`) or functions.

## Pitfalls

- Importing `animejs` from a CDN at render time breaks offline, reproducible renders: keep it in `node_modules`.
- `tl.add()` positions default to the end of the previous animation; give explicit positions for anything that must
  line up with a voice cue (`events.json` times).
- Timelines with hundreds of DOM targets are slower to seek than one object tween plus your own draw loop; for dense
  particle motion compute positions from `t` directly (see `core/lib.js` `seg`, `eio`, `spring`).
- Animating CSS `transform` on many elements means the screenshot captures DOM compositing; a canvas you draw yourself
  is both faster and exactly what the grain/mux step expects.
