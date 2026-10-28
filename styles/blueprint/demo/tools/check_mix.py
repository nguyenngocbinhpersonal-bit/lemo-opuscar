"""成片旁白可懂度自检：从 mix.wav 按字幕区间切段，whisper 转写对比原文
.venv/bin/python styles/blueprint/demo/tools/check_mix.py"""
import os, json, re, numpy as np, soundfile as sf, librosa
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = load_model()
y, sr = sf.read(os.path.join(HERE, 'mix.wav')); y = y.mean(1)
y = librosa.resample(y, orig_sr=sr, target_sr=16000)
subs = json.load(open(os.path.join(HERE, 'subs.json')))
L = {l['id']: l for l in json.load(open(os.path.join(HERE, 'lines.json')))}
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower().replace("'", '').replace('-', ' ')).split()
bad = 0
for s in subs:
    seg = y[int(max(0, s['t0'] - .2) * 16000): int((s['t1'] + .2) * 16000)].astype(np.float32)
    got = ' '.join(x.text.strip() for x in m.transcribe(seg, beam_size=BEAM, language='en')[0])
    want = L[s['id']].get('asr', L[s['id']]['text']); ok = norm(got) == norm(want); bad += not ok
    print('OK  ' if ok else 'DIFF', s['id'], '|', got)
print('mismatches:', bad)
