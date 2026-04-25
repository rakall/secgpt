# pentest-agent

Analyze security reconnaissance with semantic search, persistent sessions, and configurable LLM-backed assistance.

This project is read-only and does not execute payloads or perform active exploitation. It ingests existing pentest tool output, normalizes it into a structured session database, retrieves relevant context from a local knowledge base, and generates deterministic analysis and reports for security operators.

## Status

Functional MVP with session management, ingestion, knowledge-base retrieval, analysis, chat, and reporting in place. Ongoing work is focused on final hardening and workflow cleanup rather than core feature availability.

## Features

- Session-based workflow with SQLite persistence and WAL mode enforcement
- Tool ingestion for Nmap, Nuclei, FFUF, OpenAPI, Burp, and raw HTTP request data
- Local knowledge base backed by ChromaDB with NVD, MITRE ATT&CK, and runbook content
- Configurable LLM providers: local GGUF models, OpenAI, Anthropic, and Google
- Deterministic analysis pipeline with rule-based intent classification and static SQL planning
- Interactive chat workflow for session-aware analysis
- Session analysis persistence for report generation
- Markdown and JSON reporting
- YARA and Sigma stub generation from findings and KB context
- Audit logging, sanitization, and prompt-injection mitigations

## Requirements

- Python 3.11+
- `pip`
- ChromaDB-compatible local runtime environment
- Knowledge base source files you provide yourself, such as NVD feeds, ATT&CK data, and runbooks

To enable local LLM support, install the optional `local` extra and provide GGUF-formatted model files separately during configuration.

## Installation

```bash
pip install -e .
pip install -e .[local]
```

Configuration is stored in `~/.config/pentest-agent/` with sensitive credentials kept in the `secrets` file within that same directory.

Run `agent --help` to explore available commands and subcommands.

## Quick Start

Before using this tool, ensure you have explicit written permission to perform security testing on the target systems, as unauthorized access is illegal.

The examples below assume you already have scan output files; this tool analyzes existing security data and does not run scans itself.

```bash
agent init demo-target
agent sessions use demo-target
agent scope add --ip 10.0.0.10
agent daemon start
agent ingest nmap --file .\samples\scan.xml
agent analyze session
agent report
```

To export structured output instead of Markdown:

```bash
agent report --format json
```

## Common Commands

### Session and setup

```bash
agent init <target>
agent sessions list
agent sessions use <target>
agent status
```

### Scope and configuration

```bash
agent scope add --ip 10.0.0.10
agent scope add --cidr 10.0.0.0/24
agent scope show
agent config show
agent config set provider.active local
```

### Daemon and knowledge base

```bash
agent daemon start
agent daemon status
agent kb ingest --nvd-feed .\feeds\nvd.json --attck .\feeds\enterprise-attack.json --runbook .\runbooks
agent kb stats
agent kb check
```

ChromaDB-backed knowledge-base operations require the daemon to be running.

### Ingestion

```bash
agent ingest nmap --file .\scan.xml
agent ingest nuclei --file .\findings.jsonl
agent ingest ffuf --file .\ffuf.json
agent ingest openapi --file .\openapi.yaml
agent ingest burp --file .\burp.xml
agent ingest http --file .\requests.txt
```

### Exploration and analysis

```bash
agent show hosts
agent show endpoints
agent show findings
agent analyze session
agent analyze analyze-code --file .\app.py
agent analyze query-cve CVE-2024-1234
agent analyze query-service Apache
agent analyze query-rules --finding-id <finding-id>
agent chat
```

### Reporting

```bash
agent report
agent report --format json
```

`agent analyze session` stores a session-level summary, attack paths, and ATT&CK mapping that `agent report` can render into Markdown or JSON output.

## Workflow Model

The intended flow is:

1. Create a session workspace.
2. Define engagement scope.
3. Start the daemon.
4. Ingest existing scan output.
5. Review hosts, endpoints, and findings.
6. Run session analysis.
7. Generate reports or exports.

`agent init` creates a per-target workspace under `sessions/<target>/` with `session.db`, `scope.txt`, and subdirectories for `ingested/`, `reports/`, and `rules/`.

## Architecture

- CLI: Typer-based command surface
- Session state: SQLite with WAL mode
- Knowledge base: ChromaDB collections managed through a background daemon
- Embeddings: local-first, using local model configuration
- Analysis: rule-based intent classification, deterministic query planning, KB retrieval, prompt assembly, and hashing
- Reporting: session-backed analysis persistence plus Markdown and JSON rendering

## Security and Privacy

- All ingested tool output is sanitized before storage
- Secrets are kept out of `config.toml`
- Sensitive values such as passwords, tokens, and API keys are redacted
- Prompt injection mitigations are applied to session and code artifact inputs
- Knowledge-base embeddings are kept local-first
- External providers are configurable, with explicit confirmation flow in the CLI
- Audit logs record analysis and reporting activity

See `docs/SECURITY.md` for the detailed security architecture and hardening notes.

## Repository Layout

```text
secgpt/
├── pyproject.toml
├── docs/
├── pentest_agent/
│   ├── analysis/
│   ├── cli/
│   ├── config/
│   ├── daemon/
│   ├── db/
│   ├── ingest/
│   ├── kb/
│   └── logging/
└── tests/
```

## Contributing

Run verification scripts in the `tests/` directory with Python, such as `python tests/test_determinism_regression.py`, before submitting changes.

## Limitations

- Users must provide their own scan outputs and knowledge base source data
- The tool does not perform active exploitation or state-changing actions
- Hardening and workflow cleanup are still being refined around the MVP core