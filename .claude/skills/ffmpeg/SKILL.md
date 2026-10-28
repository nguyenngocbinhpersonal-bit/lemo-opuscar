---
name: ffmpeg
description: >-
  FFmpeg and ffprobe recipes for encoding and delivering a code-rendered film: probing, frames to video, muxing and
  two-pass loudnorm (what core/render/mux.sh does), concat, trims, burn-in subtitles, overlays, vertical/padded
  variants, GIF and ProRes exports, audio mixing and ducking, colour-range tags. Use for any encode, convert, cut,
  mux, loudness or format question, or when mux.sh refuses a file.
---

# FFmpeg for Lemo-Opuscar films

FFmpeg (LGPL/GPL, https://github.com/FFmpeg/FFmpeg, docs https://ffmpeg.org/ffmpeg-filters.html) is the system tool
the user installs (TECHNIQUE.md §1). The library already drives it in `core/render/video.mjs` (frames → H.264) and
`core/render/mux.sh` (picture + mix → delivered mp4). Reach for the commands below for everything around that.

## The house finisher first

```sh
sh core/render/mux.sh out/video.mp4 out/mix.wav film.mp4 24 2      # fps, grain (0 for pixel/vector styles)
```

Two-pass `loudnorm` to −14 LUFS / true peak −1.2 dB, film grain, `yuv420p`, `+faststart`, refuses damaged or
truncated audio, pads short audio, cuts long audio at the picture's end, prints the measured loudness.
`LEMO_COLOR=bt709` writes limited-range BT.709 instead of the default full-range output. Do not reimplement it.

## Look before you encode

```sh
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt,color_range,sample_rate,channels -of default=nw=1 in.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4
ffmpeg -hide_banner -i in.mp4 -af ebur128=peak=true -f null -          # I (LUFS), LRA, true peak
ffmpeg -i in.mp4 -ss 12.5 -frames:v 1 -q:v 2 frame.jpg                  # one still (seek before -i is fast, after is exact)
```

## Recipes

| Need | Command |
|---|---|
| Frames → video (what `video.mjs` does) | `ffmpeg -framerate 24 -i out/f_%05d.jpg -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart v.mp4` |
| Lossless-ish master | `ffmpeg -i film.mp4 -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -c:a pcm_s24le master.mov` |
| Join films (same codec/size/fps) | `printf "file 'a.mp4'\nfile 'b.mp4'\n" > list.txt; ffmpeg -f concat -safe 0 -i list.txt -c copy reel.mp4` |
| Trim without re-encode (keyframe accurate) | `ffmpeg -ss 00:00:05 -to 00:00:20 -i in.mp4 -c copy cut.mp4` |
| Trim frame-accurate | `ffmpeg -i in.mp4 -ss 5 -to 20 -c:v libx264 -crf 18 -c:a aac -b:a 256k cut.mp4` |
| Burn subtitles (libass) | `ffmpeg -i film.mp4 -vf "subtitles=film.srt:force_style='FontName=Noto Sans,FontSize=22,Outline=1'" -c:a copy sub.mp4` (Windows path: `subtitles='D\:/path/film.srt'`) |
| Soft subtitles | `ffmpeg -i film.mp4 -i film.srt -c copy -c:s mov_text -metadata:s:s:0 language=vie out.mp4` |
| Vertical from landscape | `ffmpeg -i film.mp4 -vf "scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black" out.mp4` (better: render the page with `--size 1080x1920`) |
| Overlay a logo | `ffmpeg -i film.mp4 -i logo.png -filter_complex "[1]scale=240:-1[l];[0][l]overlay=W-w-48:H-h-48" -c:a copy out.mp4` |
| Fade in/out | `-vf "fade=t=in:d=1,fade=t=out:st=58:d=2" -af "afade=t=in:d=1,afade=t=out:st=58:d=2"` |
| Speed | `-vf "setpts=0.5*PTS" -af "atempo=2"` (atempo 0.5–100; chain for more) |
| GIF | `ffmpeg -i clip.mp4 -vf "fps=12,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" clip.gif` |
| Extract / replace audio | `ffmpeg -i film.mp4 -vn -c:a pcm_s16le mix.wav` · `ffmpeg -i film.mp4 -i new.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest out.mp4` |
| Mix two tracks | `ffmpeg -i voice.wav -i music.wav -filter_complex "[1]volume=0.4[m];[0][m]amix=inputs=2:normalize=0" mix.wav` |
| Duck music under voice | `ffmpeg -i music.wav -i voice.wav -filter_complex "[0][1]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=400[d];[d][1]amix=inputs=2:normalize=0" mix.wav` |
| Loudness, one file | measure with `loudnorm=I=-14:TP=-1.2:LRA=11:print_format=json`, then second pass with `measured_*` and `linear=true` (as in `mux.sh`) |
| Silence detection | `ffmpeg -i take.wav -af silencedetect=n=-40dB:d=0.4 -f null -` |
| Resample / mono | `ffmpeg -i in.wav -ar 48000 -ac 1 out.wav` |
| Colour tags only (no re-encode) | `ffmpeg -i in.mp4 -c copy -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 out.mp4` |
| Frame rate change | `-vf fps=24` (drops/dups) · `-vf minterpolate=fps=24:mi_mode=mci` (interpolates, slow) |

Always `-pix_fmt yuv420p` for H.264 players; `-movflags +faststart` for web; `-shortest` when the audio is longer.

## Pitfalls

- `video.mjs` writes full-range `yuvj420p` tagged bt470bg; mixing it with limited-range footage shifts blacks. Convert
  one side (`scale=in_range=pc:out_range=tv` plus tags), or render everything through `mux.sh` with the same
  `LEMO_COLOR`.
- `-c copy` keeps codec timing: trims land on keyframes, concat needs identical streams. Re-encode when exactness
  matters.
- `-ss` before `-i` is fast and keyframe-snapped; after `-i` it decodes to the exact frame.
- Filters quote paths; on Windows escape the drive colon (`D\:/`) inside filter strings and use forward slashes.
- Grain in the page makes frames incompressible; add it in `mux.sh` (`noise=c0s=2:allf=t`), not in `render(t)`.
- A WAV streamed to stdout has a placeholder length; `mux.sh` tolerates it, other tools may not: write to a file.
- Never overwrite the delivered `<name>.mp4` in place; write `-y` to a new name and swap when checked.
