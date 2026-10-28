# Career & Recruiting

LinkedIn.

## LinkedIn

```bash
# Get a person's profile
mcporter call linkedin.get_person_profile linkedin_username="username" sections="experience,education"

# Search for talent
mcporter call linkedin.search_people keywords="AI engineer" location="Shanghai"

# Get a company's profile
mcporter call linkedin.get_company_profile company_name="openai" sections="posts,jobs"

# Search for jobs
mcporter call linkedin.search_jobs keywords="software engineer" location="Remote" max_pages=2
```

> **Login required**: before first use, run `mcp-server-linkedin --login` (first `uv tool install mcp-server-linkedin==4.24.2`; never `uvx ...@latest`) to save a valid login state.

### Fallback option

If the MCP is unavailable, you can use Jina Reader:

```bash
curl -s "https://r.jina.ai/https://linkedin.com/in/username"
```

## Browser session cleanup

If a LinkedIn lookup went through OpenCLI, close its tab lease when done (SKILL.md standing rule 7):
`opencli browser site:linkedin close`
