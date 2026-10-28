---
name: tsparticles
description: >-
  tsParticles (@tsparticles/engine, slim/all bundles) particle presets in a code-rendered film: configured particles,
  links, polygons, emitters, absorbers, seeded with setRandom and stepped through a fake requestAnimationFrame so frames
  bake deterministically for window.render(t). Use when the user names tsParticles or particles.js, wants a quick
  particle background, constellation lines, confetti, snow, fireworks or bubbles with ready-made options, and when
  deciding between tsParticles and a hand-written seeded particle system.
---

# tsParticles in a Lemo-Opuscar film

tsParticles (MIT, https://github.com/tsparticles/tsparticles, options reference https://particles.js.org) is a
configurable particle engine (shapes, links, emitters, absorbers, trails, collisions) with JSON options and presets.
Version 4.5.0 when this was written. It is a real-time library: it draws on its own canvas from
`requestAnimationFrame` timestamps and `Math.random`. Both must be taken over for a film.

## First decide

A film particle layer written by hand is 30–60 lines: `n` particles whose position is a closed-form function of
`(seed, i, t)` or a baked table, drawn on the film's canvas (`mulberry`, `vnoise`, `seg` from `/core/lib.js`). It is
deterministic, fast and sits under your grade. Use tsParticles when the user asks for it or wants its specific looks
(links between neighbours, polygon masks, emitters with life cycles, preset "fireworks"/"snow"/"confetti") faster than
writing them.

## Install, in the project folder

```sh
cd films/<name> && npm i --no-audit --no-fund @tsparticles/engine@4.5.0 @tsparticles/slim@4.5.0
```

The ESM builds import each other by bare specifier, so an import map must list every `@tsparticles/*` package that
`slim` pulls in (look in `node_modules/@tsparticles/`). Easier: the single-file bundle shipped in the package root
(`tsparticles.slim.bundle.min.js`; check the exact name in `node_modules/@tsparticles/slim/`), loaded with a classic
`<script>`, which exposes `tsParticles` and `loadSlim` on `window`.

## Fit the page contract: own the clock, own the random

Install the hooks **before** the engine script runs, then bake frames in order:

```js
// 1. a requestAnimationFrame we control
const queue = []; let now = 0;
window.requestAnimationFrame = (cb) => (queue.push(cb), queue.length);
window.cancelAnimationFrame = () => {};
window.performance.now = () => now;
function pump(ms) { now = ms; const cbs = queue.splice(0); for (const cb of cbs) cb(ms); }
```

```js
// 2. seeded random (ESM build) and the container
import { tsParticles, setRandom } from '@tsparticles/engine';
import { loadSlim } from '@tsparticles/slim';
import { mulberry } from '/core/lib.js';
setRandom(mulberry(7));                                     // every random draw in the engine now comes from the seed
await loadSlim(tsParticles);
const container = await tsParticles.load({ id: 'p', options: {
  fullScreen: { enable: false }, fpsLimit: 120, smooth: false, background: { color: 'transparent' },
  particles: { number: { value: 120 }, color: { value: '#ffffff' }, size: { value: { min: 1, max: 3 } },
    move: { enable: true, speed: 0.6 }, links: { enable: true, distance: 140, opacity: 0.4 } } } });
// 3. bake: step the engine with our timestamps, copy the canvas per frame
const STEP = 1000 / 24, frames = [];
for (let ms = 0; ms <= DUR * 1000; ms += STEP) { pump(ms); const c = document.createElement('canvas'); c.width = 1920; c.height = 1080; c.getContext('2d').drawImage(container.canvas.element, 0, 0); frames.push(c); }
container.pause();
window.render = (t) => { ctx.drawImage(frames[Math.min(frames.length - 1, Math.round(t * 24))], 0, 0); drawTheRest(ctx, t); };
window.READY = true;
```

Baked canvases cost 8 MB each at 1080p; for a long film bake a smaller layer (960×540, scaled up: particles forgive it)
or keep the particle positions instead of pixels. The baked frames are the same in every worker because the seed, the
options and the timestamps are.

## Options worth knowing

`particles.shape.type` (`circle`, `square`, `triangle`, `polygon`, `star`, `image`, `char`), `particles.opacity` and
`size` with `animation`, `move` (`direction`, `outModes`, `trail`, `attract`, `gravity`), `links` (`triangles`),
`collisions`, `emitters` (`rate`, `life`, `position`), `absorbers`, `interactivity` (irrelevant in a film: disable),
`polygon` mask (plugin), presets (`@tsparticles/preset-*`). The full schema is at https://particles.js.org/docs/.

## Pitfalls

- Without `setRandom` every worker renders different particles and the video flickers between worker boundaries.
- `fpsLimit` below the pump rate drops frames (`smooth: false` and a high `fpsLimit` keep every step).
- Interactivity (hover, click) and `fullScreen` are web-page features; off in a film.
- The engine's canvas is positioned by the container id's element; give it the page size and draw it into the film
  canvas rather than stacking DOM layers.
