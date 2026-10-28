"""成片 whisper 自检：从 mp4 抽音轨转写，逐句比对旁白与时间"""
import sys, json, re, subprocess, numpy as np, os
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
H = os.path.dirname(os.path.abspath(__file__)); mp4 = sys.argv[1]
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', mp4, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout
a = np.frombuffer(raw, np.float32)
m = load_model()
segs, _ = m.transcribe(a, beam_size=BEAM, language='en', word_timestamps=True)
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower()).split()
got = [(s.start, s.end, s.text.strip()) for s in segs]
for s in got: print(f'{s[0]:6.2f}-{s[1]:6.2f}  {s[2]}')
allw = ' '.join(norm(' '.join(g[2] for g in got)))
ok = 0
for L in json.load(open(f'{H}/lines.json')):
    w = ' '.join(norm(L['text'])); f = w in allw; ok += f; print('OK ' if f else 'MISS', L['id'], L['text'])
print(f'{ok}/5 lines found')
