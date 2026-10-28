---
name: faster-whisper
description: >-
  faster-whisper (CTranslate2 Whisper) speech-to-text for a film: transcribing a user's voice recording into cues and
  SRT, word timestamps for lip sync and caption timing, model and device choice (GPU float16 / CPU int8), VAD, and how
  core/tts/asr_check.py already wraps it for the voice check. Use when the user brings a recording to transcribe,
  wants subtitles from audio, word-level timing, or names Whisper / faster-whisper.
---

# faster-whisper in a Lemo-Opuscar film

faster-whisper (MIT, https://github.com/SYSTRAN/faster-whisper, 1.2.1 when this was written) runs OpenAI's Whisper
models on CTranslate2, several times faster than the reference implementation with word timestamps and VAD. It is in
the library's voice tier (`sh plugin/skills/lemo-opuscar/scripts/setup.sh deps voice`).

## Already wired in: the voice check

```sh
.venv/bin/python core/tts/asr_check.py lines.json voices/ --lang vi          # large-v3, beam 10, GPU when it fits
```

checks every generated `<id>.wav` against its line, writes `voices/words.json` (word timestamps) and reports
mismatches. Environment: `WHISPER_MODEL` (name or local folder), `WHISPER_DEVICE` (`auto` / `cuda` / `cpu`),
`HF_ENDPOINT` (mirror). On Windows the GPU needs `pip install nvidia-cublas-cu12` (and cuDNN 9 wheels) or it falls
back to the CPU. Whisper mishears tones and names; put the expected spelling in the line's `asr` field instead of
rewriting the script (core/README.md, Audio). The default is `large-v3` for every language; `WHISPER_COMPUTE` pins a compute
type. Load models in your own scripts through `core/tts/whisper_model.py` (`load_model()`, `transcribe()`, `BEAM`) so the
GPU ladder (float16 → int8_float16 → CPU) and the fallbacks apply.

## Transcribing the user's own recording

```python
from faster_whisper import WhisperModel, BatchedInferencePipeline
model = WhisperModel('large-v3', device='cuda', compute_type='float16')    # or load_model() from core/tts/whisper_model.py; CPU: device='cpu', compute_type='int8'
segments, info = model.transcribe('user_take.wav', language='vi', beam_size=BEAM, word_timestamps=True,
                                  vad_filter=True, vad_parameters={'min_silence_duration_ms': 300},
                                  initial_prompt='Tên riêng: Lemo, Opuscar.')      # spelling hints, same language
print(info.language, info.language_probability)
cues = []
for s in segments:                                   # a generator: iterate once, keep what you need
    cues.append({'t0': round(s.start, 3), 't1': round(s.end, 3), 'text': s.text.strip(),
                 'words': [{'t0': w.start, 't1': w.end, 'w': w.word, 'p': w.probability} for w in (s.words or [])]})
```

Batched, for long files on a GPU: `BatchedInferencePipeline(model).transcribe(path, batch_size=16, …)` (same keyword
arguments, VAD on by default).

## From cues to the film

- Subtitles: write `[{t0, t1, text}]` to `cues.json`, then `.venv/bin/python core/render/srt.py cues.json film.srt`
  (TECHNIQUE.md §7). Re-chunk long segments to ≤ 2 lines, ≤ 42 Latin characters a line, ≥ 1 s on screen.
- Lip sync and karaoke captions: `words[].t0/t1` drive the mouth states or the highlight in `render(t)`. Snap to
  frames (`Math.round(t * fps) / fps`) once, in a table built at load.
- Pacing the picture: segment starts and ends become `EV` cues for scene changes and sound.
- Reading the take back as text for the treatment: join `s.text` and quote it, never paraphrase a user's recording.

## Models

| Model | When |
|---|---|
| `large-v3` | **the library default** for every check and language (≈ 3 GB; float16 needs ≈ 4.2 GB of free VRAM, int8_float16 ≈ 2.7 GB) |
| `large-v3-turbo` (`turbo`) | nearly large-v3 accuracy at small-model speed, for long user recordings |
| `medium`, `small`, `base.en` | quick passes only; their mishearings are the model's, not the voice's |
| `distil-large-v3` | English only, fastest large-quality |

Models download to the Hugging Face cache on first use (`HF_ENDPOINT` for a mirror); a local folder from
`ct2-transformers-converter` works as `WhisperModel('/path')`.

## Pitfalls

- `segments` is lazy: nothing runs until you iterate, and it cannot be iterated twice.
- `word_timestamps=True` costs ~20 %; `vad_filter=True` removes hallucinated text in silences.
- Audio in: anything ffmpeg decodes, or a float32 numpy array at 16 kHz (`asr_check.py` pads with silence so the
  first word is not clipped).
- Whisper's language detection on short clips is unreliable: pass `language=` when you know it.
- Never "fix" a script line because Whisper misheard it; fix the `asr` field or regenerate the take.
