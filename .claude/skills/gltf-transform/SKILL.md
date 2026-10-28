---
name: gltf-transform
description: >-
  glTF Transform (CLI and Node API) to inspect, clean, optimise and convert 3D assets before a code-rendered film loads
  them: inspect, optimize, dedup, prune, weld, simplify, resize and compress textures, Draco or Meshopt compression,
  centering and joining. Use when the user has a .glb/.gltf (or exported from Blender, CAD, a scan), a three.js scene
  loads slowly, textures are huge, or a model must be trimmed, recentred or converted for the web.
---

# glTF Transform for film assets

glTF Transform (MIT, https://github.com/donmccurdy/glTF-Transform, docs https://gltf-transform.dev) reads, edits and
writes glTF 2.0 files. Version 4.5.1 when this was written. In this library it prepares models for the 3D styles
(brick toy, glass product, teardown, low-poly island, HD-2D) so the headless three.js page loads fast and stays within
GPU memory.

## CLI, no install needed

```sh
npx --yes @gltf-transform/cli@4.5.1 inspect model.glb                       # scenes, meshes, materials, textures, sizes
npx --yes @gltf-transform/cli@4.5.1 optimize in.glb out.glb --compress draco --texture-compress webp --texture-size 2048
```

`optimize` runs the usual chain (dedup, instance, flatten, join, weld, simplify, resample, prune, sparse, texture
compress and resize, geometry compress). Pieces, when one step is wanted:

| Command | What it does |
|---|---|
| `dedup`, `prune` | merge identical accessors/textures/materials; drop unused nodes and properties |
| `weld`, `simplify --ratio 0.5 --error 0.001` | index vertices, then reduce triangles (meshoptimizer) |
| `resize --width 1024 --height 1024`, `webp`, `avif`, `ktx2` | textures (`ktx2` needs KTX-Software `toktx`) |
| `draco` / `meshopt` / `quantize` | geometry compression (the loader must match, below) |
| `center --pivot center`, `flatten`, `join`, `instance` | place the model at the origin, fewer nodes and draw calls |
| `metalrough`, `unlit`, `sparse` | spec/gloss → metal/rough, unlit materials, sparse accessors |
| `copy a.gltf b.glb` | convert between .gltf + bins and a single .glb |

## Node API, when a script must do it

```sh
npm i --no-audit --no-fund @gltf-transform/core@4.5.1 @gltf-transform/extensions@4.5.1 @gltf-transform/functions@4.5.1 draco3dgltf meshoptimizer sharp
```

```js
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, simplify, textureCompress, center } from '@gltf-transform/functions';
import { MeshoptSimplifier } from 'meshoptimizer';
import draco3d from 'draco3dgltf';
import sharp from 'sharp';
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'draco3d.decoder': await draco3d.createDecoderModule(), 'draco3d.encoder': await draco3d.createEncoderModule() });
const doc = await io.read('in.glb');
await doc.transform(dedup(), prune(), weld(), simplify({ simplifier: MeshoptSimplifier, ratio: 0.5, error: 0.001 }),
  textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [2048, 2048] }), center());
await io.write('out.glb', doc);
```

The document API (`doc.getRoot().listMeshes()`, `material.setBaseColorFactor()`, `node.setTranslation()`) edits
anything the CLI cannot: rename nodes for the film's rig, strip a logo texture, bake a material change.

## Loading the result in three.js (see the `threejs` skill)

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
const loader = new GLTFLoader();
loader.setDRACOLoader(new DRACOLoader().setDecoderPath('/node_modules/three/examples/jsm/libs/draco/'));
loader.setMeshoptDecoder(MeshoptDecoder);
const { scene: model } = await loader.loadAsync('assets/model.glb');
```

Set `window.READY = true` only after the model and its textures are loaded; the render tools wait up to 180 s.

## Rules of the house

- Only CC0 / CC BY models, named in the film's `CREDITS` with source and licence (TECHNIQUE.md §11). Poly Haven
  models and HDRIs are in `core/assets/polyhaven/` (`sh tools/fetch.sh hdri`).
- Optimised copies live in the project folder (`films/<name>/assets/`); the original stays untouched.
- Big textures are the usual culprit for a slow page: 2048 px WebP is enough at 1080p unless the camera fills the
  frame with one surface.
- Draco decodes on the CPU once at load (fine); Meshopt is lighter; KTX2/Basis saves GPU memory for texture-heavy
  scenes but needs the `KTX2Loader` transcoder path.
