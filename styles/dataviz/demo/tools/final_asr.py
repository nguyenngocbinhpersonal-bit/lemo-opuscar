# 成片逐句 whisper：从成片音轨按字幕区间截取每句再转写，对照 lines.json 的 asr/text
import sys, json, os, re, subprocess, numpy as np
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); MP4 = sys.argv[1]
wav = os.path.join(D, 'out', 'final16k.wav')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', MP4, '-ac', '1', '-ar', '16000', wav], check=True)
import soundfile as sf
y, sr = sf.read(wav); m = load_model()
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower().replace("'", '').replace('-', ' ')).split()
dur = json.load(open(os.path.join(D, 'voices/dur.json'))); bad = 0
for L in json.load(open(os.path.join(D, 'lines.json'))):
    a, b = int((L['t'] - .15) * sr), int((L['t'] + dur[L['id']] + .25) * sr)
    segs, _ = m.transcribe(y[a:b].astype(np.float32), beam_size=BEAM, language='en')
    got = ' '.join(s.text.strip() for s in segs); ok = norm(got) == norm(L.get('asr', L['text'])); bad += not ok
    print('OK  ' if ok else 'DIFF', L['id'], '|', got)
print('final mismatches:', bad)
