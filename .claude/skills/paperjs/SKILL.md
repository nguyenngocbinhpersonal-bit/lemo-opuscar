---
name: paperjs
description: >-
  Paper.js for vector paths in a code-rendered film: Path, CompoundPath, segments and handles, getPointAt/getNormalAt
  along a path, smoothing and simplification, boolean operations (unite, intersect, subtract), dashOffset draw-on,
  SVG import, driven frame by frame from window.render(t) with view.autoUpdate off. Use when the user names paper.js,
  wants bezier or path geometry, a line that draws itself, shapes cut from each other, or vector illustration moves.
---

# Paper.js in a Lemo-Opuscar film

Paper.js (MIT, https://github.com/paperjs/paper.js, reference http://paperjs.org/reference/) is a vector scene graph
on Canvas 2D: paths with bezier handles, hit tests, boolean operations, and geometry queries along a curve. Version
0.16.0 when this was written. Use the core build (plain JavaScript, no PaperScript).

## Install, in the project folder

```sh
cd films/<name> && npm i --no-audit --no-fund paper@0.16.0
```

```html
<canvas id="c" hidpi="off"></canvas>                          <!-- hidpi off: the screenshot is 1:1 -->
<script src="./node_modules/paper/dist/paper-core.js"></script> <!-- global paper -->
```

## Fit the page contract

```js
const canvas = document.getElementById('c');
canvas.width = innerWidth; canvas.height = innerHeight;
paper.setup(canvas);
paper.view.autoUpdate = false;            // we decide when to paint
paper.settings.insertItems = false;       // new items are not added to the scene unless we say so

const layer = paper.project.activeLayer;
const spine = new paper.Path({ segments: [[100, 800], [500, 300], [900, 700], [1500, 200]], strokeColor: '#222', strokeWidth: 3 });
spine.smooth({ type: 'continuous' });
const pen = new paper.Path.Circle({ center: [0, 0], radius: 6, fillColor: '#c33' });
layer.addChildren([spine, pen]);

window.DUR = 12;
window.render = (t) => {
  const u = Math.min(1, t / 6);                       // 0→1 over six seconds
  spine.dashArray = [spine.length, spine.length];     // draw-on: dash as long as the path, offset slides it in
  spine.dashOffset = spine.length * (1 - u);
  const p = spine.getPointAt(spine.length * u), n = spine.getNormalAt(spine.length * u);
  pen.position = p.add(n.multiply(8));                // an item that rides the line
  paper.view.update();                                // paint now; the screenshot follows
};
window.READY = true;
```

Build or mutate items from `t`, then `view.update()`. Never attach `view.onFrame`: it is the wall clock.

## Useful here

| Need | API |
|---|---|
| Shapes | `new Path.Circle({ center, radius })`, `Path.Rectangle`, `Path.RegularPolygon`, `Path.Star`, `Path.Arc` |
| Along a curve | `path.length`, `getPointAt(offset)`, `getTangentAt`, `getNormalAt`, `getCurvatureAt`, `getNearestPoint(pt)` |
| Hand-drawn feel | `path.smooth()`, `path.simplify(tolerance)` on a jittered polyline, `strokeCap: 'round'`, `strokeJoin` |
| Cut-outs (paper-cut, stencil, woodcut) | `a.unite(b)`, `a.subtract(b)`, `a.intersect(b)`, `a.exclude(b)`, `a.divide(b)` |
| Holes and letters | `new CompoundPath({ children: [outer, hole] })`, `fillRule: 'evenodd'` |
| Artwork from a file | `project.importSVG(svgText, { insert: false, expandShapes: true })` then walk `item.children` |
| Transforms | `item.position`, `rotate(deg, center)`, `scale(f, center)`, `item.matrix`, `item.clone()` |
| Hit tests | `project.hitTest(point, { fill: true, stroke: true, tolerance: 4 })` |
| Export | `item.exportSVG()`, `project.exportJSON()` |

Boolean operations run on paths that are **closed** and non-self-intersecting; `path.reduce()` and `path.reorient()`
clean inputs. Keep booleans out of the per-frame path: compute the shapes once per cue and cache them.

## Pitfalls

- Without `hidpi="off"` Paper multiplies the canvas by `devicePixelRatio`; the render tools run at scale 1, but an
  explicit `off` keeps a developer's retina preview and the headless frame identical.
- `view.update()` repaints everything; thousands of segments with shadows are slow. Rasterise static artwork once
  (`item.rasterize()`) or keep it on a second plain canvas.
- Paper's `Point`, `Size` and `Color` are objects, not arrays; `item.position = [x, y]` works, `item.position.x = 1`
  also works (observed objects), but math returns new objects: `p.add(q)`, never `p += q`.
- Text in Paper (`PointText`) must be reported in `window.TEXTS(t)` for `readcheck.mjs`; its bounds are
  `item.bounds`.
