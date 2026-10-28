---
name: rapier
description: >-
  Rapier 3D (and 2D) physics via @dimforge/rapier3d-compat in a code-rendered film: World, RigidBodyDesc, ColliderDesc,
  fixed timestep, collision events, snapshots, stepped once and baked so window.render(t) poses three.js or OGL meshes
  deterministically. Use when the user names Rapier, wants 3D collisions, falling or stacking objects, ragdoll or
  joints, kinematic pushers, or physics in a three.js scene.
---

# Rapier in a Lemo-Opuscar film

Rapier (Apache-2.0, https://github.com/dimforge/rapier, JS guide https://rapier.rs/docs/user_guides/javascript) is a
Rust rigid-body engine compiled to WebAssembly: rigid bodies, colliders, joints, ray casts, contact and collision
events, deterministic on one platform. Use the `-compat` packages (the wasm is embedded, no bundler needed), version
0.21.0 when this was written. 2D twin: `@dimforge/rapier2d-compat`, same API with `{x, y}`.

## Install, in the project folder

```sh
cd films/<name> && npm i --no-audit --no-fund @dimforge/rapier3d-compat@0.21.0
```

```html
<script type="importmap">{"imports":{
  "@dimforge/rapier3d-compat":"./node_modules/@dimforge/rapier3d-compat/dist/rapier.mjs",
  "three":"/node_modules/three/build/three.module.js","three/addons/":"/node_modules/three/examples/jsm/"}}</script>
```

## Fit the page contract: bake, then pose

```js
import RAPIER from '@dimforge/rapier3d-compat';
await RAPIER.init();                                               // loads the wasm; do this before READY

const STEP = 1 / 60, DUR = 15;
const world = new RAPIER.World({ x: 0, y: -9.81, z: 0 });
world.timestep = STEP;                                             // fixed, always
world.createCollider(RAPIER.ColliderDesc.cuboid(10, 0.1, 10));     // ground, attached to nothing = static
const bodies = [];
for (let i = 0; i < 40; i++) {
  const b = world.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation((i % 5) * 0.52 - 1, 1 + Math.floor(i / 5) * 0.55, 0));
  world.createCollider(RAPIER.ColliderDesc.cuboid(0.25, 0.25, 0.25).setRestitution(0.2).setFriction(0.8).setActiveEvents(RAPIER.ActiveEvents.COLLISION_EVENTS), b);
  bodies.push(b);
}
const events = new RAPIER.EventQueue(true), frames = [], EV = [];
for (let s = 0; s <= Math.ceil(DUR / STEP); s++) {
  frames.push(bodies.map(b => { const p = b.translation(), q = b.rotation(); return [p.x, p.y, p.z, q.x, q.y, q.z, q.w]; }));
  world.step(events);
  events.drainCollisionEvents((h1, h2, started) => { if (started) EV.push({ t: s * STEP, type: 'click' }); });
}
window.DUR = DUR; window.EV = EV;
window.render = (t) => {                                           // meshes[], lerp3() and quat() are yours
  const f = Math.min(frames.length - 1, t / STEP), i = Math.floor(f), k = f - i, A = frames[i], B = frames[Math.min(frames.length - 1, i + 1)];
  meshes.forEach((m, j) => { m.position.set(...lerp3(A[j], B[j], k)); m.quaternion.slerpQuaternions(quat(A[j]), quat(B[j]), k); });
  renderer.render(scene, camera);                                  // three.js, see the threejs skill
};
window.READY = true;
```

- Rapier is deterministic for the same build, platform, insertion order and timestep. All workers run the same bake,
  so all frames agree. Seed any scripted randomness with `mulberry` from `/core/lib.js`.
- Long films: `world.takeSnapshot()` every N steps, then `RAPIER.World.restoreSnapshot(bytes)` and step forward to
  reach an arbitrary `t` without a full table.
- Collision events need `setActiveEvents(COLLISION_EVENTS)` on at least one collider of the pair; contact force
  events (`CONTACT_FORCE_EVENTS`, `drainContactForceEvents`) give impact strength for sound gains.

## Useful here

| Need | API |
|---|---|
| Body types | `RigidBodyDesc.dynamic() / fixed() / kinematicPositionBased() / kinematicVelocityBased()` |
| Driven props (a hand, a piston) | kinematic body + `b.setNextKinematicTranslation(v)` / `setNextKinematicRotation(q)` each step |
| Shapes | `ColliderDesc.cuboid, ball, capsule, cylinder, cone, convexHull(points), trimesh(vertices, indices), heightfield` |
| Materials | `.setRestitution`, `.setFriction`, `.setDensity`, `.setSensor(true)`, `.setCollisionGroups(bits)` |
| Impulses | `b.applyImpulse({x,y,z}, true)`, `applyTorqueImpulse`, `setLinvel`, `setAngvel`, `b.sleep()` |
| Joints | `world.createImpulseJoint(RAPIER.JointData.revolute/spherical/prismatic/fixed(...), b1, b2, true)` |
| Queries | `world.castRay(ray, maxToi, solid)`, `intersectionsWithPoint`, `world.debugRender()` → `{vertices, colors}` lines |
| Damping, CCD | `RigidBodyDesc.setLinearDamping / setAngularDamping / setCcdEnabled(true)` for fast small bodies |

## Pitfalls

- Units are metres and kilograms; a 1080p-pixel scene scaled 1:1 explodes. Model in metres and scale the camera.
- `world.step()` without the fixed `timestep` set uses the default 1/60; varying it changes the result.
- `RAPIER.init()` is async; everything that builds the world waits for it, and `READY` comes after the bake.
- Meshes come from three.js / OGL / glTF; Rapier only knows colliders. Keep collider shapes simpler than the visible
  mesh (a convex hull or a few cuboids) or the bake crawls.
