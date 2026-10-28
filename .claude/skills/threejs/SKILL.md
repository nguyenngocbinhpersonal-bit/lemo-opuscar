---
name: threejs
description: >-
  three.js 3D scenes in a code-rendered film: the library's own copy (node_modules/three, r170) through an import map,
  a deterministic renderer.render inside window.render(t) with preserveDrawingBuffer, lights and Poly Haven HDRIs,
  glTF models, the house post pipeline core/three/post.js (depth of field, GTAO, bloom, grade), cameras and text.
  Use when the user names three.js or wants 3D (products, toys, miniatures, isometric islands, paper pop-ups, HD-2D),
  or a 3D element inside a 2D style.
---

# three.js in a Lemo-Opuscar film

three.js (MIT, https://github.com/mrdoob/three.js, docs https://threejs.org/docs, API digest for agents
https://github.com/mrdoob/three.js/blob/dev/llms.txt) is the library's 3D engine. The clone ships r170 in
`$LIB/node_modules/three` (`package.json`: `three ^0.170.0`) and `core/three/post.js` is written for it (TECHNIQUE.md
§9). npm is at 0.186.1: a film may install a newer three into its own `node_modules`, but `post.js` then needs
checking against the newer addons, so stay on the library copy unless a feature forces the move.

## Import, from the library copy

```html
<script type="importmap">{"imports":{"three":"/node_modules/three/build/three.module.js","three/addons/":"/node_modules/three/examples/jsm/"}}</script>
```

Absolute paths resolve to the library root in both clone and skill mode (TECHNIQUE.md §2). The demos in
`styles/brick-toy/`, `styles/paper-popup/`, `styles/glass-product/`, `styles/hd-2d/` are the worked examples.

## Fit the page contract

```js
import * as THREE from 'three';
import { makePost } from '/core/three/post.js';
import { eio, seg } from '/core/lib.js';
const W = innerWidth, H = innerHeight;                                 // 1920×1080, or the --size the tool passes
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H); document.body.appendChild(renderer.domElement);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(32, W / H, 0.1, 50);
await buildScene(scene);                                               // models, lights, HDRI: all awaited
const post = makePost(renderer, scene, camera, W, H, { ssaa: 2, ao: true });   // { composer, dof, bloom, vig }
window.DUR = 40;
window.render = (t) => {
  const u = eio(seg(t, 2, 9));                                         // every pose is a function of t
  camera.position.set(4 - 2 * u, 1.6, 5 + u); camera.lookAt(0, 0.4, 0);
  hero.rotation.y = 0.4 * t;
  post.composer.render();                                              // or renderer.render(scene, camera) without post
};
window.READY = true;
```

Rules that keep it deterministic: no `THREE.Clock`, no `requestAnimationFrame`, no `Math.random` (use
`THREE.MathUtils.seededRandom(seed)` or `mulberry` from `/core/lib.js`, evaluated once at build); skinned or glTF
animations are posed with `mixer.setTime(t)`, never `mixer.update(dt)`; GPU simulations and particles are re-run
from zero for the frame or baked at load; `READY` comes after `await loader.loadAsync(...)` of every asset.
`preserveDrawingBuffer: true` is what the screenshot captures; `setPixelRatio(1)` keeps the frame 1:1.

## Light, environment, materials

- HDRI: `RGBELoader` (`three/addons/loaders/RGBELoader.js`) → `new THREE.PMREMGenerator(renderer).fromEquirectangular(tex).texture`
  → `scene.environment`, `scene.environmentIntensity ≈ 0.3–0.6`, plus soft key light (`RectAreaLight` after
  `RectAreaLightUniformsLib.init()`, or a large `DirectionalLight` with a 2048² shadow map). Low HDRI + area lights read
  more real than bright ambient (TECHNIQUE.md §9). Files: `core/assets/polyhaven/*.hdr` after `sh tools/fetch.sh hdri`,
  CC0, listed in `CREDITS` (`core/assets/polyhaven/SOURCES.md`).
- Materials: `MeshStandardMaterial` / `MeshPhysicalMaterial` (`clearcoat`, `transmission`, `sheen`, `iridescence`) for
  products and toys; `MeshToonMaterial` with a 3-step gradient map for cel looks; `MeshMatcapMaterial` for cheap
  stylised shading. Albedo textures: `tex.colorSpace = THREE.SRGBColorSpace`; data maps stay linear.
- Cameras: FOV 20–35 for products and miniatures (tilt-shift = narrow DoF band); `OrthographicCamera` for isometric
  islands and HD-2D; dolly along `new THREE.CatmullRomCurve3(points).getPointAt(u)`.

## The house post pipeline

`makePost(renderer, scene, camera, w, h, { ssaa: 2, ao: true, … })` builds: scene (MSAA + depth) → GTAO → physical
depth of field (CoC ∝ |1/focus − 1/z|, spiral gather) → bloom → grade and vignette → tone mapping/output, rendered at
`ssaa`× and downsampled. Call `post.composer.render()` in `render(t)`; the DoF focus distance, aperture and max CoC,
the AO amount, and `post.bloom.strength / radius / threshold` are the knobs (names and defaults are in the comments at
the top of `core/three/post.js`). It expects a perspective camera: with an orthographic one swap
`perspectiveDepthToViewZ` for `orthographicDepthToViewZ` in its depth pass or the DoF silently breaks.

## Models, text, 2.5D

- glTF: `GLTFLoader` with `DRACOLoader` (`setDecoderPath('/node_modules/three/examples/jsm/libs/draco/')`) and
  `MeshoptDecoder`; optimise first with the `gltf-transform` skill. After loading:
  `model.traverse(o => { if (o.isMesh) o.castShadow = o.receiveShadow = true; })`.
- Text: `TextGeometry` needs a typeface JSON; the house way is a 2D overlay canvas above the GL canvas (see
  `styles/paper-popup/demo/index.html`, `#ov`), drawn in the same `render(t)` and reported in `window.TEXTS(t)`.
- A 3D object inside a 2D style: render three to its own canvas and `ctx.drawImage(renderer.domElement, x, y)` into
  the film canvas (needs `preserveDrawingBuffer`).
- Thick lines: `Line2` / `LineMaterial` from `three/addons/lines/`; `EdgesGeometry` for toon outlines.

## Pitfalls

- Headless GPU: macOS needs `LEMO_ANGLE=metal` (default); a software-rendering warning from the render tool means
  minutes per frame. `LEMO_GPU=high` picks the discrete GPU on dual-GPU laptops (core/README.md).
- Transmission and refraction render the scene twice; reserve them for hero objects.
- Build once, pose per frame. Rebuilding geometry or textures inside `render(t)` leaks GPU memory (`dispose()`) and is
  slow.
- With the post composer leave `renderer.toneMapping` alone (the `OutputPass` applies it); without post set
  `renderer.toneMapping = THREE.ACESFilmicToneMapping` and `outputColorSpace = THREE.SRGBColorSpace`.
- `MathUtils.damp`, `lerp` towards a target each frame and `OrbitControls` are time-integrating: closed-form eases on
  `t` instead.
