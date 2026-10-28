"""The library's one way to load faster-whisper, at the highest configuration the machine allows.

    sys.path.insert(0, os.path.join(LIB, 'core', 'tts')); from whisper_model import load_model, BEAM
    m = load_model()                       # large-v3 on the GPU (float16), else on the CPU (int8)
    segs, m = transcribe(m, audio, language='en', word_timestamps=True)   # beam_size=BEAM, GPU → CPU fallback

Model: WHISPER_MODEL (a name or a local folder for offline use), else large-v3 for every language. Earlier defaults
      (base.en, small, medium) are still accepted by name when a quick check is enough, but the check scripts default to large-v3.
Device: an NVIDIA GPU when ctranslate2 sees one, else the CPU (int8). On the GPU the compute type follows the free VRAM that nvidia-smi
      reports: float16 when the weights plus ≈ 1.2 GB of working memory fit (large-v3 ≈ 4.2 GB), else int8_float16 (the weights in
      int8, the maths in float16, ≈ 2.7 GB for large-v3: the same words come back, a hair less confident), else the CPU. Never trust
      a load that "succeeds" without the room: on Windows CUDA spills into shared system memory and a line then takes a minute. WHISPER_DEVICE=cpu forces the CPU, =cuda insists on
      the GPU. WHISPER_COMPUTE pins one compute type (float16 | int8_float16 | int8 | float32). On Windows the GPU needs cuBLAS:
      pip install nvidia-cublas-cu12 (its DLL folder is put on PATH here); if the GPU fails on the first transcription (out of memory,
      missing DLL), the model is reloaded on the CPU once and the work goes on, with a note on stderr.
Decoding: beam_size=BEAM (10), one best-of candidate per beam, no VAD cut (every word of a line counts), temperature fallback left
      at faster-whisper's default so a line that will not decode at temperature 0 still comes back.
Download: the first run fetches from Hugging Face (large-v3 ≈ 3 GB); behind a firewall set HF_ENDPOINT=https://hf-mirror.com."""
import os, sys

DEFAULT_MODEL = 'large-v3'
BEAM = 10
TAG = os.path.basename(sys.argv[0]) or 'whisper_model.py'


def default_model(lang=None):
    """WHISPER_MODEL, else large-v3 (multilingual, the most accurate Whisper there is; `lang` is accepted for callers that
    used to pick an English-only model and is ignored)."""
    return os.environ.get('WHISPER_MODEL') or DEFAULT_MODEL


GPU_LADDER = ('float16', 'int8_float16')   # tried in this order on the GPU unless WHISPER_COMPUTE pins one
WORK_MB = 1200                              # VRAM for activations and the beam search on top of the weights (float16 large-v3 still ran out with 3.9 GB free)


def free_vram_mb():
    """Free VRAM of the first GPU in MiB from nvidia-smi, or None when it cannot be asked."""
    try:
        import subprocess
        out = subprocess.run(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=10).stdout
        return int(out.strip().splitlines()[0])
    except Exception: return None


def weights_mb(name):
    """Size of the model's model.bin in MiB (the Hugging Face copy is fetched first if needed), or None."""
    try:
        d = name if os.path.isdir(name) else __import__('faster_whisper.utils', fromlist=['download_model']).download_model(name)
        return os.path.getsize(os.path.join(d, 'model.bin')) / 2**20
    except Exception: return None


def gpu_ladder(name):
    """The compute types to try on the GPU for `name`, from the free VRAM: float16 needs the weights (stored in float16) + WORK_MB,
    int8_float16 half the weights + WORK_MB; an empty list means the CPU. Unknown sizes fall back to trying every type."""
    free, w = free_vram_mb(), weights_mb(name)
    if free is None or w is None: return list(GPU_LADDER)
    fits = [ct for ct, need in (('float16', w + WORK_MB), ('int8_float16', w / 2 + WORK_MB)) if free >= need]
    if not fits: print(f"{TAG}: {free} MiB of VRAM free, '{name}' needs {int(w / 2 + WORK_MB)} even in int8_float16: using the CPU", file=sys.stderr)
    return fits


def whisper_device():
    """('cuda', 'float16') when an NVIDIA GPU is usable, else ('cpu', 'int8'). WHISPER_DEVICE=auto (default) | cuda | cpu;
    WHISPER_COMPUTE pins the compute type. On Windows ctranslate2 loads cuBLAS by name (cublas64_12.dll): the pip wheel
    nvidia-cublas-cu12 puts it in site-packages/nvidia/cublas/bin, which is added to PATH here. Callers still fall back to the
    CPU if the GPU fails on the first transcription (a missing library only shows then), see transcribe()."""
    want = os.environ.get('WHISPER_DEVICE', 'auto').lower()
    compute = os.environ.get('WHISPER_COMPUTE')
    if want == 'cpu': return 'cpu', compute or 'int8'
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() < 1: raise RuntimeError('no CUDA device')
        for sp in sys.path:
            d = os.path.join(sp, 'nvidia', 'cublas', 'bin')
            if os.path.isdir(d):
                os.environ['PATH'] = d + os.pathsep + os.environ.get('PATH', '')
                if hasattr(os, 'add_dll_directory'): os.add_dll_directory(d)
                break
        return 'cuda', compute or 'float16'
    except Exception as e:
        if want == 'cuda': sys.exit(f'{TAG}: WHISPER_DEVICE=cuda but CUDA is not usable ({type(e).__name__}: {e})')
        return 'cpu', compute or 'int8'


def load_model(name=None):
    """A faster_whisper.WhisperModel for `name` (default: default_model()). Exits with code 2 when it cannot load at all."""
    name = name or default_model()
    try: from faster_whisper import WhisperModel
    except ImportError: sys.exit(f'{TAG}: faster-whisper is missing: install the voice tier: sh plugin/skills/lemo-opuscar/scripts/setup.sh deps voice')
    device, compute = whisper_device()
    ladder = [compute] if device == 'cpu' or os.environ.get('WHISPER_COMPUTE') else gpu_ladder(name)
    if not ladder: os.environ['WHISPER_DEVICE'] = 'cpu'; return load_model(name)
    err = None
    for i, ct in enumerate(ladder):
        try:
            m = WhisperModel(name, device=device, compute_type=ct)
            m.lemo_name = name
            if device == 'cuda' and ct != 'float16': print(f"{TAG}: '{name}' loaded on the GPU in {ct} (float16 does not fit in the free VRAM)", file=sys.stderr)
            return m
        except Exception as e:
            err = e
            if device == 'cuda' and i + 1 < len(ladder):
                print(f"{TAG}: cannot load '{name}' on the GPU in {ct} ({type(e).__name__}: {str(e)[:100]}): trying {ladder[i + 1]}", file=sys.stderr); continue
            if device == 'cuda':
                print(f"{TAG}: cannot load '{name}' on the GPU ({type(e).__name__}: {str(e)[:120]}): using the CPU", file=sys.stderr)
                os.environ['WHISPER_DEVICE'] = 'cpu'; return load_model(name)
    print(f"{TAG}: cannot load the whisper model '{name}'.\n  {type(err).__name__}: {str(err)[:300]}", file=sys.stderr)
    if not os.path.isdir(name):
        print("  The model is downloaded from huggingface.co on first use. If that site is blocked or you are offline:\n"
              "    set HF_ENDPOINT=https://hf-mirror.com (a mirror), or download the model once and pass --model /path/to/model-dir", file=sys.stderr)
    sys.exit(2)


def transcribe(m, audio, **kw):
    """m.transcribe(audio, beam_size=BEAM, **kw) as a list of segments. If the model runs on the GPU and fails (cuBLAS / cuDNN
    missing, out of memory), it is reloaded on the CPU once and the audio is transcribed again; returns (segments, model)."""
    kw.setdefault('beam_size', BEAM)
    try: return list(m.transcribe(audio, **kw)[0]), m
    except Exception as e:
        if getattr(m.model, 'device', 'cpu') != 'cuda': raise
        print(f'{TAG}: the GPU failed ({type(e).__name__}: {str(e)[:120]}): continuing on the CPU (pip install nvidia-cublas-cu12 gives ctranslate2 its cuBLAS)', file=sys.stderr)
        os.environ['WHISPER_DEVICE'] = 'cpu'; m = load_model(getattr(m, 'lemo_name', None))
        return list(m.transcribe(audio, **kw)[0]), m


def device_of(m):
    return getattr(m.model, 'device', 'cpu')
