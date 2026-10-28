# Video & Podcasts

Subtitles and transcripts for YouTube, Bilibili, and Xiaoyuzhou Podcast.

## YouTube (yt-dlp)

### Get video metadata

```bash
yt-dlp --dump-json "URL"
```

### Download subtitles

```bash
# Download subtitles (without downloading the video)
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --skip-download -o "/tmp/%(id)s" "URL"

# Then read the .vtt file
cat /tmp/VIDEO_ID.*.vtt
```

### Get comments

```bash
# Extract comments (best-effort, not guaranteed complete)
yt-dlp --write-comments --skip-download --write-info-json \
  --extractor-args "youtube:max_comments=20" \
  -o "/tmp/%(id)s" "URL"
# Comments are in the comments field of the .info.json
```

### Search videos

```bash
yt-dlp --dump-json "ytsearch5:query"
```

> **Subtitle note**: manually-uploaded subtitles extract reliably; auto-generated subtitles may have duplicate lines that need post-processing.
> **Comments note**: `--write-comments` is based on web scraping (not the YouTube Data API); some comments may be missing.

### Retry chain when subtitle fetch fails (run in order, stop once you get real content)

`doctor` only confirms yt-dlp itself and the JS runtime can execute — it does not request a specific video; therefore
`active_backend: yt-dlp` does not mean the target video's subtitles have already been verified live.

1. First use the `yt-dlp --write-sub --write-auto-sub` command above.
2. If a bot check appears, the subtitle response is empty, or no subtitle file is generated, and OpenCLI is connected:
   `opencli youtube transcript "URL" -f yaml`.
3. If OpenCLI returns `Caption URL returned empty response`, retry up to 3 times; this is an occasional failure of the
   time-limited subtitle URL, not proof "the video has no subtitles."
4. If it still fails, or the video genuinely has no subtitles: `agent-reach transcribe "URL"` to download the audio and transcribe it.

Success means actually getting non-empty subtitle/transcript content — not the command's exit code or `doctor`'s version probe result.

### Fallback with no subtitles: Whisper audio transcription

```bash
# Fallback when a video has no subtitles: download audio and transcribe with Whisper (a free Groq key works)
agent-reach transcribe "https://www.youtube.com/watch?v=VIDEO_ID"
agent-reach transcribe ./local_audio.mp3 -o /tmp/transcript.txt
```

> `agent-reach transcribe` only accepts a public http(s) URL or a local audio file. When using `ytsearch5:` search, first pick a specific video URL from the yt-dlp results, then transcribe it.
> You need to configure a key first: `agent-reach configure groq-key` (hidden input; free, console.groq.com)
> or `agent-reach configure openai-key`. The default auto mode only uses the first configured provider
> (Groq preferred, otherwise OpenAI); on failure it stops rather than automatically sending the audio to the other provider.
> `--allow-provider-fallback` explicitly authorizes cross-provider fallback; the same audio content may be processed by
> both Groq and OpenAI separately and may incur OpenAI charges — only use this once you've confirmed the content can be shared with both.

## Bilibili (bili-cli primary, OpenCLI for subtitles)

> ⚠️ **Don't use yt-dlp for Bilibili**: Bilibili's anti-bot measures now block yt-dlp entirely with 412 (confirmed with no workaround). yt-dlp is for YouTube only.

### Video details/search/trending/rankings (bili-cli, read-only, no login required)

```bash
# Video details (title/uploader/duration/view-interaction stats/subtitle availability)
bili video BVxxx

# Search videos
bili search "query" --type video -n 5

# Trending videos / rankings
bili hot -n 10
bili rank -n 10

# Download audio and split into ASR-ready WAV (pair with agent-reach transcribe when no subtitles exist)
bili audio BVxxx
```

### Subtitles (OpenCLI, requires desktop Chrome)

```bash
# Subtitles with per-line timestamps
opencli bilibili subtitle BVxxx

# OpenCLI can also search/read video metadata (fallback)
opencli bilibili search "query" -f yaml
opencli bilibili video BVxxx -f yaml
```

### Zero-config fallback: direct search API

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
curl -s -c /tmp/bili_ck.txt -o /dev/null -A "$UA" "https://www.bilibili.com/"
curl -s -b /tmp/bili_ck.txt -A "$UA" -e "https://www.bilibili.com/" \
  "https://api.bilibili.com/x/web-interface/search/all/v2?keyword=QUERY&page=1"
```

> **Installing bili-cli**: `pipx install 'bilibili-cli==0.6.2'` (upstream stopped updating as of 2026-03 but is confirmed healthy; read-only use requires no login; `bili login` via QR code unlocks personal features like moments/favorites).

## Xiaoyuzhou Podcast

### Transcribe a single podcast episode (optional --polish for better punctuation)

```bash
# Outputs a Markdown file to /tmp/. --polish has Llama 3.3 70B add Chinese punctuation + reasonable paragraphing
~/.agent-reach/tools/xiaoyuzhou/transcribe.sh --polish "https://www.xiaoyuzhoufm.com/episode/EPISODE_ID"
```

> The transcription prompt already asks Whisper to output Chinese punctuation; if punctuation quality is still poor, add `--polish` to use Groq's free Llama 3.3 70B to add punctuation + reasonable paragraphing (adds ~7 seconds for a 9-minute podcast). Each transcription adds one more LLM call, so use as needed.

### Prerequisites

1. **ffmpeg**: `brew install ffmpeg`
2. **Groq API key** (free): https://console.groq.com/keys
3. **Configure the key**: `agent-reach configure groq-key` (hidden input)
4. **First run**: `agent-reach install --env=auto --system --channels=xiaoyuzhou` (requires explicit user authorization)

### Check status

```bash
agent-reach doctor
```

> Output Markdown files are saved to `/tmp/` by default.

## Tool selection guide

| Scenario | Recommended tool |
|-----|---------|
| YouTube subtitles | yt-dlp; on failure, OpenCLI (up to 3 retries) → agent-reach transcribe |
| Bilibili video details/search | bili-cli |
| Bilibili subtitles | opencli bilibili subtitle |
| Podcast transcription | Xiaoyuzhou transcribe.sh |
| Audio/video with no subtitles | agent-reach transcribe (for Bilibili audio, run `bili audio` first) |

## Browser session cleanup

If Bilibili subtitles were fetched via OpenCLI, close its tab lease when done (SKILL.md standing rule 7):
`opencli browser site:bilibili close`
