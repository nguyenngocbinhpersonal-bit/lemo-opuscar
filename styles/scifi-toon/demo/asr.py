"""whisper 校对（改自 core/tts/asr_check.py）：前后补 0.6s 静音再转写（短句不补会被听成 "R U D calf"），
并输出逐词时间戳 voices/words.json（用于打断点剪切与口型检查）。
用法：python asr.py lines.json voices_dir"""
import sys, json, re, os, numpy as np, soundfile as sf, librosa
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
m = load_model()
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower().replace("'", '').replace('-', ' ')).split()
bad, words = 0, {}
for L in json.load(open(sys.argv[1])):
    y, sr = sf.read(os.path.join(sys.argv[2], L['id'] + '.wav'))
    if y.ndim > 1: y = y.mean(1)
    y = librosa.resample(y, orig_sr=sr, target_sr=16000); pad = np.zeros(int(.6 * 16000))
    segs, _ = m.transcribe(np.concatenate([pad, y, pad]).astype(np.float32), beam_size=BEAM, language='en', word_timestamps=True)
    segs = list(segs); got = ' '.join(s.text.strip() for s in segs)
    words[L['id']] = [(w.word.strip(), round(w.start - .6, 3), round(w.end - .6, 3)) for s in segs for w in s.words]
    want = L.get('asr', L['text']); ok = norm(got) == norm(want); bad += not ok
    print(('OK  ' if ok else 'DIFF'), L['id'], '|', want, '→', got)
json.dump(words, open(os.path.join(sys.argv[2], 'words.json'), 'w'), indent=0)
print('mismatches:', bad)
