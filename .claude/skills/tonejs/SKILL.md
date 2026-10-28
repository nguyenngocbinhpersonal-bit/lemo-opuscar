---
name: tonejs
description: >-
  Tone.js synthesizers, samplers, effects and Transport scheduling for a film's score and sound design, rendered
  offline with Tone.Offline to a WAV at the film's length and cue times from events.json. Use when the user names
  Tone.js, wants synthesised music, a chiptune/ambient/pad score, rhythmic stingers, or Web Audio effects, and when
  choosing between Tone.js and the library's numpy sampler/sfx tools.
---

# Tone.js for the score

Tone.js (MIT, https://github.com/Tonejs/Tone.js, docs https://tonejs.github.io/docs/) is a Web Audio framework:
synths, samplers, effects, a Transport with musical time (`'4n'`, `'1m'`, `bpm`). Version 15.1.22 when this was written.
The library's default score path is Python (`core/audio/sampler.py`, `pluck.py`, `sfx.py`: TECHNIQUE.md §5–6) because it
needs no browser. Tone.js earns its place when the score is synth-based (FM, subtractive, chip), when the user wants
Web Audio effects, or when they ask for it.

## Install, in the project folder

```sh
cd films/<name> && npm i --no-audit --no-fund tone@15.1.22
```

```html
<script type="importmap">{"imports":{"tone":"./node_modules/tone/build/esm/index.js"}}</script>
```

## Render offline, never in real time

`Tone.Offline(callback, duration, channels = 2, sampleRate)` builds a fresh offline context, runs your scheduling, and
resolves to a `ToneAudioBuffer`. Create every node **inside** the callback (they must belong to the offline context).
Cue times come from `events.json` (`node core/render/events.mjs <demo>`), so the music lands on the picture.

```js
import * as Tone from 'tone';
const { dur, ev } = await (await fetch('./events.json')).json();
const buffer = await Tone.Offline(async ({ transport }) => {
  const reverb = new Tone.Reverb({ decay: 3, wet: 0.25 }).toDestination();
  await reverb.ready;                                         // impulse generated before rendering
  const pad = new Tone.PolySynth(Tone.FMSynth, { envelope: { attack: 0.8, release: 2 } }).connect(reverb);
  const hit = new Tone.MembraneSynth().toDestination();
  transport.bpm.value = 92;
  new Tone.Part((time, chord) => pad.triggerAttackRelease(chord, '2m', time),
    [[0, ['C3', 'G3', 'E4']], ['2m', ['A2', 'E3', 'C4']], ['4m', ['F2', 'C3', 'A3']]]).start(0);
  for (const e of ev) if (e.type === 'thump') hit.triggerAttackRelease('C1', '8n', e.t, e.gain ?? 1);   // picture cues
  transport.start(0);
}, dur, 2, 48000);
```

Write the buffer as a 48 kHz WAV (16- or 24-bit PCM: interleave `buffer.toArray()` channels, prepend a RIFF header)
and save it as `out/music.wav`; `mix.py` or `sfx.add()` then layers voice and foley, and `mux.sh` normalises loudness
(−14 LUFS, true peak −1.2 dB), so leave 6 dB of headroom rather than limiting in Tone.

Run the page once in a browser and download the WAV, or drive it headless with the library's `playwright-core`
(`node_modules/playwright-core` after `setup.sh deps`): open the page, `page.evaluate` the render, return the WAV as
base64, write it with `fs.writeFileSync`. Chromium's offline audio context runs faster than real time.

## Useful here

| Need | API |
|---|---|
| Instruments | `Synth`, `PolySynth(Voice, opts)`, `FMSynth`, `AMSynth`, `MonoSynth`, `MembraneSynth`, `MetalSynth`, `NoiseSynth`, `PluckSynth` |
| Samples | `new Tone.Sampler({ urls: { C4: 'C4.wav' }, baseUrl: './samples/' })` + `await Tone.loaded()`; `Player`, `Players`, `GrainPlayer` |
| Effects | `Reverb`, `FeedbackDelay`, `PingPongDelay`, `Chorus`, `Phaser`, `Tremolo`, `Vibrato`, `Distortion`, `BitCrusher`, `Filter`, `AutoFilter`, `Compressor`, `Limiter`, `EQ3` |
| Time | `transport.bpm`, `timeSignature`, `'4n'` / `'8t'` / `'1m'`, `Tone.Time('2m').toSeconds()`, `transport.schedule(cb, time)`, `scheduleRepeat` |
| Patterns | `Part`, `Sequence`, `Loop`, `Pattern(cb, values, 'upDown')` |
| Tempo moves | `transport.bpm.rampTo(60, 4)`, `Signal` automation (`param.linearRampTo`) |
| Analysis | `Meter`, `FFT` (for a visualiser drawn in `render(t)` from a pre-analysed table, not live) |

## Pitfalls

- Nodes created outside the `Offline` callback belong to the real-time context and are silent in the render.
- `Reverb` needs `await reverb.ready`; `Sampler`/`Player` need `await Tone.loaded()` inside the callback.
- Sample files must be CC0/CC BY and credited (TECHNIQUE.md §11); the library's own instrument packs
  (`sh tools/fetch.sh instruments <lib>`) are already cleared and `sampler.py credits()` writes their lines.
- Offline rendering is deterministic except for `Tone.Noise` and random `humanize`; seed by baking a noise sample or
  accept that the music is one fixed take kept in the project.
- Musical time depends on `bpm`; set it before `Part.start(0)` and keep tempo changes explicit.
