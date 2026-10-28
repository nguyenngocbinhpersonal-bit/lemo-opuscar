"""成片 whisper 自检：python tools/final_asr.py <成片.mp4>；按 events.json 的旁白时间逐句截取转写并比对"""
import sys, os, json, re, subprocess, numpy as np
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mp4 = sys.argv[1]
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', mp4, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout
y = np.frombuffer(raw, np.float32)
ev = json.load(open(os.path.join(HERE, 'events.json')))['ev']
lines = {L['id']: L for L in json.load(open(os.path.join(HERE, 'lines.json')))}
m = load_model()
def norm(s):   # 口语等价：7am = 7 a.m.，they're = they are
    s = s.lower().replace("they're", 'they are').replace('a.m.', 'am').replace('7am', '7 am').replace("'", '').replace('-', ' ')
    return re.sub(r'[^a-z0-9 ]', '', s).split()
bad = 0
for e in ev:
    if e['type'] != 'vo': continue
    L = lines[e['id']]; a = int(max(0, e['t'] - .3) * 16000); b = int((e['t'] + 4.0) * 16000)
    segs, _ = m.transcribe(y[a:b], beam_size=BEAM, language='en')
    got = ' '.join(s.text.strip() for s in segs); want = L.get('asr', L['text'])
    w, g = norm(want), norm(got); ok = g[:len(w)] == w
    bad += not ok; print('OK  ' if ok else 'DIFF', e['id'], '|', want, '→', got)
print('mismatches:', bad)
