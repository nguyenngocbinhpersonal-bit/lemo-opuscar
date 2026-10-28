# Finance & Market Data

Xueqiu stock quotes, search, and trending content. Quotes may be delayed; this is not investment advice.

## Check status first

```bash
agent-reach doctor --json
```

When `xueqiu.active_backend` has a value, use that backend; a value of `null` only means Doctor didn't complete
live content verification. Xueqiu requires a logged-in session or a minimal cookie — don't treat an HTTP 400 as "the stock doesn't exist."

## OpenCLI (preferred when desktop already has a Chrome login state)

```bash
# Verify current login state
opencli xueqiu whoami -f yaml

# Stock search and live quotes
opencli xueqiu search "NVIDIA" -f yaml
opencli xueqiu stock NVDA -f yaml

# Trending content and trending stocks
opencli xueqiu hot -f yaml
opencli xueqiu hot-stock -f yaml

# See all read-only commands
opencli xueqiu --help
```

OpenCLI only reuses a browser session the user already has and explicitly controls. Do not automatically run
`opencli xueqiu login`; if no login state exists, have the user log in via Chrome first, or explicitly import
the minimal cookie Xueqiu needs:

```bash
agent-reach configure --from-browser chrome --platform xueqiu
```

This configuration only reads and saves `xq_a_token`; it does not incidentally collect cookies for other platforms.

## Acceptance and failure handling

- Success means the response returns a stock name, code, price, or a non-empty content list; exit code 0 with empty fields does not count as success.
- HTTP 400 is usually a session/cookie problem, not proof the stock code doesn't exist.
- If `whoami` succeeds but `stock`/`hot` fails, report it as an adapter-parsing or platform-API issue — don't misdiagnose it as "not logged in."

## Browser session cleanup

`opencli xueqiu whoami` is a persistent session, so close its tab lease when done (SKILL.md standing rule 7):
`opencli browser site:xueqiu close`
