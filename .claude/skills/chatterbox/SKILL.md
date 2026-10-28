---
name: chatterbox
description: >-
  Chatterbox (Resemble AI) open-source TTS and voice cloning for a film's voice track: Turbo, Nano, Chatterbox and
  Multilingual V3 models, reference-clip cloning, exaggeration and cfg_weight, paralinguistic tags, writing the
  <id>.wav + dur.json that core/tts expects so asr_check.py and the mix work unchanged. Use when the user wants a
  cloned voice, an expressive English or multilingual narrator beyond Kokoro/edge-tts, or names Chatterbox.
---

# Chatterbox for the voice track

Chatterbox (MIT, https://github.com/resemble-ai/chatterbox, PyPI `chatterbox-tts`, 0.1.7 when this was written) is a
0.5B-parameter TTS family with zero-shot voice cloning from a ~10 s reference clip. Models:

| Model | Class | Languages | Notes |
|---|---|---|---|
| Turbo | `chatterbox.tts_turbo.ChatterboxTurboTTS` | English | fastest, needs a reference clip, paralinguistic tags `[chuckle]`, `[sigh]`, `[laugh]` |
| Nano | same class, `nano=True` | English | runs on CPU |
| Chatterbox | `chatterbox.tts.ChatterboxTTS` | English | `exaggeration`, `cfg_weight` controls |
| Multilingual V3 | `chatterbox.mtl_tts.ChatterboxMultilingualTTS`, `t3_model="v3"` | ar da de el en es fi fr he hi it ja ko ms nl no pl pt ru sv sw tr zh | `language_id` per call; Single Language Pack finetunes for zh, es, pt, hi |

**Vietnamese is not in the list.** For Vietnamese keep `core/tts/tts_zh.py` with an edge-tts `vi-VN` voice; for
English and Chinese Chatterbox is an alternative to Kokoro / edge-tts when the user wants a specific or cloned voice.
Every output carries Resemble's PerTh watermark (inaudible); mention it in `CREDITS` as the voice source.

## Install, in a private venv (torch is large; never into `$LIB/.venv`)

```sh
cd films/<name>
python -m venv .venv-tts
.venv-tts/Scripts/pip install -U pip                     # macOS/Linux: .venv-tts/bin/pip
# install the CUDA build of torch first on a GPU machine, per https://pytorch.org/get-started/locally/
.venv-tts/Scripts/pip install chatterbox-tts==0.1.7 soundfile soxr numpy
```

Python 3.10+; the first run downloads the model from Hugging Face (`HF_ENDPOINT` sets a mirror). A GPU is strongly
recommended for anything but Nano.

## A `tts_cb.py` that writes what the pipeline expects

`core/tts/tts.py` writes `voices/<id>.wav` (24 kHz, silence trimmed) and `voices/dur.json` (`{id: seconds}`), and
`core/tts/asr_check.py lines.json voices/` checks them. Keep that contract:

```python
import json, sys, numpy as np, soundfile as sf, soxr, torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS          # or ChatterboxTTS / ChatterboxTurboTTS
lines, out, ref = json.load(open(sys.argv[1], encoding='utf-8')), sys.argv[2], sys.argv[3]   # lines.json out_dir ref.wav
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
model = ChatterboxMultilingualTTS.from_pretrained(device=dev, t3_model='v3')
torch.manual_seed(7)                                                # repeatable takes
dur = {}
for L in lines:
    wav = model.generate(L.get('say', L['text']), audio_prompt_path=ref, language_id=L.get('lang', 'en'),
                         exaggeration=L.get('exaggeration', 0.5), cfg_weight=L.get('cfg_weight', 0.5))
    a = wav.squeeze().cpu().numpy().astype(np.float32)
    if model.sr != 24000: a = soxr.resample(a, model.sr, 24000)
    keep = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, keep[0] - 1200): keep[-1] + 2400] if len(keep) else a   # trim
    sf.write(f'{out}/{L["id"]}.wav', a, 24000); dur[L['id']] = round(len(a) / 24000, 3)
json.dump(dur, open(f'{out}/dur.json', 'w', encoding='utf-8'), indent=1)
```

Then the usual voice check, with `asr` overrides for names and numbers as the line format allows:

```sh
.venv/bin/python core/tts/asr_check.py films/<name>/lines.json films/<name>/voices --lang en
```

## Getting the read right

- One reference clip for the whole film: 8–12 s, clean, mono, the speaker alone, matching the target language
  (a mismatched clip transfers its accent; `cfg_weight=0` reduces that).
- Defaults `exaggeration=0.5, cfg_weight=0.5` suit narration. Dramatic reads: `exaggeration≈0.7, cfg_weight≈0.3`.
  A fast reference speaker: lower `cfg_weight` to ≈0.3. Higher exaggeration speeds speech up.
- Turbo tags go in the text itself (`"…calling you back [chuckle], have you got a minute?"`). Other models read them
  aloud: strip them.
- Long paragraphs drift; one line per sentence or two, as `lines.json` already encourages.
- The voice must be the user's own, a consenting speaker's, or a CC0/CC BY sample; say so in `CREDITS`. Never clone a
  public figure or a voice the user does not have rights to.

## Pitfalls

- `model.generate` returns a torch tensor `(1, n)`; squeeze before writing.
- CPU inference of the 500M models is minutes per line; batch overnight or use Nano for drafts, then regenerate.
- `torch.manual_seed` gives repeatable output on the same machine and version; keep the generated WAVs in the
  project (they are the take), do not plan to regenerate them byte-identically elsewhere.
