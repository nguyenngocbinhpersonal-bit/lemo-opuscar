import json, re
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))   # 路径相对 demo/
import os as _o, sys as _s; _s.path.insert(0, next((_d for _d in [_o.environ.get('LIB') or '', _o.getcwd()] + [_o.path.abspath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), *(['..'] * _k))) for _k in range(1, 6)] if _o.path.isfile(_o.path.join(_d, 'core', 'tts', 'whisper_model.py'))), '.') + '/core/tts')
from whisper_model import load_model, BEAM   # the library's faster-whisper loader: large-v3 (WHISPER_MODEL) on the GPU when the free VRAM holds it (float16, else int8_float16), else the CPU; beam 10
m = load_model()
norm = lambda s: re.sub(r'[^一-鿿0-9]', '', s)
for L in json.load(open('script.json')):
    segs, _ = m.transcribe(f"vo/{L['id']}.wav", language='zh', beam_size=BEAM, initial_prompt='以下是普通话的句子。')
    got = ''.join(s.text for s in segs)
    print('OK  ' if norm(got)==norm(L['text']) else 'DIFF', L['id'], norm(L['text']), '→', norm(got))
