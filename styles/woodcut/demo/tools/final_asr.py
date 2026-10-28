"""成片 whisper 自检：逐句在其时间窗内单独转写（成片里有配乐和拟音），和原文比对。python tools/final_asr.py woodcut.mp4"""
import sys, os, json, re, subprocess, numpy as np
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mp4 = sys.argv[1]
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', mp4, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout
y = np.frombuffer(raw, np.float32)
m = load_model()
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower().replace("'", '').replace('-', ' ').replace('five', '5')).split()
K = json.load(open(os.path.join(D, 'timeline.json')))['keys']; L = [dict(l, t=K[l['id']]) for l in json.load(open(os.path.join(D, 'lines.json')))]; dur = json.load(open(os.path.join(D, 'voices/dur.json')))
bad = 0
for l in L:
    if l.get('fx'): continue
    a, b = max(0, int((l['t'] - .15) * 16000)), int((l['t'] + dur[l['id']] + .25) * 16000)
    seg = np.concatenate([np.zeros(8000, np.float32), y[a:b], np.zeros(8000, np.float32)])
    got = ' '.join(s.text.strip() for s in m.transcribe(seg, language='en', beam_size=BEAM)[0])
    want = l.get('trim', l['text'])
    ok = norm(want) == norm(got)[:len(norm(want))] and len(norm(got)) <= len(norm(want)) + 1
    bad += not ok; print('OK  ' if ok else 'DIFF', f"{l['t']:6.2f}", want, '→', got)
print('mismatches:', bad)
