import os
"""试多个说法/声线，whisper 回听，挑能被听对的：python vo_try.py"""
import sys, json, re, numpy as np, soundfile as sf, librosa
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
from kokoro_onnx import Kokoro
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
C = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')), 'core', 'tts', '')
k = Kokoro(C + 'kokoro-v1.0.onnx', C + 'voices-v1.0.bin')
ms = [load_model(n) for n in sys.argv[2:] or [None]]
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower().replace("'", '')).split()
for text, want, sp, *lg in json.load(open(sys.argv[1])):
    a, sr = k.create(text, voice=(lg[1] if len(lg)>1 else 'af_heart'), speed=sp, lang=(lg[0] if lg else 'en-us'))
    thr = np.abs(a).max() * .02; nz = np.where(np.abs(a) > thr)[0]; a = a[max(0, nz[0]-720): nz[-1]+1900]
    y = librosa.resample(a, orig_sr=sr, target_sr=16000); pad = np.zeros(9600)
    res = []
    for m in ms:
        segs, _ = m.transcribe(np.concatenate([pad, y, pad]).astype(np.float32), beam_size=BEAM, language='en')
        got = ' '.join(s.text.strip() for s in segs); res.append(('OK' if norm(got) == norm(want) else '--') + ' ' + got)
    print(f'{len(a)/sr:.2f}s | {text} || ' + ' || '.join(res))
