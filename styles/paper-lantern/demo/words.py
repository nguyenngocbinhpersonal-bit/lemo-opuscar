import json, sys
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))   # 路径相对 demo/
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
m = load_model()
out = {}
for lid in sys.argv[1:]:
    segs, _ = m.transcribe(f"vo/{lid}.wav", beam_size=BEAM, language='zh', word_timestamps=True, initial_prompt='以下是普通话的句子。')
    out[lid] = [(w.word, round(w.start, 2), round(w.end, 2)) for s in segs for w in s.words]
    print(lid, out[lid])
json.dump(out, open('vo/words.json', 'w'), ensure_ascii=False, indent=0)
