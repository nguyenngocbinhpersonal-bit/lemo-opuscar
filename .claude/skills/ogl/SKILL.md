---
name: ogl
description: >-
  OGL, the minimal WebGL library, for custom shaders in a code-rendered film: Renderer, Program, Triangle (full-screen
  pass), Mesh, Texture, RenderTarget ping-pong, Post passes, Camera and Transform for light 3D, with uniforms set from
  window.render(t). Use when the user names OGL, wants a fragment-shader look (grain, halftone, dither, CRT, ink,
  displacement, liquid, feedback), a shader transition, or a thin alternative to three.js.
---

# OGL in a Lemo-Opuscar film

OGL (MIT, https://github.com/oframe/ogl, examples https://oframe.github.io/ogl/examples/) is a small WebGL 1/2 library:
no scene bloat, explicit programs and uniforms, a handful of helpers. Version 1.0.11 when this was written. It suits
shader passes over a 2D canvas and small 3D scenes; for materials, lights, glTF and post pipelines use three.js
(the `threejs` skill) and `core/three/post.js`.

## Install, in the project folder

```sh
cd films/<name> && npm i --no-audit --no-fund ogl@1.0.11
```

```html
<script type="importmap">{"imports":{"ogl":"./node_modules/ogl/src/index.js"}}</script>
```

## Fit the page contract: a shader over a 2D canvas

Draw the picture on a plain canvas, upload it as a texture, run one fragment shader, and let the screenshot capture the
GL canvas. Every uniform comes from `t`.

```js
import { Renderer, Program, Triangle, Mesh, Texture } from 'ogl';
const art = document.createElement('canvas'); art.width = 1920; art.height = 1080; const ctx = art.getContext('2d');
const renderer = new Renderer({ width: 1920, height: 1080, dpr: 1, antialias: false, preserveDrawingBuffer: true });
const gl = renderer.gl; document.body.appendChild(gl.canvas);
const tex = new Texture(gl, { image: art, generateMipmaps: false, flipY: true });
const program = new Program(gl, {
  vertex: `attribute vec2 uv, position; varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position, 0., 1.); }`,
  fragment: `precision highp float; varying vec2 vUv; uniform sampler2D tMap; uniform float uTime, uAmount;
    void main(){ vec2 d = vec2(sin(vUv.y * 40. + uTime * 3.) * uAmount, 0.); gl_FragColor = vec4(texture2D(tMap, vUv + d).rgb, 1.); }`,
  uniforms: { tMap: { value: tex }, uTime: { value: 0 }, uAmount: { value: 0.004 } },
});
const quad = new Mesh(gl, { geometry: new Triangle(gl), program });
window.DUR = 20;
window.render = (t) => {
  drawPicture(ctx, t);                 // the 2D part, deterministic in t
  tex.needsUpdate = true;              // re-upload the canvas
  program.uniforms.uTime.value = t;
  renderer.render({ scene: quad });    // no camera for a screen-space pass; synchronous
};
window.READY = true;
```

`preserveDrawingBuffer: true` keeps the frame for the screenshot; `dpr: 1` matches the render size. Film grain is
better added by `mux.sh` (TECHNIQUE.md §2: grain in the page makes every frame incompressible), so use the shader for
the look itself (halftone, ink bleed, chromatic shift, CRT), not for grain.

## Useful here

| Need | API |
|---|---|
| Full-screen pass | `new Triangle(gl)` geometry (one triangle, no seams) |
| Several passes | `const post = new Post(gl); post.addPass({ fragment, uniforms }); post.render({ scene, camera })` |
| Feedback / simulation | two `new RenderTarget(gl, { width, height })`, swap each frame, pass the previous as `tMap`; rebuild from `t = 0` for a given frame or bake a table (the frame must not depend on render order) |
| Light 3D | `Camera(gl, { fov })`, `Transform()`, `Box / Sphere / Plane / Cylinder / Torus(gl)`, `Mesh(gl, { geometry, program })`, `renderer.render({ scene, camera })` |
| Textures | `new Texture(gl, { image, wrapS: gl.REPEAT, minFilter: gl.LINEAR })`, `KTXTexture`, `TextureLoader` |
| Models and text | `GLTFLoader.load(gl, url)` (extras), `Text` (MSDF fonts), `Polyline` (thick lines), `Flowmap`, `Shadow` |
| WebGL2 shaders | `#version 300 es` on the very first line, `in/out` instead of `attribute/varying` |
| Shader transitions | the `gl-transitions` skill: `uniform float progress; sampler2D from, to;` as a `Program` |

## Pitfalls

- Uniforms are `{ value }` objects; replace `.value`, not the object.
- No `requestAnimationFrame`, no `performance.now()`: every per-frame input is `t` or a constant.
- `Renderer` defaults to WebGL2 with a WebGL1 fallback; check `renderer.isWebgl2` before using `#version 300 es`.
- Headless rendering without a GPU falls back to SwiftShader (the render tool warns). Keep passes few and resolutions
  honest: a 2× supersample at 1080p is 8 M fragments per pass.
- The GL canvas and the 2D canvas must have the same size as the page (`innerWidth × innerHeight`) when the film is
  rendered with `--size`.
