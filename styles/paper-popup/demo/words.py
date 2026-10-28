import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))   # voices/ 相对 demo/
m = load_model()
for v in ['v04', 'v05', 'v07', 'v10', 'v14']:
    segs, _ = m.transcribe(f"voices/{v}.wav", beam_size=BEAM, word_timestamps=True)
    print(v, ' '.join(f"{w.word.strip()}@{w.start:.2f}" for s in segs for w in s.words))
