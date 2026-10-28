"""Whisper each narration line from the FINAL mp4 audio (single-line checks can pass while the mix masks a word)."""
import sys, os, json, subprocess, numpy as np, soundfile as sf
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); mp4 = sys.argv[1]
wav = os.path.join(D, 'out', 'final16k.wav')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp4, '-ac', '1', '-ar', '16000', wav], check=True)
a, sr = sf.read(wav); lines = json.load(open(os.path.join(D, 'lines.json')))
ev = [e for e in json.load(open(os.path.join(D, 'events.json')))['ev'] if e['type'] == 'voice']
m = load_model()
import re; norm = lambda s: re.sub(r'[^a-z ]', '', s.lower().replace('knight', 'night')).split()
bad = 0
for e in ev:
    L = next(l for l in lines if l['id'] == e['id']); dur = sf.info(os.path.join(D, 'voices', e['id'] + '.wav')).duration
    seg = a[int((e['t'] - .25) * sr): int((e['t'] + dur + .15) * sr)]
    txt = ' '.join(s.text for s in m.transcribe(seg.astype(np.float32), language='en', beam_size=BEAM)[0]).strip()
    ok = norm(txt) == norm(L['text']); bad += not ok
    print('OK  ' if ok else 'DIFF', e['id'], '|', txt)
print('final mismatches:', bad)
