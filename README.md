# Micro Agent Protocol (MAP) 🗺️

> **A 50-line YAML that runs anywhere** - Define agent workflows in a single file, execute on microcontrollers, edge devices, or cloud servers.

## Why MAP?

Inspired by [KrillClaw](https://github.com/krillclaw/KrillClaw) (49KB agent runtime) and [IntentLang](https://github.com/l3yx/intentlang) (intent-driven programming), MAP is an experiment in **minimalist agent orchestration**.

**The Problem:**
- AI agent frameworks are heavy (50-500MB, 100+ dependencies)
- Workflow definitions require complex infrastructure
- Edge devices can't run typical agent systems

**The MAP Solution:**
```yaml
# agent.map.yaml - Your entire agent workflow in one file
version: "1.0"
name: research-agent
trigger: cron "0 9 * * *"

steps:
  - id: fetch
    intent: "Search for recent papers on {topic}"
    output: papers
    
  - id: analyze
    intent: "Summarize key findings from {papers}"
    when: "len(papers) > 0"
    output: summary
    
  - id: notify
    intent: "Send summary to Slack"
    tools: [slack]
    input: {summary}

tools:
  slack:
    type: webhook
    url: ${SLACK_WEBHOOK}
```

## Core Concepts

### 1. **Intent-First Design**
Like IntentLang, MAP treats natural language as executable:
```yaml
- intent: "Find the best price for {product}"
```

### 2. **Single File, Zero Dependencies**
Inspired by KrillClaw's minimalism:
- One YAML file = complete workflow
- Optional: compile to standalone binary
- Runs on devices with 2MB RAM

### 3. **Universal Runtime Targets**
```bash
# Run directly (Python interpreter)
map run agent.map.yaml

# Compile to KrillClaw binary (Zig)
map compile --target krillclaw agent.map.yaml -o agent

# Export as OpenClaw skill
map compile --target openclaw agent.map.yaml -o skill/
```

## Quick Start

```bash
# Install
pip install micro-agent-protocol

# Create your first agent
cat > daily-news.map.yaml << 'EOF'
version: "1.0"
name: daily-news
trigger: cron "0 8 * * *"

env:
  NEWS_API_KEY: required

steps:
  - id: fetch
    intent: "Get top 5 tech news headlines"
    tools: [http]
    
  - id: summarize
    intent: "Create a brief summary of these headlines"
    
  - id: deliver
    intent: "Send to my email"
    tools: [email]
EOF

# Run
map run daily-news.map.yaml
```

## Design Philosophy

| Principle | Implementation |
|-----------|----------------|
| **Minimalism** | Core spec < 500 lines |
| **Readability** | YAML that reads like documentation |
| **Portability** | Runs on microcontroller to cloud |
| **Intent-driven** | Natural language as first-class construct |
| **Zero-config** | Sensible defaults, no setup required |

## MAP vs Other Approaches

| Feature | MAP | LangChain | CrewAI | KrillClaw |
|---------|-----|-----------|--------|-----------|
| Single file workflow | ✅ | ❌ | ❌ | ❌ |
| Runs on microcontroller | ✅ | ❌ | ❌ | ✅ |
| Intent-first | ✅ | ❌ | ❌ | ❌ |
| Zero dependencies | ✅ | ❌ | ❌ | ✅ |
| Visual workflow editor | 🔄 | ❌ | ❌ | ❌ |

## Roadmap

- [ ] Core YAML spec v1.0
- [ ] Python interpreter
- [ ] KrillClaw compiler target
- [ ] OpenClaw skill exporter
- [ ] Visual editor (Web)
- [ ] VS Code extension
- [ ] Embedded examples (RPi Pico, ESP32)

## Inspiration & Credits

- **[KrillClaw](https://github.com/krillclaw/KrillClaw)** - Proving agents can be tiny
- **[IntentLang](https://github.com/l3yx/intentlang)** - Intent as first-class executable
- **[12-Factor Agents](https://github.com/humanlayer/12-factor-agents)** - Agent design principles

## License

MIT

---

**MAP**: Because your agent workflow shouldn't need a 500MB runtime.
