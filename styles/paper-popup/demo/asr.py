import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))   # voices/ 相对 demo/
import glob
m = load_model()
for f in sorted(glob.glob("voices/v*.wav")):
    segs, _ = m.transcribe(f, beam_size=BEAM)
    print(f[-7:-4], " ".join(s.text.strip() for s in segs))
