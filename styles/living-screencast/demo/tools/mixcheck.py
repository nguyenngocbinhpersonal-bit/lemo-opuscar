"""整片混音的 whisper 回听：人声在音乐音效下是否仍听得清（逐词匹配率）"""
import sys, json, re, difflib, numpy as np, soundfile as sf, librosa, os
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
y, sr = sf.read(os.path.join(H, 'mix.wav')); y = librosa.resample(y.mean(1), orig_sr=sr, target_sr=16000).astype(np.float32)
m = load_model(os.environ.get('WM'))
segs, _ = m.transcribe(y, beam_size=BEAM, language='en')
got = ' '.join(s.text for s in segs)
norm = lambda s: re.sub(r'[^a-z0-9 ]', ' ', s.lower().replace("'", '')).split()
want = ' '.join(L.get('asr', L['text']) for L in json.load(open(os.path.join(H, 'lines.json'))))
a, b = norm(want), norm(got); sm = difflib.SequenceMatcher(a=a, b=b)
print(got); print('match %.1f%%' % (100 * sum(x.size for x in sm.get_matching_blocks()) / len(a)))
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op != 'equal': print(op, a[i1:i2], '→', b[j1:j2])
