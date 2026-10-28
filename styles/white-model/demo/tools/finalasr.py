"""Speech-to-text on the final film (music, foley and all): every narration line must come back verbatim.
usage: python -I tools/finalasr.py <film.mp4> <demo_dir> [model=small.en]"""
import sys, os, json, re, subprocess, tempfile
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
mp4, D = sys.argv[1], sys.argv[2]; model = sys.argv[3] if len(sys.argv) > 3 else None
wav = os.path.join(tempfile.mkdtemp(), 'mix16k.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp4, '-ac', '1', '-ar', '16000', wav], check=True)
segs, _ = load_model(model).transcribe(wav, beam_size=BEAM, language='en', vad_filter=False)
heard = ' '.join(s.text for s in segs)
print('heard:', heard.strip())
norm = lambda s: re.sub(r'[^a-z0-9 ]', ' ', s.lower().replace('centre', 'center').replace('metres', 'meters').replace('nine', '9')).split()
H = norm(heard); bad = 0
for L in json.load(open(os.path.join(D, 'voice/lines.json'))):
    exp = norm(L.get('asr') or L['text'])
    ok = any(H[i:i + len(exp)] == exp for i in range(len(H) - len(exp) + 1)); bad += not ok
    print(('OK   ' if ok else 'MISS ') + ' '.join(exp))
print('all lines heard in the final mix' if not bad else f'{bad} line(s) not heard verbatim')
