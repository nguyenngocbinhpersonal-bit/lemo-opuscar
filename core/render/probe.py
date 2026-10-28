"""Checks a finished film, or material the user brings, with ffprobe, before anyone watches it.

Film mode:  python core/render/probe.py film.mp4 [--fps 24] [--size 1920x1080] [--dur SECONDS] [--like video.mp4] [--color full|bt709]
  Every check prints OK or FAIL on one line; exit 0 when all pass, 1 when any fails, 2 when ffprobe cannot read the file.
  - one H.264 video stream and one AAC audio stream, nothing else
  - --size WxH (default 1920x1080) and --fps (default 24) match the stream; frames = round(duration × fps) ± 1
    (--like takes size and frame count from the frame video that mux.sh was given, so a dropped frame shows)
  - 4:2:0 pixels (yuvj420p full range by default, yuv420p with LEMO_COLOR=bt709); colour tags: --color full (default, what
    mux.sh writes) is range pc, --color bt709 wants range tv + bt709 matrix/primaries/transfer (LEMO_COLOR=bt709)
  - audio 48 kHz, 1 or 2 channels; audio and video lengths within 0.1 s; --dur within 0.05 s of window.DUR when given
  - moov atom before mdat (faststart), so the film starts playing while it still downloads
Material mode:  python core/render/probe.py --material take.wav music.mp3 clip.mov …
  Prints what each file is (container, codec, sample rate, channels, size, fps, length) and warns about what the
  pipeline handles badly: variable frame rate, a sample rate under 44.1 kHz, more than 2 channels, a missing audio
  or video stream, a container length that disagrees with the decoded length (a truncated file). Exit 1 on any warning.
"""
import sys, os, json, subprocess, argparse, shutil
from fractions import Fraction

TAG = 'probe.py'


def ffprobe(path, *extra):
    if not shutil.which('ffprobe'): sys.exit(f'{TAG}: ffprobe is not installed (it comes with ffmpeg)')
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', *extra, '-of', 'json', path], capture_output=True, text=True)
    if r.returncode or not r.stdout.strip():
        print(f"{TAG}: ffprobe cannot read '{path}': {r.stderr.strip()[:300]}", file=sys.stderr); sys.exit(2)
    return json.loads(r.stdout)


def rate(s):
    try: return float(Fraction(s))
    except (ValueError, ZeroDivisionError): return 0.0


def faststart(path):
    """True when the moov atom comes before mdat in the top-level boxes of an MP4."""
    with open(path, 'rb') as f:
        off, size, seen = 0, os.path.getsize(path), []
        while off + 8 <= size and len(seen) < 16:
            f.seek(off); hdr = f.read(16)
            n = int.from_bytes(hdr[:4], 'big'); kind = hdr[4:8]
            if n == 1: n = int.from_bytes(hdr[8:16], 'big')
            elif n == 0: n = size - off
            seen.append(kind)
            if kind in (b'moov', b'mdat') and {b'moov', b'mdat'} <= set(seen): break
            off += max(n, 8)
    return b'moov' in seen and (b'mdat' not in seen or seen.index(b'moov') < seen.index(b'mdat'))


def film(a):
    p = ffprobe(a.film, '-count_packets')
    vs = [s for s in p['streams'] if s['codec_type'] == 'video']; au = [s for s in p['streams'] if s['codec_type'] == 'audio']
    bad = 0
    def chk(ok, what, got=''):
        nonlocal bad; bad += not ok; print(('OK  ' if ok else 'FAIL'), what, ('' if ok else f'  ← {got}'))
    chk(len(vs) == 1 and len(au) == 1 and len(p['streams']) == 2, 'one video + one audio stream', f'{len(vs)} video, {len(au)} audio, {len(p["streams"])} in all')
    if not vs or not au: sys.exit(1)
    v, s = vs[0], au[0]
    W, H = a.size; frames_want = None
    if a.like:
        q = ffprobe(a.like, '-count_packets'); lv = next(x for x in q['streams'] if x['codec_type'] == 'video')
        W, H = int(lv['width']), int(lv['height']); frames_want = int(lv.get('nb_read_packets') or lv.get('nb_frames') or 0) or None
    chk(v['codec_name'] == 'h264', 'video H.264', v['codec_name'])
    chk(int(v['width']) == W and int(v['height']) == H, f'size {W}x{H}', f"{v['width']}x{v['height']}")
    fps = rate(v.get('r_frame_rate', '0')); avg = rate(v.get('avg_frame_rate', '0'))
    chk(abs(fps - a.fps) < 1e-3 and abs(avg - a.fps) < 0.01, f'{a.fps:g} fps, constant', f'r_frame_rate {fps:g}, average {avg:g}')
    vd = float(v.get('duration') or p['format'].get('duration') or 0); ad = float(s.get('duration') or vd)
    n = int(v.get('nb_read_packets') or v.get('nb_frames') or 0)
    want = frames_want or round(vd * a.fps)
    chk(abs(n - want) <= 1, f'{want} frames' + (' (as the frame video)' if frames_want else ' (= duration × fps)'), f'{n} frames in the file')
    tags = (v.get('color_range', '?'), v.get('color_space', '?'), v.get('color_primaries', '?'), v.get('color_transfer', '?'))
    if a.color == 'bt709':
        chk(v.get('pix_fmt') == 'yuv420p', 'pixel format yuv420p', v.get('pix_fmt'))
        chk(tags == ('tv', 'bt709', 'bt709', 'bt709'), 'colour tags tv / bt709', ' '.join(tags))
    else:
        chk(v.get('pix_fmt') in ('yuv420p', 'yuvj420p'), 'pixel format 4:2:0', v.get('pix_fmt'))
        chk(v.get('color_range') == 'pc', 'colour range full (pc), the default output', ' '.join(tags))
    chk(s['codec_name'] == 'aac', 'audio AAC', s['codec_name'])
    chk(int(s.get('sample_rate', 0)) == 48000, 'audio 48 kHz', s.get('sample_rate'))
    chk(int(s.get('channels', 0)) in (1, 2), 'audio 1 or 2 channels', s.get('channels'))
    chk(abs(vd - ad) <= 0.1, f'audio and video the same length ({vd:.2f} s)', f'video {vd:.2f} s, audio {ad:.2f} s')
    if a.dur is not None: chk(abs(vd - a.dur) <= 0.05, f'length {a.dur:g} s (window.DUR)', f'{vd:.3f} s')
    chk(faststart(a.film), 'moov before mdat (faststart)', 'mdat first: the film cannot start before it is fully downloaded')
    print(f'{TAG}: {a.film}: {"all checks pass" if not bad else f"{bad} check(s) failed"}')
    sys.exit(1 if bad else 0)


def material(paths):
    warn = 0
    for path in paths:
        p = ffprobe(path); f = p['format']; vs = [s for s in p['streams'] if s['codec_type'] == 'video' and s.get('disposition', {}).get('attached_pic', 0) == 0]
        au = [s for s in p['streams'] if s['codec_type'] == 'audio']; notes = []
        parts = [f"{f.get('format_name', '?').split(',')[0]}", f"{float(f.get('duration') or 0):.2f} s"]
        for s in au[:1]:
            parts.append(f"audio {s['codec_name']} {s.get('sample_rate', '?')} Hz {s.get('channels', '?')} ch")
            if int(s.get('sample_rate', 0)) < 22050: notes.append(f"sample rate {s.get('sample_rate')} Hz is below 22.05 kHz (telephone quality): it will sound dull next to the other voices")
            if int(s.get('channels', 0)) > 2: notes.append(f"{s.get('channels')} channels: downmix to stereo first")
        for s in vs[:1]:
            fps, avg = rate(s.get('r_frame_rate', '0')), rate(s.get('avg_frame_rate', '0'))
            parts.append(f"video {s['codec_name']} {s['width']}x{s['height']} {avg:g} fps {s.get('pix_fmt', '')}")
            if abs(fps - avg) > 0.05: notes.append(f"variable frame rate ({avg:g} average, {fps:g} timebase): convert with ffmpeg -vsync cfr -r <fps> before cutting")
            if s.get('pix_fmt', '').startswith('yuv4') and s['pix_fmt'] not in ('yuv420p', 'yuvj420p'): notes.append(f"pixel format {s['pix_fmt']}: fine as a source, mux.sh converts it")
        if not au and not vs: notes.append('no audio or video stream at all')
        # a container length far from what decodes = a truncated or damaged file
        r = subprocess.run(['ffmpeg', '-v', 'error', '-nostats', '-progress', 'pipe:1', '-i', path, '-f', 'null', '-'], capture_output=True, text=True)
        dec = [l.split('=')[1] for l in r.stdout.splitlines() if l.startswith('out_time_us=') or l.startswith('out_time_ms=')]
        if dec and float(f.get('duration') or 0) > 0:
            got = int(dec[-1]) / 1e6
            if got < float(f['duration']) - 0.5: notes.append(f"only {got:.2f} s decode of the {float(f['duration']):.2f} s the container claims: the file is truncated or damaged")
        if r.stderr.strip(): notes.append(f"ffmpeg reported while decoding: {r.stderr.strip().splitlines()[0][:120]}")
        print(f"{path}: " + ', '.join(parts))
        for n in notes: print(f'  warning: {n}'); warn += 1
    sys.exit(1 if warn else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('film', nargs='?'); ap.add_argument('--material', nargs='+', metavar='FILE')
    ap.add_argument('--fps', type=float, default=24); ap.add_argument('--size', default='1920x1080'); ap.add_argument('--dur', type=float)
    ap.add_argument('--like', help='the frame video given to mux.sh: its size and frame count are the expectation')
    ap.add_argument('--color', choices=['full', 'bt709'], default='bt709' if os.environ.get('LEMO_COLOR') == 'bt709' else 'full')
    a = ap.parse_args()
    if a.material: material(a.material)
    if not a.film: ap.error('a film to check, or --material FILE …')
    try: a.size = tuple(int(x) for x in a.size.lower().split('x'))
    except ValueError: ap.error('--size must be WxH')
    if not os.path.isfile(a.film): sys.exit(f"{TAG}: not found: {a.film}")
    film(a)


if __name__ == '__main__':
    main()
