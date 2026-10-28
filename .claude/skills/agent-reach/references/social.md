# Social Media & Communities

Xiaohongshu, Twitter/X, Bilibili, V2EX, Reddit, Facebook, Instagram.

## Xiaohongshu (multi-backend)

Xiaohongshu has three backends. **First run `agent-reach doctor --json` to see xiaohongshu's `active_backend`**, then use the matching command group.

### Backend A: OpenCLI (preferred on desktop)

```bash
# Search notes
opencli xiaohongshu search "query" -f yaml

# Read note body + engagement stats (use the full URL from search results, including xsec_token)
opencli xiaohongshu note "NOTE_URL" -f yaml

# Comments (supports nested replies)
opencli xiaohongshu comments NOTE_ID -f yaml

# Homepage recommendation feed
opencli xiaohongshu feed -f yaml

# A user's public notes
opencli xiaohongshu user USER_ID -f yaml
```

> Requires Chrome to be open with the OpenCLI extension installed. OpenCLI only uses a Chrome session
> the user already has and explicitly controls; Agent Reach does not log in on the user's behalf, and does not read browser cookies.
> `agent-reach configure xhs-cookies` does not inject cookies into OpenCLI.
> If no login session already exists, do not auto-login — fall back to backend B/C instead, configured via the
> corresponding manual Cookie-Editor export flow.

### Backend B: xiaohongshu-mcp (server scenarios)

```bash
# Before authenticating, have the user manually export via Cookie-Editor, then import explicitly
agent-reach configure xhs-cookies

# Read-only check of current status
mcporter call xiaohongshu.check_login_status --timeout 120000

# Search
mcporter call xiaohongshu.search_feeds keyword="query" --timeout 120000

# Note detail + comments (feed_id and xsec_token come from search results)
mcporter call xiaohongshu.get_feed_detail feed_id="..." xsec_token="..." --timeout 120000
```

> The first call auto-downloads a ~150MB headless browser, so always pass `--timeout 120000`.
> Authentication is only done via manual Cookie-Editor export; after importing, run `check_login_status` first.
> This explicit command saves/imports the user-provided set of xiaohongshu.com same-domain cookies; the user should
> confirm the scope. Cookies from domains other than xiaohongshu.com are ignored.

### Backend C: xhs-cli (legacy fallback, upstream unmaintained since 2026-03)

```bash
xhs search "query"          # Search
xhs read NOTE_ID_OR_URL     # Read a note (must use the URL/ID from search results, not a bare note_id)
xhs comments NOTE_ID_OR_URL # Comments
xhs hot                     # Trending
xhs feed                    # Recommendations
```

> Known instability: `xhs user` / `xhs user-posts` / `xhs favorites` may return an API error (upstream is unmaintained, no fixes). New users should go straight to backend A/B.

### General notes

> **Auth boundary**: Agent Reach must not log in to Xiaohongshu on the user's behalf, and must not read browser
> cookies. OpenCLI may only use a Chrome session the user already has and explicitly controls;
> xiaohongshu-mcp / legacy tools use a manually Cookie-Editor-exported cookie.
>
> **xsec_token restriction**: Xiaohongshu enforces the xsec_token mechanism — **you cannot read with a bare note_id directly**. Correct flow: search/feed first to get results, then read using the full URL/ID from those results. All three backends work this way.
>
> **Rate limiting**: high-frequency requests (bulk searches, deep comment paging) trigger a CAPTCHA, and the platform's limits cannot be bypassed. Leave 2-3 seconds between operations.
>
> **Write operations (posting/commenting/liking)**: read-only use is recommended. xhs-cli v0.6.x write operations may return 406 due to signature issues.

## Twitter/X (twitter-cli)

### Auth prerequisites

`twitter-cli` reads only `TWITTER_AUTH_TOKEN` / `TWITTER_CT0` from its own process environment; it does
not read the cookie that `agent-reach configure twitter-cookies` saves to `~/.agent-reach/config.yaml`
(`agent-reach doctor` only checks that the pair exists). So **every `twitter ...` command below must be run
through the wrapper**, which reads that config file on each call and injects the pair into the child
process only (no `export`, values redacted from output, existing env vars win if already set):

```bash
python D:\SOFTWARE\LOCAL_APP\YT_WF_001\.claude\skills\agent-reach\scripts\twitter.py <twitter args...>
# e.g.  ...\twitter.py search "ネアンデルタール" --lang ja --since 2026-09-10 --min-likes 100 -n 10 --yaml
```

Wherever a command below says `twitter <args>`, run `python ...\scripts\twitter.py <args>` instead. Exit
code 2 = credentials missing from both env and config (run `agent-reach configure twitter-cookies`);
3 = `twitter-cli` not on PATH. Don't hand-roll env injection and never print the values.

### Stable commands

```bash
# Home timeline (most stable)
twitter feed -n 20

# Read a single tweet (including replies)
twitter tweet URL_OR_ID

# Read a long-form post / X Article
twitter article URL_OR_ID

# User timeline
twitter user-posts @username -n 20

# User profile
twitter user @username
```

### Potentially unstable commands

```bash
# Search tweets (Twitter frequently changes its GraphQL endpoints, may 404)
twitter search "query" -n 10

# Likes (since 2024, only your own likes are visible — a platform limitation)
twitter likes
```

### Retry chain when search fails (run in order, stop on success)

1. Retry directly once (occasional failures are common): `twitter search "query" -n 10`
2. Upgrade and retry: `pipx upgrade twitter-cli && twitter search "query" -n 10`
3. Switch to OpenCLI fallback (desktop, reuses browser login state): `opencli twitter search "query" -f yaml`
4. If none of those work, work around it using stable commands like `twitter feed` / `twitter user-posts @somebody`

### Important notes

> **Install**: `pipx install 'twitter-cli==0.8.5'` (version pinned)
>
> **Auth**: only via manual Cookie-Editor export (`agent-reach configure twitter-cookies`); the
> `scripts/twitter.py` wrapper then supplies `TWITTER_AUTH_TOKEN` + `TWITTER_CT0` from the config on every
> call. Don't rely on automatic browser reading.
>
> **IP risk control**: don't call this frequently from a VPS/data-center IP, especially for followers/following — risk of account suspension. Use a residential proxy or a local environment.
>
> **OpenCLI fallback**: if OpenCLI is installed on desktop, the full set `opencli twitter search/article/user-posts -f yaml` works (browser login state, no cookie env vars needed).
>
> **Output format**: prefer `--yaml` or `--json` for structured output that's friendlier to an AI agent.

## Bilibili

> ⚠️ **Don't use yt-dlp for Bilibili** (anti-bot measures now block it entirely with 412, confirmed no workaround). Use bili-cli / OpenCLI.

```bash
# Search / trending / video details (bili-cli, read-only, no login required)
bili search "query" --type video -n 5
bili hot -n 10
bili video BVxxx

# Subtitles (OpenCLI, requires desktop Chrome)
opencli bilibili subtitle BVxxx
```

> For detailed commands (audio transcription, direct API fallback) see [references/video.md](video.md).

## V2EX (public API)

No authentication required — call the public API directly.

### Hot topics

```bash
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"
```

### Node topics

```bash
# node_name examples: python, tech, jobs, qna, programmers
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=python&page=1" -H "User-Agent: agent-reach/1.0"
```

### Topic details

```bash
# topic_id comes from the URL, e.g. https://www.v2ex.com/t/1234567
curl -s "https://www.v2ex.com/api/topics/show.json?id=TOPIC_ID" -H "User-Agent: agent-reach/1.0"
```

### Topic replies

```bash
curl -s "https://www.v2ex.com/api/replies/show.json?topic_id=TOPIC_ID&page=1" -H "User-Agent: agent-reach/1.0"
```

### User info

```bash
curl -s "https://www.v2ex.com/api/members/show.json?username=USERNAME" -H "User-Agent: agent-reach/1.0"
```

### Python usage example

```python
from agent_reach.channels.v2ex import V2EXChannel

ch = V2EXChannel()

# Get hot topics
topics = ch.get_hot_topics(limit=10)
for t in topics:
    print(f"[{t['node_title']}] {t['title']} ({t['replies']} replies)")

# Get node topics
node_topics = ch.get_node_topics("python", limit=5)

# Get topic details + replies
topic = ch.get_topic(1234567)
print(topic["title"], "—", topic["author"])

# Get user info
user = ch.get_user("Livid")
```

> **Node list**: https://www.v2ex.com/planes

## Reddit (multi-backend, login state required)

**Reddit has no zero-config path**: the anonymous `.json` endpoints are now blocked (403), and the official API has largely stopped approving new applications manually since 2025-11. Both backends rely on a login state — first run `agent-reach doctor --json` to check reddit's `active_backend`. Access from mainland China requires a proxy.

> When the OpenCLI bridge is ready, Doctor live-verifies the login with the read-only command `opencli reddit whoami`:
> a real username yields `status: ok` / `active_backend: OpenCLI`; a failed probe stays `warn` with the reason.
> The probe reads no cookie and writes no state. Set `reddit_probe: off` (or `REDDIT_PROBE=off`) to keep Doctor out
> of the browser entirely.

### Backend A: OpenCLI (preferred on desktop, reuses browser login state)

```bash
# Search posts
opencli reddit search "query" -f yaml

# Read a post's full text + comments
opencli reddit read POST_ID -f yaml

# Browse a subreddit / hot / popular
opencli reddit subreddit LocalLLaMA -f yaml
opencli reddit hot -f yaml
opencli reddit popular -f yaml

# Subreddit metadata (subscriber count, description)
opencli reddit subreddit-info LocalLLaMA -f yaml
```

> Requires Chrome to be open and logged in to reddit.com in the browser.

### Backend B: rdt-cli (legacy/server fallback, upstream unmaintained since 2026-03)

```bash
rdt search "query" --limit 10   # Search posts
rdt read POST_ID                # Read a post's full text + comments
rdt sub python --limit 20       # Browse a subreddit
rdt popular --limit 10          # Browse popular
rdt all --limit 10              # Browse /r/all
```

> **Install**: `pipx install 'git+https://github.com/public-clis/rdt-cli.git@5e4fb3720d5c174e976cd425ccc3b879d52cac66'` (pinned to a reviewed commit). Run `rdt login` first before you can search and read (on a server with no browser, write the cookie manually — see the doctor prompt).
> Prefer `--yaml` output, which is friendlier to an AI agent.

### Advanced option: official API + PRAW (only for users who already have credentials)

Users who registered a Reddit script app before 2025-11 (and hold a client_id/client_secret) can use PRAW to access the official API (100 QPM free). New applications require manual approval and are largely rejected for personal projects, **do not recommend this path to new users**.

## Facebook (OpenCLI, login state required)

Facebook goes through OpenCLI, reusing the user's facebook.com login state in Chrome. First run `agent-reach doctor --json` to check facebook's `active_backend`, which should normally be `OpenCLI`. Don't recommend Jina/Exa/Graph API as the default path.

```bash
# Search users / pages / posts
opencli facebook search "query" -f yaml

# User or page info
opencli facebook profile zuck -f yaml

# Current account's News Feed
opencli facebook feed --limit 10 -f yaml

# List of groups visible to / recent activity of the current account
opencli facebook groups --limit 20 -f yaml
```

> Requires Chrome to be open with the OpenCLI extension installed, and logged in to facebook.com. Facebook Groups currently only guarantees reading the current account's visible group list/recent activity — not an API for arbitrary group posts and comments.

## Instagram (OpenCLI, login state required)

Instagram goes through OpenCLI, reusing the user's instagram.com login state in Chrome. First run `agent-reach doctor --json` to check instagram's `active_backend`, which should normally be `OpenCLI`. Don't default back to instaloader; it has historically been unstable with cookies/401/429 issues.

```bash
# Search users (not a site-wide post keyword search)
opencli instagram search "query" -f yaml

# User profile
opencli instagram profile nasa -f yaml

# User's recent posts
opencli instagram user nasa --limit 12 -f yaml

# Explore / Discover
opencli instagram explore --limit 20 -f yaml

# Current account's saved posts
opencli instagram saved --limit 20 -f yaml
```

> Requires Chrome to be open with the OpenCLI extension installed, and logged in to instagram.com. `instagram search` is a user search; to read posts you need to determine the username first, then use `instagram user USERNAME`. If you hit 429 / login required, have the user log back in via Chrome and reduce request frequency.

## Browser session cleanup

Per SKILL.md standing rule 7, close the OpenCLI tab lease when done with any of these platforms, e.g.:
`opencli browser site:reddit close`
