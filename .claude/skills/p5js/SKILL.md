---
name: p5js
description: >-
  p5.js 2.x for generative visuals in a code-rendered film: instance mode, noLoop()/redraw() driven by window.render(t),
  seeded random() and noise(), pixelDensity(1), async setup() with awaited loadImage/loadFont, 2D and WEBGL modes.
  Use when the user names p5, p5.js or Processing-style sketches, wants generative or procedural art, flow fields,
  noise textures or a creative-coding look.
---

# p5.js in a Lemo-Opuscar film

p5.js (LGPL-2.1, https://github.com/processing/p5.js, reference https://p5js.org/reference/) is the Processing-style
creative-coding library. 2.x (2.3.4 when this was written) differs from 1.x: `preload()` is gone, `setup()` may be
`async` and awaits the loaders. The library's own `render(t)` loop replaces p5's draw loop.

## Install, in the project folder

```sh
cd films/<name> && npm i --no-audit --no-fund p5@2.3.4
```

```html
<script src="./node_modules/p5/lib/p5.min.js"></script>    <!-- UMD build; global p5 -->
```

## Fit the page contract

Use **instance mode**, switch the loop off, and redraw from `t`:

```js
let T = 0, img;
const sketch = (p) => {
  p.setup = async () => {
    p.createCanvas(innerWidth, innerHeight);     // 1920×1080, or whatever --size the render tool passes
    p.pixelDensity(1);                           // the screenshot is 1:1; retina scaling doubles the work
    p.noLoop();                                  // nothing moves on its own
    img = await p.loadImage('assets/plate.png'); // 2.x: await the loaders instead of preload()
    window.READY = true;
  };
  p.draw = () => {
    p.randomSeed(7); p.noiseSeed(7);             // re-seed every frame: the sequence is identical whatever the order
    p.background(245, 240, 230);
    const n = 400;
    for (let i = 0; i < n; i++) {                // positions are a function of (seed, i, T) only
      const a = p.noise(i * 0.05, T * 0.2) * p.TWO_PI;
      p.circle(p.width * p.random(), p.height * p.random(), 4 + 20 * p.abs(p.sin(a + T)));
    }
  };
};
const inst = new p5(sketch, document.body);
window.DUR = 30;
window.render = (t) => { T = t; inst.redraw(); };   // synchronous: the screenshot that follows sees this frame
```

Never read `frameCount`, `millis()`, `deltaTime` or `Date`: they are wall-clock. Everything derives from `T`.

## Useful here

| Need | API |
|---|---|
| Organic motion | `noise(x, y, z)` (seeded by `noiseSeed`), `noiseDetail(octaves, falloff)` |
| Vector maths | `createVector`, `p5.Vector.fromAngle`, `.heading()`, `.lerp()` |
| Colour spaces | `colorMode(HSB, 360, 100, 100, 1)`, `lerpColor` |
| Brush strokes | `beginShape(); curveVertex(...); endShape()`, `strokeWeight`, `blendMode(MULTIPLY)` |
| Offscreen layers | `createGraphics(w, h)` then `image(g, 0, 0)` (keep them alive across frames; only redraw what changes) |
| Pixels | `loadPixels(); pixels[i]; updatePixels()` (slow at 1080p: prefer shaders in WEBGL mode) |
| Shaders | `createCanvas(w, h, WEBGL)`, `createShader(vert, frag)`, `shader(s)`, `s.setUniform('uTime', T)` |
| Text | `textFont(await loadFont('fonts/x.ttf'))`, `textAlign`, `textWidth`, and report it in `window.TEXTS(t)` |

## Pitfalls

- WEBGL mode: p5 keeps `preserveDrawingBuffer` on by default, which is what the screenshot needs; leave it.
- p5 draws through the Canvas 2D API with its own bookkeeping; at 1080p with thousands of primitives it is slower
  than raw canvas. Keep heavy static layers in a `createGraphics` buffer.
- `random()` inside `setup()` runs once; `random()` inside `draw()` must follow a `randomSeed()` call in that draw.
- Global-mode sketches (`function setup() {}`) pollute `window` and cannot coexist with the library's helpers.
- Fonts and images load from the project folder with relative paths; absolute `/core/...` paths reach the library.
