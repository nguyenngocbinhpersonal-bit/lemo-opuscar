---
name: obs-studio
description: >-
  OBS Studio for screen, window and camera capture around a code-rendered film: recording settings that cut cleanly
  (mkv/fragmented mp4, CRF, fixed fps, 48 kHz), command-line start flags, obs-websocket 5 automation with
  obs-websocket-js (scenes, StartRecord/StopRecord), and remuxing to mp4 with ffmpeg. Use when the user needs real
  screen footage (a demo, a screencast reference, a tutorial of the agent working), a webcam insert, or asks about OBS.
---

# OBS Studio around a Lemo-Opuscar film

OBS Studio (GPL-2.0, https://github.com/obsproject/obs-studio, 33.0.0 when this was written) records and streams
screens, windows, cameras and audio. The films in this library are rendered headless from code, so OBS is never in the
render path. It has three jobs here:

1. **Real footage the film quotes**: a true screen recording for a Living Screencast style film, a webcam clip, a
   reference of how an app behaves. It then counts as the user's own material (brief question 2, DIRECTOR.md §1).
2. **A tutorial or behind-the-scenes recording** of the agent producing a film.
3. **Capturing a prototype** that only exists as an interactive page.

The user installs OBS (`winget install OBSProject.OBSStudio`, `brew install --cask obs`, distro packages). Never
install system software yourself; never kill a running OBS (it is the user's process).

## Settings that cut cleanly

| Setting | Value | Why |
|---|---|---|
| Output → Recording → Format | `mkv`, or `fragmented mp4` | survives a crash; remux to mp4 after |
| Encoder / rate control | x264 or NVENC, `CQP`/`CRF` 16–18 | edit-grade quality, no bitrate starvation |
| Video → Base and output resolution | the film's size (1920×1080 or 1080×1920) | no rescale later |
| FPS | the film's fps (24, 25 or 30), constant | mixed frame rates stutter after `mux.sh` |
| Colour | sRGB, Rec. 709, limited | default; matches `LEMO_COLOR=bt709` output |
| Audio | 48 kHz, separate tracks for mic and desktop | the mix can duck or drop each |
| Scene | a `Window Capture` of the one window, cursor on only if the film shows it | no desktop clutter |

Remux after recording:

```sh
ffmpeg -i rec.mkv -c copy rec.mp4
```

## Command line

```sh
obs --startrecording --minimize-to-tray --profile "Film" --collection "Film" --scene "Capture"
obs --startvirtualcam          # expose a scene as a webcam for a browser page
obs --safe-mode                # no plugins, when something misbehaves
```

Other flags: `--startstreaming`, `--startreplaybuffer`, `--studio-mode`, `--portable`, `--multi` (second instance),
`--always-on-top`, `--verbose`, `--disable-updater`, `--disable-shutdown-check`. On Windows the executable is
`C:\Program Files\obs-studio\bin\64bit\obs64.exe` and must be started from its own folder (`cd` there first, or use
the Start Menu shortcut's working directory). On macOS: `open -a OBS --args --startrecording`.

## Automation with obs-websocket 5

Built in since OBS 28: Tools → WebSocket Server Settings (port 4455, set a password). Client:

```sh
npm i --no-audit --no-fund obs-websocket-js@5.0.8
```

```js
import OBSWebSocket from 'obs-websocket-js';
const obs = new OBSWebSocket();
await obs.connect('ws://127.0.0.1:4455', process.env.OBS_PASSWORD);
await obs.call('SetCurrentProgramScene', { sceneName: 'Capture' });
await obs.call('StartRecord');
// drive the page / app here, with the same timings each take
const { outputPath } = await obs.call('StopRecord');       // the mkv/mp4 OBS wrote
await obs.disconnect();
```

Requests follow the obs-websocket protocol names (`GetSceneList`, `SetSceneItemEnabled`, `SetInputMute`,
`SaveSourceScreenshot`, `TriggerHotkeyByName`); events arrive on `obs.on('RecordStateChanged', …)`. Keep the
password out of the repo (environment variable or the user's keychain).

## Pitfalls

- A recording from a 60 Hz desktop into a 24 fps film needs a deliberate conversion (`fps=24` in ffmpeg, or ask for
  24/48 fps capture). Do not let `mux.sh` drop frames arbitrarily.
- Desktop audio captured with the recording carries system sounds; record it to its own track or mute it.
- Window capture of a browser with hardware acceleration can show black on some GPUs; `Display Capture` or the
  browser's own flag `--disable-gpu` for the capture session fixes it.
- Leave no OBS instance running when the job is done, as with any background process the agent started.
