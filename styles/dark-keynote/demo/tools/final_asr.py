"""成片 whisper 抽查：从 mp4 里按旁白时间切片转写，并算 300–4000 Hz 频段的人声/背景 SNR。
python styles/dark-keynote/demo/tools/final_asr.py styles/dark-keynote/dark-keynote.mp4"""
import sys, os, json, re, subprocess, numpy as np, soundfile as sf, librosa
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
from scipy.signal import butter, sosfilt, resample_poly
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); K = json.load(open(os.path.join(D, 'timeline.json')))['K']
lines = json.load(open(os.path.join(D, 'lines.json'))); dur = json.load(open(os.path.join(D, 'voices/dur.json')))
tmp = os.path.join(D, 'out', 'final_audio.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', sys.argv[1], '-ac', '1', '-ar', '16000', tmp], check=True)
y, sr = sf.read(tmp); m = load_model()
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower()).split()
sos = butter(4, [300, 4000], 'band', fs=sr, output='sos'); ok = 0
mix48, _ = sf.read(os.path.join(D, 'mix.wav'))
for L in lines:
    t0 = K['vo'][L['id']]; a, b = int((t0 - .3) * sr), int((t0 + dur[L['id']] + .3) * sr)
    segs, _ = m.transcribe(y[a:b].astype(np.float32), beam_size=BEAM, language='en')
    got = ' '.join(s.text.strip() for s in segs); good = norm(got) == norm(L['text']); ok += good
    v, vs = sf.read(os.path.join(D, 'voices', L['id'] + '.wav')); v = resample_poly(v, sr, vs)
    seg = y[int(t0 * sr):int(t0 * sr) + len(v)]; vb = sosfilt(sos, v); sb = sosfilt(sos, seg)
    gain = np.dot(sb, vb) / (np.dot(vb, vb) + 1e-12); rest = sb - gain * vb
    snr = 10 * np.log10(np.sum((gain * vb) ** 2) / (np.sum(rest ** 2) + 1e-12))
    print(('OK  ' if good else 'DIFF'), L['id'], f'SNR {snr:+.1f} dB |', L['text'], '→', got)
print(f'{ok}/{len(lines)} OK')
