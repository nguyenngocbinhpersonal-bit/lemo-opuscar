"""单词命令：Kokoro 念单个词结尾会带一个元音尾巴（Pump → "Pompey"）。
做法：生成 "Pump, now!"，按 whisper 词时间戳只留第一个词，末尾 40ms 淡出。python trim_cmd.py lines.json voices"""
import sys, json, os, numpy as np, soundfile as sf
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
import librosa
m = load_model()
L = json.load(open(sys.argv[1])); vd = sys.argv[2]; dur = json.load(open(os.path.join(vd, 'dur.json')))
for x in L:
    if 'trim' not in x: continue
    f = os.path.join(vd, x['id'] + '.wav'); y, sr = sf.read(f)
    y16 = librosa.resample(y, orig_sr=sr, target_sr=16000); pad = np.zeros(int(.6 * 16000))
    segs, _ = m.transcribe(np.concatenate([pad, y16, pad]).astype(np.float32), beam_size=BEAM, language='en', word_timestamps=True)
    ws = [w for s in segs for w in s.words]
    end = ws[0].end - .6 + .03
    # 在词尾后找能量最低点（最多往后 80ms）切
    n = int(end * sr); win = int(.08 * sr); seg = np.abs(y[n:n + win]); cut = n + (int(np.argmin(np.convolve(seg, np.ones(64) / 64, 'same'))) if len(seg) > 64 else 0)
    y = y[:cut].copy(); fo = int(.04 * sr); y[-fo:] *= np.linspace(1, 0, fo)
    sf.write(f, y, sr); dur[x['id']] = round(len(y) / sr, 3); x['asr'] = x['trim']
    print(x['id'], 'trimmed to', dur[x['id']], 's (first word:', ws[0].word, ')')
json.dump(dur, open(os.path.join(vd, 'dur.json'), 'w'), indent=1)
json.dump(L, open(sys.argv[1] + '.asr.json', 'w'), indent=1)
