# Micro Agent Protocol (MAP) Specification v1.0

## Overview

MAP is a declarative format for defining AI agent workflows in a single YAML file.

## File Structure

```yaml
version: "1.0"           # Required: MAP version
name: string             # Required: Workflow name
description: string      # Optional: Human-readable description
trigger: trigger_spec    # Optional: How workflow is triggered

env:                     # Optional: Environment variables
  VAR_NAME: default_value | required

inputs:                  # Optional: Expected inputs
  param_name:
    type: string | number | boolean | array | object
    description: string
    required: boolean
    default: any

tools:                   # Optional: Tool definitions
  tool_name:
    type: http | webhook | mcp | shell | function
    # Tool-specific config...

steps:                   # Required: Workflow steps
  - id: step_id
    intent: string       # Natural language description
    input: object        # Step inputs (can reference previous outputs)
    when: string         # Optional: Condition to execute
    tools: [string]      # Optional: Tools this step can use
    output: string       # Optional: Variable name for output
    retry: retry_spec    # Optional: Retry configuration
    timeout: number      # Optional: Timeout in seconds
```

## Trigger Specification

```yaml
# Cron trigger
trigger: cron "0 9 * * *"

# Event trigger
trigger:
  type: webhook
  path: /my-workflow

# Manual trigger (default)
trigger: manual
```

## Step Definition

### Basic Step
```yaml
- id: fetch_data
  intent: "Fetch latest stock prices for {symbols}"
  output: prices
```

### Conditional Step
```yaml
- id: alert
  intent: "Send alert if price changed significantly"
  when: "abs(prices.change) > threshold"
  tools: [slack]
```

### Step with Tools
```yaml
- id: query_database
  intent: "Get user data from database"
  tools: [postgres]
  input:
    query: "SELECT * FROM users WHERE id = {user_id}"
```

### Parallel Steps
```yaml
- parallel:
    - id: fetch_weather
      intent: "Get weather data"
      tools: [weather_api]
      
    - id: fetch_news
      intent: "Get news headlines"
      tools: [news_api]
```

## Variable References

Use `{variable}` syntax to reference:
- Previous step outputs: `{step_id}`
- Environment variables: `{env.VAR_NAME}`
- Inputs: `{input.param_name}`
- Nested access: `{step_id.field.nested}`

## Tool Types

### HTTP Tool
```yaml
tools:
  weather_api:
    type: http
    base_url: https://api.weather.com
    auth:
      type: bearer
      token: ${WEATHER_API_KEY}
```

### Webhook Tool
```yaml
tools:
  slack:
    type: webhook
    url: ${SLACK_WEBHOOK_URL}
    method: POST
```

### MCP Tool
```yaml
tools:
  filesystem:
    type: mcp
    server: filesystem-mcp
    command: mcp-filesystem
```

### Shell Tool
```yaml
tools:
  git:
    type: shell
    allowed_commands: [git, npm, pip]
    sandbox: true
```

### Function Tool
```yaml
tools:
  custom_tool:
    type: function
    module: my_tools
    function: process_data
```

## Error Handling

### Retry Specification
```yaml
retry:
  max_attempts: 3
  backoff: exponential  # linear | exponential | fixed
  initial_delay: 1      # seconds
  max_delay: 60         # seconds
```

### Fallback
```yaml
- id: primary_api
  intent: "Fetch from primary API"
  fallback:
    - id: backup_api
      intent: "Fetch from backup API"
```

## Output Specification

```yaml
output:
  format: json | markdown | text
  schema:
    field_name:
      type: string
      description: Field description
```

## Complete Example

```yaml
version: "1.0"
name: daily-standup-bot
description: Automated daily standup report generator
trigger: cron "0 9 * * 1-5"  # 9 AM on weekdays

env:
  JIRA_API_KEY: required
  SLACK_WEBHOOK: required
  GITHUB_TOKEN: required

inputs:
  team_members:
    type: array
    description: List of team member usernames
    required: true

steps:
  - parallel:
      - id: jira_tasks
        intent: "Get tasks completed yesterday and planned for today from JIRA"
        tools: [jira]
        input:
          users: {team_members}
          
      - id: github_prs
        intent: "Get open PRs from GitHub"
        tools: [github]
        input:
          users: {team_members}
  
  - id: generate_report
    intent: "Generate a standup report from {jira_tasks} and {github_prs}"
    output: report
    
  - id: post_slack
    intent: "Post the standup report to team channel"
    tools: [slack]
    when: "report != ''"
    input:
      message: {report}

tools:
  jira:
    type: http
    base_url: https://company.atlassian.net
    auth:
      type: bearer
      token: ${JIRA_API_KEY}
      
  github:
    type: http
    base_url: https://api.github.com
    auth:
      type: bearer
      token: ${GITHUB_TOKEN}
      
  slack:
    type: webhook
    url: ${SLACK_WEBHOOK}

output:
  format: json
```

## Runtime Targets

MAP files can be executed on different runtimes:

1. **Python Interpreter** (map run)
   - Full Python environment
   - All tool types supported
   
2. **KrillClaw Binary** (map compile --target krillclaw)
   - Compiled to Zig binary
   - Subset of features (HTTP, webhook, shell tools)
   
3. **OpenClaw Skill** (map compile --target openclaw)
   - Generates skill directory with SKILL.md
   - Integrates with OpenClaw ecosystem

4. **Edge Runtime** (map compile --target wasm)
   - WebAssembly for browser/edge
   - Limited tool support

## Extension Points

### Custom Tool Types
```yaml
tools:
  my_custom:
    type: custom
    runtime: python
    module: custom_tools
    class: MyCustomTool
```

### Plugins
```yaml
plugins:
  - name: observability
    config:
      tracing: true
      metrics: true
```

## Versioning

- MAP spec follows semver
- `version` field in YAML must match interpreter version
- Backward compatibility guaranteed within major version
