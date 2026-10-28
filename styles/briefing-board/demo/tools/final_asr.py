#!/usr/bin/env python3
"""Speech check on the FINAL mix (music, foley and all): transcribe the film with faster-whisper and
compare with the script, line by line (word match after normalising numbers and punctuation).
    $LIB/.venv/bin/python tools/final_asr.py <film.mp4> [--model base.en]"""
import json, os, re, subprocess, sys, tempfile, difflib
DEMO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
film = sys.argv[1]; model = sys.argv[sys.argv.index('--model') + 1] if '--model' in sys.argv else 'base.en'
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
tmp = tempfile.mktemp(suffix='.wav'); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', film, '-ac', '1', '-ar', '16000', tmp], check=True)
segs, _ = load_model(model).transcribe(tmp, word_timestamps=True, beam_size=BEAM, language='en'); os.remove(tmp)
words = [(w.start, w.word) for s in segs for w in s.words]
norm = lambda t: re.sub(r'[^a-z0-9 ]', ' ', re.sub(r'(\d)\s*,\s*(\d)', r'\1\2', t.lower()).replace(',', '')).split()   # '1 ,208' and '1,208' are 1208
lines = {l['id']: l for l in json.load(open(os.path.join(DEMO, 'audio', 'lines.json')))}
ev = {e['id']: e['t'] for e in json.load(open(os.path.join(DEMO, 'scenes', 'film.json')))['ev'] if e['type'] == 'vo'}
dur = json.load(open(os.path.join(DEMO, 'audio', 'vo', 'dur.json')))
bad = 0
for k, l in lines.items():
    t0, t1 = max(0, ev[k] - .6), ev[k] + dur[k] + .3
    heard = ' '.join(w for t, w in words if t0 <= t <= t1)
    want = l.get('asr') or l['text']
    r = difflib.SequenceMatcher(None, norm(want), norm(heard)).ratio()
    ok = r >= .85; bad += not ok
    print(f"{'OK ' if ok else 'BAD'} {k} {r:.2f} | {want} → {heard.strip()}")
print('final mix speech check:', 'OK' if not bad else f'{bad} lines below 0.85')
sys.exit(1 if bad else 0)
