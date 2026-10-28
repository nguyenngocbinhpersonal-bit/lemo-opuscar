---
name: react-spring
description: >-
  react-spring (@react-spring/web, pmndrs) spring-physics animation for React UIs: useSpring, useSprings, useTrail,
  useTransition, useChain, SpringValue, config presets, Globals and the rafz frame loop. Use when the user names
  react-spring or wants spring-based motion inside a React or Remotion page. For plain canvas films the closed-form
  spring() in core/lib.js is the first choice; this skill also explains how to step react-spring deterministically
  when React is unavoidable.
---

# react-spring in a Lemo-Opuscar film

react-spring (MIT, https://github.com/pmndrs/react-spring, docs https://www.react-spring.dev) animates React props
with physical springs instead of durations. Package `@react-spring/web` (10.1.2 when this was written) needs React 18
or 19 and a bundler (Vite, or the Remotion / HyperFrames toolchains); it is not a drop-in for the import-map pages
this library renders.

## When to reach for it

- You are building a React page: a Remotion composition (see the `remotion-*` skills), a HyperFrames scene, or a
  mock UI for a Living Screencast style film that is later captured.
- The user asked for react-spring by name.

When the film is a plain canvas page, use `spring(t, k, z)` from `/core/lib.js` (or Remotion's `spring()` in a Remotion
project): both are closed-form in `t`, so a frame rendered alone matches the same frame rendered in sequence. That is
the page contract (TECHNIQUE.md §2).

## Install

```sh
npm i --no-audit --no-fund @react-spring/web@10.1.2
```

## Core API

```jsx
import { useSpring, useSprings, useTrail, useTransition, useChain, animated, config, to } from '@react-spring/web';

const styles = useSpring({ from: { opacity: 0, y: 40 }, to: { opacity: 1, y: 0 }, config: config.gentle });
return <animated.div style={{ opacity: styles.opacity, transform: styles.y.to(y => `translateY(${y}px)`) }} />;
```

| Hook | Use |
|---|---|
| `useSpring(props)` | one set of values; `api.start({...})` for imperative control (`useSpring(() => props)` form) |
| `useSprings(n, i => props)` | n items in parallel |
| `useTrail(n, props)` | n items, each following the previous (staggered reveal) |
| `useTransition(items, props)` | enter / update / leave lifecycle for lists |
| `useChain([refA, refB], [0, 0.5])` | sequence hooks on one timeline |
| `config.default / gentle / wobbly / stiff / slow / molasses` | presets; or `{ mass, tension, friction, clamp, precision }` |
| `SpringValue`, `Controller` | class API outside React |

## Rendering frames deterministically

react-spring integrates its springs step by step on a frame loop driven by `@react-spring/rafz`. Two ways to make a
frame reproducible:

1. **Skip the physics** for stills or to-end states: `Globals.assign({ skipAnimation: true })` makes every spring jump
   to its target. Good for style frames, useless for motion.
2. **Drive the loop yourself** with a fixed step. Set `frameLoop: 'demand'`, supply your own clock, and call
   `raf.advance()` once per step:

```js
import { Globals } from '@react-spring/web';
import { raf } from '@react-spring/rafz';          // a dependency of @react-spring/web
let clock = 0;
Globals.assign({ frameLoop: 'demand', now: () => clock });
export function stepTo(seconds, fps = 60) {          // call after mounting; advance in order within a worker
  for (let ms = clock; ms <= seconds * 1000; ms += 1000 / fps) { clock = ms; raf.advance(); }
}
```

The integrator is step-size dependent: always step at the same `dt`, from the same mount, so every worker produces the
same numbers. A frame requested earlier than the current clock means remounting and stepping from zero. Remotion's
`spring()` avoids all of this, which is why it is the default in Remotion projects.

## Pitfalls

- `animated.div` is required: a plain `<div>` ignores `SpringValue`s.
- Interpolate with `value.to(...)` or `to([a, b], (a, b) => ...)`; do not read `.get()` inside render for motion.
- Springs never "finish" exactly; `precision` and `clamp: true` stop the tail. `duration` in `config` turns the spring
  into an eased tween.
- Layout thrash: animate `transform` and `opacity`, not `width`/`top`.
