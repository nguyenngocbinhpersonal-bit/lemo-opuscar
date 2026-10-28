"""成片 whisper 抽查：逐句在各自时间窗内单独转写（成片里有配乐和拟音），与期望文本比对。python tools/final_asr.py iso-infographic.mp4"""
import sys, os, json, re, subprocess, numpy as np
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', sys.argv[1], '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout
y = np.frombuffer(raw, np.float32)
m = load_model()
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower().replace("'", '').replace('-', ' ').replace(',', '')).split()
L = json.load(open(os.path.join(D, 'lines.json'))); dur = json.load(open(os.path.join(D, 'voices/dur.json'))); bad = 0
for l in L:
    a, b = max(0, int((l['t'] - .15) * 16000)), int((l['t'] + dur[l['id']] + .25) * 16000)
    seg = np.concatenate([np.zeros(8000, np.float32), y[a:b], np.zeros(8000, np.float32)])
    got = ' '.join(s.text.strip() for s in m.transcribe(seg, language='en', beam_size=BEAM)[0]); want = l.get('asr', l['text'])
    ok = norm(want) == norm(got); bad += not ok; print('OK  ' if ok else 'DIFF', f"{l['t']:6.2f}", want, '→', got)
print('mismatches:', bad)
