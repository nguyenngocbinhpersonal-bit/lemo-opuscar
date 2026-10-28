---
name: matterjs
description: >-
  Matter.js 2D rigid-body physics in a code-rendered film: Engine, Bodies, Composite, Constraint, collision events,
  stepped at a fixed delta and baked into a per-frame table so window.render(t) can draw any frame deterministically.
  Use when the user names matter.js, wants things that fall, stack, bounce, swing, topple, pile up or collide in 2D,
  rope and chain constraints, or physics-driven sound cues.
---

# Matter.js in a Lemo-Opuscar film

Matter.js (MIT, https://github.com/liabru/matter-js, docs https://brm.io/matter-js/docs/) is a 2D rigid-body engine:
rectangles, circles, polygons, compound bodies, constraints, collision events. Version 0.20.0 when this was written.
You draw the bodies yourself on the film's canvas; Matter's `Render` and `Runner` (real-time helpers) are not used.

## Install, in the project folder

```sh
cd films/<name> && npm i --no-audit --no-fund matter-js@0.20.0
```

```html
<script src="./node_modules/matter-js/build/matter.min.js"></script>   <!-- global Matter -->
```

## Fit the page contract: bake, then look up

A simulation carries state from step to step; the page contract (TECHNIQUE.md §2) wants any frame alone. Resolve it
by stepping once at load with a fixed delta and storing a snapshot per step; `render(t)` only reads the table.

```js
const { Engine, Bodies, Body, Composite, Constraint, Events } = Matter;
const STEP = 1 / 60, DUR = 20;
const engine = Engine.create({ gravity: { x: 0, y: 1 } });   // y down, 1 ≈ 9.8 m/s² at Matter's default scale
const ground = Bodies.rectangle(960, 1060, 1920, 60, { isStatic: true });
const crates = Array.from({ length: 24 }, (_, i) => Bodies.rectangle(700 + (i % 4) * 90, 100 - Math.floor(i / 4) * 90, 80, 80, { restitution: 0.1, friction: 0.6 }));
Composite.add(engine.world, [ground, ...crates]);

const frames = [], EV = [];
Events.on(engine, 'collisionStart', e => {                    // sound cues from the physics
  const t = frames.length * STEP;
  for (const p of e.pairs) { const v = Math.hypot(p.bodyA.velocity.x - p.bodyB.velocity.x, p.bodyA.velocity.y - p.bodyB.velocity.y); if (v > 2) EV.push({ t, type: 'thump', gain: Math.min(1, v / 12) }); }
});
for (let i = 0; i <= Math.ceil(DUR / STEP); i++) {
  frames.push(crates.map(b => ({ x: b.position.x, y: b.position.y, a: b.angle, v: b.vertices.map(v => [v.x, v.y]) })));
  Engine.update(engine, STEP * 1000);                          // delta in ms, always the same
}
window.DUR = DUR; window.EV = EV;
window.render = (t) => {
  const f = Math.min(frames.length - 1, t / STEP), i = Math.floor(f), k = f - i, A = frames[i], B = frames[Math.min(frames.length - 1, i + 1)];
  ctx.clearRect(0, 0, 1920, 1080);
  A.forEach((s, j) => { const b = B[j]; drawCrate(ctx, s.x + (b.x - s.x) * k, s.y + (b.y - s.y) * k, s.a + (b.a - s.a) * k); });
};
window.READY = true;
```

- Same bodies, same insertion order, same delta → the same table in every worker (one browser build, one platform).
- Memory: a snapshot per body per step; 60 steps/s × 60 s × 200 bodies is fine. For long films store every 2nd step
  and interpolate, or only `x, y, angle` and rebuild vertices from the body's shape.
- Export `EV` with `node core/render/events.mjs` and let `mix.py` place `sfx.thump()` at those times (TECHNIQUE.md §6).
- Scripted pushes happen inside the bake loop at a chosen step: `Body.applyForce(b, b.position, { x: 0.05, y: -0.1 })`,
  `Body.setVelocity`, `Body.setAngularVelocity`, `Body.setPosition` (kinematic moves).

## Useful here

| Need | API |
|---|---|
| Shapes | `Bodies.rectangle`, `circle`, `polygon(x, y, sides, r)`, `trapezoid`, `fromVertices(x, y, [[{x,y},…]])` (concave needs `poly-decomp` via `Common.setDecomp`) |
| Compound | `Body.create({ parts: [a, b] })` |
| Ropes, pendulums, bridges | `Constraint.create({ bodyA, pointA, bodyB, pointB, length, stiffness, damping })`, `Composites.chain`, `Composites.stack` |
| Materials | `restitution`, `friction`, `frictionAir`, `density`, `slop`, `collisionFilter: { group, category, mask }` |
| Sensors and queries | `isSensor: true`, `Query.point(bodies, pt)`, `Query.ray`, `Query.region` |
| No-gravity, slow-motion | `engine.gravity.scale`, `engine.timing.timeScale` (keep constant across the bake) |
| Sleeping | `engine.enableSleeping = true` speeds long piles; wake with `Sleeping.set(b, false)` |

## Pitfalls

- Matter is unitless; keep sizes in screen pixels and gravity near 1. Tiny or huge bodies tunnel: smaller `STEP` or
  thicker walls, not `timeScale` tricks.
- `Engine.update` with a varying delta changes the outcome: never derive the delta from the frame rate or `t`.
- Drawing with `body.vertices` is exact for polygons; circles are polygons too (`circle(…, { … }, maxSides)`), draw
  them as arcs from `position` and `circleRadius`.
- `Render.create` opens its own canvas and loop; do not use it in a film page (fine in a scratch preview).
