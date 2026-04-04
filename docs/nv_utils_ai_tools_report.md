# NVIDIA /home/nv/utils/ AI-Related Tools - Deep Research Report

**Date**: April 3, 2026  
**Scope**: Comprehensive inventory of AI-powered agent tools, agentic frameworks, and LLM integration tools

---

## Executive Summary

The `/home/nv/utils/` directory houses a rich ecosystem of AI-assisted development tools spanning **50+ projects** across chip design, debug automation, coverage analysis, and development workflows. These tools leverage LLMs, RAG systems, and agentic frameworks to improve HW/SW verification, debugging, and productivity.

**Key Observations:**
- **Two-tier architecture**: Core agent frameworks (Carpenter, nv-agent, Nighthawk) + domain-specific tools (ChipNeMo, Athena, Coverscout)
- **Standard deployment**: Versioned releases at `/home/nv/utils/<tool>/<version>/` with NFS mirroring of P4 source
- **IDE integration**: Heavy focus on Claude Code / Cursor / Codex plugins and MCP server integration
- **Authentication**: Most tools require NVIDIA SSO (serviceToken, NVAUTH_PROXY_TOKEN, or NVCARPS token)
- **Distribution**: NICC CLI (emerging) as central discovery + skill/plugin registry (NV-CARPS backend)

---

## Summary Table

| Tool | Path | Version | Type | Auth Required | Key Capability |
|------|------|---------|------|---|---|
| **ChipNeMo CLI** | `/home/nv/utils/chipnemo-cli/` | 1.0.0+ | LLM CLI | serviceToken | Domain-adapted LLM for chip design Q&A |
| **NICC CLI** | `/home/nv/utils/nicc-cli/` | 1.0.9 | Hub/Registry | NVCARPS token | Central skill/rule/plugin discovery & installation |
| **Agent Skills** | `/home/nv/utils/agent_skills/` | -- | Framework | service-token | 50+ atomic agent-invoked capabilities (skills) |
| **Agent Plugins** | `/home/nv/utils/agent_plugins/` | -- | Framework | -- | Compound bundles (skills + MCPs + hooks + agents) |
| **Carpenter** | `/home/nv/utils/carpenter/` | 1.0+ | Agent Framework | -- | Agent orchestration engine + GUI |
| **nv-agent** | `/home/nv/utils/nv-agent/` | 0.0.1 | Agent Framework | -- | Terminal coding agent framework (LLM orchestration) |
| **Arch-Agent** | `/home/nv/utils/arch-agent/` | 2.1.1 | Specialized Agent | NVAUTH_PROXY_TOKEN | Architecture design assistant with DeepAgent CLI |
| **Athena Agent** | `/home/nv/utils/athena-agent/` | 0.1.12 | Plugin System | -- | Multi-IDE harness (Claude/Cursor/Codex) |
| **Arrow AI** | `/home/nv/utils/arrow_ai/` | 0.4.1 | RAG + Indexer | NVIDIA API key | Arrow test development RAG pipeline + API indexing |
| **CoverScout** | `/home/nv/utils/mmplex/coverscout/` | 0.85+ | Coverage AI | Azure OpenAI API | AI-powered coverage-to-POR mapping tool |
| **Nighthawk** | `/home/nv/utils/mmplex/nighthawk/` | 1.0.10 | Debug Agent | -- | Automated RTL test debug with WaveInsight MCP |
| **CL2Feature** | `/home/nv/utils/mmplex/cl2feature/` | 1.0.4 | AI Analyzer | P4 access | P4 changelist → feature impact mapping |
| **Agentic Skills** | `/home/nv/utils/mmplex/agentic_skills/` | 1.0.23 | Skills Library | -- | 30+ debug & analysis skills (bug-analysis, fsdb, rtl-trace, etc.) |
| **Stepstone** | `/home/nv/utils/stepstone/` | 1.80 | Build Tool | -- | Advanced build system |
| **WaveRunner** | `/home/nv/utils/waverunner/` | 1.4.0 | Debug Assistant | -- | Automated waveform tracing & RTL debug |
| **SmartLog MCP** | `/home/nv/utils/smartlog_mcp/` | 0.1.0 | MCP Server | Cadence tools | Cadence Verisium SmartLog analysis via MCP |
| **SimAI** | `/home/nv/utils/simai/` | 1.6 | Simulation Framework | -- | AI-assisted simulation flows |
| **Coverage AI** | `/home/nv/utils/coverage_ai/` | 1.12 | Coverage Flow | -- | Coverage infra for Synopsys/Cadence |
| **RTLOS AI** | `/home/nv/utils/rtlos_ai/` | 0.3.0 | Domain Tool | -- | Real-time low-latency OS AI support |
| **KDS Agent** | `/home/nv/utils/kds_agent/` | -- | Agent | -- | Knowledge discovery agent |
| **NVault Agent** | `/home/nv/utils/nvault-agent/` | -- | Agent | -- | NVIDIA secret/vault management agent |
| **PSC Misc Agent** | `/home/nv/utils/psc_misc_agent/` | -- | Utilities | -- | PSC (Platform Services) miscellaneous tools |

---

## Detailed Tool Analysis

### TIER 1: CORE AGENT FRAMEWORKS

#### 1. **Carpenter** - Agent Orchestration Engine
- **Path**: `/home/nv/utils/carpenter/release/`, `latest/`
- **Type**: Agent orchestration and GUI platform
- **Version**: 1.0+
- **Key Files**: 
  - `carpenter` binary (release binary)
  - `venv/bin/python3` (managed Python 3.10+ environment)
  - Quick start at `/home/nv/utils/carpenter/quick_start/`
- **What It Does**:
  - Orchestrates LLM-powered agents with tool definitions (YAML-based)
  - Provides graphical UI for agent interaction
  - Includes regression testing module for agent benchmarking
  - Python venv comes pre-installed with core dependencies (pyyaml, requests, beautifulsoup4)
- **Key Capabilities**:
  - Agent configuration via YAML
  - Tool/skill integration
  - Conversation history management
  - Performance regression testing
- **Usage**:
  ```bash
  /home/nv/utils/carpenter/release/carpenter --config config.yml
  /home/nv/utils/carpenter/release/carpenter_regress --test_path test.yml
  ```
- **Auth Required**: No explicit auth at framework level; depends on underlying LLM
- **Shebang for Scripts**: `#!/home/nv/utils/carpenter/release/venv/bin/python3`

---

#### 2. **nv-agent** - Terminal Coding Agent Framework  
- **Path**: `/home/nv/utils/nv-agent/0.0.1/`
- **Type**: Lightweight Python agent framework
- **Version**: 0.0.1
- **Key Files**:
  - `/home/nv/utils/nv-agent/release/nv-agent` (symlink to .venv binary)
  - `nv-agent/` Python package
- **What It Does**:
  - Terminal-based coding agent (inspired by Carpenter)
  - Orchestrates LLMs over local codebases
  - Workspace-aware agent execution
  - Supports config-driven tool/skill registration
  - TUI (text UI) and headless modes
- **Key Capabilities**:
  - `nv-agent` - Interactive TUI with auto-submit
  - `nv-agent exec` - Headless mode with JSON output
  - `--config-dir` - Custom config location
  - `--max-turns` - Control conversation depth
  - `--json` - Structured output for integration
- **Python Requirements**: Python >=3.12,<3.13 + uv (Astral)
- **Usage**:
  ```bash
  uv run nv-agent "Say hello"
  uv run nv-agent exec "Say hello" --max-turns 50 --json
  ```
- **Auth Required**: Depends on LLM backend config
- **Config**: `.nv-agent/config.yml` (auto-created on first run)

---

### TIER 2: DISCOVERY & SKILL/PLUGIN MANAGEMENT

#### 3. **NICC CLI** - Centralized Tool Discovery Hub
- **Path**: `/home/nv/utils/nicc-cli/1.0.9/`
- **Type**: CLI tool for skill/rule/plugin discovery and installation
- **Version**: 1.0.9
- **What It Does**:
  - Central gateway for skill/rule discovery (queries NV-CARPS backend)
  - Installs skills to Claude Code, Cursor, or Codex
  - Configures MCP servers (MaaS/MARS)
  - Manages authentication to NVCARPS
  - AI-powered skill/rule recommendations ("query")
  - Version update checking
- **Key Commands**:
  - `nicc login` - SSO authentication
  - `nicc mcp` - Configure MCP servers
  - `nicc rules list`, `nicc rules query`, `nicc rules pull` - Rule discovery
  - `nicc skills list`, `nicc skills query`, `nicc skills pull` - Skill discovery
  - `nicc update-check` - Check for NICC CLI updates
- **Installation Targets**:
  - Claude Code: `~/.claude/rules/`, `~/.claude/skills/`
  - Cursor: `~/.cursor/rules/`, `~/.cursor/skills/`
  - Codex: `.agents/skills/`
- **Auth Required**: 
  - NVCARPS token via `nicc login` (SSO)
  - Optional: `NVCARPS_TOKEN`, `MAAS_TOKEN` environment variables
- **Upstream Dependencies**:
  - NV-CARPS (registry backend) — pulls skill metadata
  - MaaS/MARS (MCP server hosting)

---

#### 4. **Agent Skills** - Atomic Capability Library
- **Path**: `/home/nv/utils/agent_skills/`
- **Type**: Shared skill library + source-of-truth
- **Content**: 50+ skills organized by category
- **What It Does**:
  - Central repository of agent-invoked skills
  - Automatically indexed into NV-CARPS registry
  - Distributed via NICC CLI to IDEs
  - Skills marked with `SKILL.md` frontmatter for discovery
- **Skill Categories**:
  - **Build Infra**: AS2, AXL, DVS (build status, failures, logs)
  - **VCS**: Perforce (P4 commands, changelists)
  - **Waveform**: Debug (Verisium/Indago waveform analysis)
  - **HW Languages**: VIVA assistant
  - **Search**: Copilot chat, retriever, VLSI search (RAG knowledge bases)
  - **Docs**: Confluence writer
  - **NV Tools**: NVBugs, NVRegress, NVDataFlow
  - **Data**: Dataframe QA, file-to-markdown conversion
  - **Contrib**: Experimental (low barrier to entry)
- **Key Files**:
  - `SKILL.md` in each skill directory (metadata + instructions)
  - Python scripts with shebang: `#!/home/nv/utils/carpenter/release/venv/bin/python3`
  - `scripts/requirements.txt` for specialized dependencies
  - Impact measurement via `@instrument` decorator
- **Auth**: service-token (embedded in Carpenter venv)
- **Discovery**: Automatic P4→NFS mirror→NV-CARPS ingestion pipeline

---

#### 5. **Agent Plugins** - Compound Bundles
- **Path**: `/home/nv/utils/agent_plugins/`
- **Type**: Plugin orchestration (skills + MCPs + hooks + agents)
- **What It Does**:
  - Groups multiple skills, MCP servers, and hooks into single installable unit
  - Thin manifest approach (no code duplication, references skills from agent_skills)
  - Supports both Claude Code (`plugin.json`) and Cursor layouts
- **Plugin Structure**:
  - `.claude-plugin/plugin.json` - Claude Code manifest
  - `nvcarps_bundle.yaml` - Dependency declaration
  - `skills/` - Thin skill pointers
  - `agents/` - Custom sub-agent definitions
  - `hooks/` - Event handlers
  - `.mcp.json` - MCP server configs
- **Currently Available Plugins**:
  - `perforce-agent` (org-wide P4 operations)
  - `viva-agent` (org-wide VIVA language assistant)
  - `rca-agent` (org-wide root-cause analysis)
  - `units/gpu/sm/sm-wave-triage/` (SM waveform triage)
  - `contrib/` (experimental)
- **Auth**: Depends on referenced skills & MCPs
- **Installation**: Manual via `claude --plugin-dir` (NICC bundle support upcoming)

---

### TIER 3: DOMAIN-SPECIFIC AI AGENTS

#### 6. **ChipNeMo CLI** - Chip Design LLM Interface
- **Path**: `/home/nv/utils/chipnemo-cli/stg/`, `1.0.0/`, etc.
- **Type**: LLM query CLI (pre-compiled binary)
- **Version**: 1.0.0+ (staging + versioned releases)
- **What It Does**:
  - Domain-adapted LLM for chip design workflows
  - Q&A interface for hardware engineering
  - Backed by ChipNeMo model (NVIDIA domain-adapted LLM)
- **Key Commands**:
  - `chipnemo ask "What is CUDA?"` - Direct query
  - `chipnemo sessions` - View conversation history
  - `chipnemo` - Show help and options
- **Configuration**: `~/.chipnemo/config.yaml`
  - `model`: gpt-4o, claude-3.5-sonnet, etc.
  - `chipnemoAPIKey`: API key (or use serviceToken)
  - `copilot`: ghw-power, router (default)
  - `team`: gpu-power, etc.
- **Auth Required**:
  - **Recommended**: serviceToken (`/home/nvmetrics/serviceToken/serviceToken init`)
  - **Alternative**: Auth token (get from NVCARPS team)
- **Shebang**: Pre-compiled binary (no setup needed)
- **Platform**: Rocky8 only (not CentOS)
- **Usage**:
  ```bash
  export PATH=/home/nv/utils/chipnemo-cli/stg:$PATH
  chipnemo ask "How do I optimize CUDA kernels?"
  ```

---

#### 7. **Arrow AI** - RAG + API Indexing
- **Path**: `/home/nv/utils/arrow_ai/0.4.1/`
- **Type**: RAG pipeline + API documentation indexer
- **Version**: 0.4.1
- **What It Does**:
  - Hybrid retrieval (FAISS vector search + BM25 keyword, fused via RRF)
  - Arrow test development RAG (doc ingestion + query)
  - Arrow API auto-discovery and documentation generation
  - SQLite indexing with full-text search (FTS5)
  - ISANOVA instruction database conversion
- **Key CLIs**:
  - `arrow-ai` - Unified CLI (rag + index subcommands)
  - `arrow-rag` - Standalone RAG pipeline
  - `arrow-indexer` - Content/API indexing
- **Commands**:
  - `arrow-ai rag ingest` - Load documents into RAG
  - `arrow-ai rag status` - Show index status
  - `arrow-ai index content /path` - Generate content docs
  - `arrow-ai index api /path` - Generate API reference
  - `arrow-indexer search db.db "query"` - Full-text search
- **Configuration**: `config.yaml`, `sources.yaml` (YAML-based sources)
- **Embedding Providers**: NVIDIA NIM (default), OpenAI, SentenceTransformers
- **Rerankers**: NVIDIA NIM, Cohere, local CrossEncoder
- **Python**: Python 3.12+ with Poetry
- **Installation**:
  ```bash
  poetry config virtualenvs.in-project true
  poetry install --with dev
  ```
- **Auth Required**: NVIDIA API key (for NIM embedding/reranking)
- **Output**: Markdown docs, SQLite databases with structured queries

---

#### 8. **Arch-Agent** - Architecture Design Assistant
- **Path**: `/home/nv/utils/arch-agent/2.1.1/`
- **Type**: Specialized agent for architecture verification
- **Version**: 2.1.1 (released 2026-03-31)
- **What It Does**:
  - Architecture-aware debug & verification agent
  - Built on DeepAgent CLI framework
  - Mentis configuration for chip arch verification
  - Plugin-compatible (works with Claude Code)
- **Components**:
  - `agent/bin/arch-agent` - Command wrapper
  - `agent/langgraph_deepagent/libs/` - DeepAgent CLI + venv
  - `agent-configs/` - YAML configurations
  - `common/` - Mentis library code
- **Usage**:
  ```bash
  arch-agent --agent-dir agent-configs/mentis
  arch-agent --agent-dir agent-configs/mentis --background -i 'task'
  claude --plugin-dir agent-configs/mentis
  ```
- **Auth Required**: `NVAUTH_PROXY_TOKEN` (set in ~/.bashrc)
- **Setup**: `bash agent/bin/install_arch_agent.sh`

---

#### 9. **Athena Agent** - Multi-IDE Harness Plugin
- **Path**: `/home/nv/utils/athena-agent/0.1.12/`
- **Type**: Claude Code / Cursor / Codex plugin system
- **Version**: 0.1.12 (released 2026-03-19)
- **What It Does**:
  - Unified plugin loader for Claude Code, Cursor, Codex
  - Centralized plugin marketplace
  - Automatic harness configuration via hooks
- **Components**:
  - `agent-configs/athena/` - Plugin directory
  - `.claude-plugin/marketplace.json` - Marketplace manifest
  - `bin/install_athena_agent.sh` - One-time setup
  - `update.sh` - Update script for maintainers
- **Usage**:
  ```bash
  # Install
  bash bin/install_athena_agent.sh
  
  # Manual reinstall
  claude plugin install athena
  
  # Plugin is auto-configured for Cursor/Codex via hooks
  ```
- **Installation**: One-time script setup, auto-register marketplace

---

#### 10. **CoverScout** - AI-Powered Coverage Mapper
- **Path**: `/home/nv/utils/mmplex/coverscout/0.85+/`
- **Type**: Coverage analysis + LLM-powered feature mapping
- **Version**: 0.85+ (under 1.0)
- **What It Does**:
  - Extracts coverage properties from simulation databases (VDB)
  - Uses Azure OpenAI GPT-4 to map coverage to Plan-of-Record (POR) features
  - Multi-source context: P4 CLs, RAG docs, NVBugs, Confluence
  - MySQL database backend for persistent storage
  - Audit system tracking token usage and costs
  - Caching to avoid redundant LLM calls
- **Key CLIs**:
  - `coverscout.py -simv <path> -vdb <path>` - Extract & map coverage
  - `mx_cov2por.py <file>` - Direct coverage-to-POR mapping
  - `cov2por_db_tool.py` - Database management (stats, query, audit)
- **Dependencies**:
  - Python 3.12.5+
  - MySQL Server
  - Azure OpenAI API key
  - Verdi tool (for VDB extraction)
  - RAG context (optional)
- **Configuration**: `user_config.yaml`, `team_config.yaml`
- **Output**: JSON mappings, text reports, SQLite databases
- **Auth Required**: Azure OpenAI API key

---

#### 11. **Nighthawk** - Automated RTL Debug Agent
- **Path**: `/home/nv/utils/mmplex/nighthawk/1.0.10/`
- **Type**: Interactive debug agent with waveform analysis
- **Version**: 1.0.10
- **What It Does**:
  - Automated RTL test failure root-cause analysis
  - Waveform tracing via WaveInsight MCP (Verisium)
  - 9-step debug workflow (identify → root cause → fix → recompile → iterate)
  - QUICK MODE for root-cause-only analysis
  - Integration with test infrastructure (vlogan, vcs_elab, etc.)
- **Key Components**:
  - `config/CLAUDE.md` - Agent system prompt
  - `config/debug_prompt_template.md` - Debug workflow
  - `tools/README.txt` - Tool definitions
  - `rules.yaml` - Tool rules
- **WaveInsight Integration** (MCP tools):
  - `load_fsdb` - Load simulation database
  - `get_value_from_fsdb_to_json` - Extract signal values
  - `find_objects`, `get_drivers_or_loads_of_a_signal` - Signal discovery
  - `calc_duty_cycle`, `expr_count` - Analysis tools
- **Workflow Modes**:
  - **Full Mode**: Steps 1-9 (analysis → fix → rerun)
  - **QUICK MODE**: Steps 1-4 only (analysis → report)
- **Output**: `nighthawk_result.json` with root_cause, confidence, fix details
- **Auth Required**: None explicitly; depends on Verisium/Cadence setup

---

#### 12. **WaveRunner** - RTL Wave Tracing Assistant
- **Path**: `/home/nv/utils/waverunner/RELEASE/`, `1.4.0/`
- **Type**: Automated waveform debug tool
- **Version**: 1.4.0
- **What It Does**:
  - Automated waveform tracing and signal analysis
  - RTL debug assistant for simulations
  - Verdi integration for visualization
  - Remote server mode (SSE) for distributed access
  - Telemetry collection (opt-out available)
- **Key Commands**:
  - `waverunner trace --signal "top.sig" --time 1000` - Trace signal
  - `waverunner --help` - Show all commands
  - `waverunner stop`, `status`, `verdi-list` - Management
- **Configuration**: User documentation at `user_docs/`
- **Telemetry**:
  - Sends metrics to NVDataflow (Elasticsearch/Kibana)
  - Collects: command, username, hostname, signal paths, timings
  - **Does NOT collect signal names or error messages**
  - Opt-out: `--no-telemetry` flag or `WAVERUNNER_NO_TELEMETRY=1`
- **Verdi Integration**: Built-in support
- **Binary**: Pre-compiled, no setup required
- **Auth Required**: None

---

#### 13. **SmartLog MCP** - Cadence Verisium Analysis
- **Path**: `/home/nv/utils/smartlog_mcp/0.1.0/`
- **Type**: MCP server for Cadence waveform analysis
- **Version**: 0.1.0
- **What It Does**:
  - MCP protocol server for SmartLog database queries (Verisium)
  - Process isolation: Python 3.11 (lightweight) + separate Cadence Python backend on LSF
  - Indexed message searches, error classification, temporal traces
  - 7 MCP tools for waveform analysis
  - Auto-discovery of Cadence tool version
- **MCP Tools**:
  - `query_messages` - Filter messages by scope, type, time, content
  - `get_error_summary` - Group errors by failure type
  - `get_temporal_trace` - Timeline of events
  - `get_messages_by_tag` - Trace transaction flow
  - `classify_failure_tool` - Failure classification with confidence
  - `get_sim_status` - UVM report summary
  - `health` - Server status
- **Setup** (Cursor):
  ```json
  "smartlog_mcp": {
    "command": "/home/nv/utils/carpenter/release/venv/bin/python3.11",
    "args": ["-m", "smartlog_mcp.server"],
    "env": {"PYTHONPATH": "/path/to/smartlog-mcp/src"}
  }
  ```
- **Prerequisites**:
  - Python 3.11
  - Cadence Verisium installed
  - LSF access (qsub, list_queues)
  - Companion files: run_verisium.sh, simv_env.log, vsim.log
- **Auth Required**: LSF credentials

---

#### 14. **CL2Feature** - Changelist-to-Feature AI Mapper
- **Path**: `/home/nv/utils/mmplex/cl2feature/1.0.4/`
- **Type**: P4 → Feature impact analyzer
- **Version**: 1.0.4
- **What It Does**:
  - Maps Perforce changelists to hardware features
  - AI-powered code analysis (LLM-based)
  - Supports single or batch CL processing
  - Optional RAG context for improved accuracy
  - Email notification for human verification
  - Outputs JSON with mapped features and confidence
- **Key Commands**:
  - `cl2feature --cl 12345 --features features.json` - Single CL
  - `cl2feature --cl 12345,23456 --features features.json` - Batch
  - `cl2feature --cl 12345 --features features.json --rag /path/to/vectordb` - With RAG
- **Python API**:
  ```python
  from cl2feature import map_cl_to_features
  result = map_cl_to_features(changelist=12345, features=features)
  ```
- **Feature Table**: JSON with `feature_reference_list` (id, name, description.summary, optional fields)
- **Configuration**:
  - `--model`: LLM model (default: bedrock-claude-sonnet-4-6)
  - `--batch-size`: 1-20 features per call
  - `--parallel`: 1-8 concurrent calls
  - `--timeout`: Max seconds per CL
  - `--email`: Notify CL author for verification
  - `--debug`: Include confidence, evidence, reasoning
- **Dependencies**: P4Python, pyyaml, requests, internal nvip/mxai LLM API, optional MRAG vectorDB
- **Auth Required**: P4 (P4PORT, P4USER, P4CLIENT), NVBugs token (optional)

---

### TIER 4: AGENTIC SKILLS & UTILITIES

#### 15. **Agentic Skills** (mmplex) - Debug & Analysis Skills Library
- **Path**: `/home/nv/utils/mmplex/agentic_skills/1.0.23/`
- **Type**: Specialized skills for debug workflows
- **Version**: 1.0.23 (30+ skills)
- **Available Skills** (sample):
  - `bug-analysis` - NVBug analysis
  - `bug-comment`, `bug-fetch`, `bug-report`, `bug-update` - Bug lifecycle
  - `fsdb-active-driver` - FSDB waveform driver analysis
  - `fsdb-signal-transitions` - Signal transition analysis
  - `rtl-signal-trace-kdb`, `rtl-signal-trace-no-kdb` - RTL tracing
  - `rtl-file-discovery` - RTL source discovery
  - `class-reference-finder` - SystemVerilog class lookup
  - `dut-tb-boundary` - DUT-testbench boundary analysis
  - `systemverilog-ast-builder` - AST parsing
  - `uvm-class-hierarchy` - UVM structure analysis
  - `uvm-runtime-analyzer` - UVM runtime info
  - `vdb-coverage` - Coverage database queries
  - `nvenc-auto-debug` - NVENC encoder debug
  - `timing-doctor` - Timing analysis
  - `tree-build` - Source tree analysis
  - `confluence-reader`, `confluence-publisher` - Confluence integration
  - `email-operations`, `send-email` - Email handling
  - `patch-rerun` - Patch application & test rerun
  - `aris-skills` - ARIS-specific tools
  - `mmplex-pptx` - PowerPoint generation
  - And more...
- **Distribution**:
  - `skills.json` - Catalog metadata
  - `setup_mmplex_skills.sh` - Installation script
  - `publish_skill_catalog.py` - Catalog publishing
  - `skill-submit`, `skill-creator` - Skill management tools
- **Auth Required**: Depends on individual skill (P4, NVBugs, Confluence access, etc.)

---

#### 16. **SimAI** - AI-Assisted Simulation
- **Path**: `/home/nv/utils/simai/1.6/`
- **Type**: Simulation framework with AI support
- **Version**: 1.6
- **What It Does**:
  - AI-assisted simulation flows for Synopsys (snps) and Cadence (cdns)
  - VSO.ai integration for bug hunting
  - Simulation-driven AI workflows
- **Components**:
  - Infra/scripts for coverage AI flows
  - Day0-HM (hardware module) flows
  - Phase exploration & bug hunting
- **Auth Required**: Tool-specific (Synopsys/Cadence)

---

#### 17. **Coverage AI** - Coverage Flow Infrastructure
- **Path**: `/home/nv/utils/coverage_ai/1.12/`
- **Type**: Coverage analysis infrastructure
- **Version**: 1.12
- **What It Does**:
  - Support infra for coverage flows (Synopsys & Cadence)
  - VSO.ai integration for bug hunting
  - SimAI flow enhancements
  - LVL file generation for custom test levels
  - LSF driver job support
- **Configuration**: Pass args like LVL_FILE_NAME, -SimAi flag, etc.
- **Auth Required**: Tool-specific

---

#### 18. **RTLOS AI** - Real-Time OS AI Support
- **Path**: `/home/nv/utils/rtlos_ai/0.3.0/`
- **Type**: Domain-specific AI tool
- **Version**: 0.3.0
- **What It Does**:
  - AI support for real-time low-latency OS
  - (Detailed docs pending - appears early-stage)
- **Status**: Repository setup complete, content minimal

---

### TIER 5: AUXILIARY AGENTS & TOOLS

#### 19. **KDS Agent** - Knowledge Discovery
- **Path**: `/home/nv/utils/kds_agent/`
- **Type**: Agent tool
- **What It Does**: Knowledge discovery and search

---

#### 20. **NVault Agent** - Secret Management
- **Path**: `/home/nv/utils/nvault-agent/`
- **Type**: Vault integration agent
- **What It Does**: NVIDIA vault/secret management
- **Source**: Official binaries from Artifactory (`sw-kaizen-data-generic`)
- **Docs**: `//dev/inf/nvault-agent/mainline/README.md`

---

#### 21. **PSC Misc Agent** - Platform Services Tools
- **Path**: `/home/nv/utils/psc_misc_agent/`
- **Type**: Platform services utilities
- **What It Does**: Miscellaneous PSC (Platform Services) agent tools

---

### TIER 6: BUILD & CORE INFRASTRUCTURE

#### 22. **Stepstone** - Advanced Build System
- **Path**: `/home/nv/utils/stepstone/latest/` (symlink to `stepstone-1.80`)
- **Type**: Build orchestration tool
- **Version**: 1.80 (many historical versions: 0.1 through 1.80+)
- **What It Does**: Advanced build system (detailed internals not documented in README)
- **Components**: 
  - bin, build_tools, docs, gui, makepp, nvbuild, nvtools, vcs_stack_prof, verif, web_portal, etc.

---

## Distribution & Discovery Pipeline

### Current State (2026-04):

```
Perforce (Source)      →  NFS Mirror (Runtime)    →  User / IDE
//hw/nv/utils/*            /home/nv/utils/*            Claude Code / Cursor / Codex
(source-of-truth)         (synced automatically)       (manual or via NICC CLI)
```

### Upcoming State (NICC Plugin Support):

```
//hw/nv/utils/         →  /home/nv/utils/        →  NV-CARPS    →  NICC CLI      →  ~/.claude/plugins/
agent_skills/              agent_skills/              Registry         Recommends        (auto-symlinked)
agent_plugins/             agent_plugins/             + Ingests        + Installs
                                                      Skills/Rules     Skills/Plugins
                                                      from P4          to IDEs
```

### Discovery Mechanisms:

1. **Skills**: Marked with `SKILL.md` → P4 → NV-CARPS ingestion → NICC registry
2. **Plugins**: Marked with `plugin.json` + `nvcarps_bundle.yaml` → P4 → NV-CARPS → NICC
3. **Rules**: JSON definitions → P4 → NV-CARPS ingestion → NICC discovery
4. **MCP Servers**: Declared in `nvcarps_bundle.yaml` or `.mcp.json` → manual or NICC (upcoming)

---

## Authentication & Setup Summary

### Token-Based Auth:

| Tool | Token Type | Obtain From | Env Var / Config |
|------|-----------|------|---|
| **ChipNeMo CLI** | serviceToken | `/home/nvmetrics/serviceToken/serviceToken init` | Config or env |
| **NICC CLI** | NVCARPS token | `nicc login` (SSO) | `NVCARPS_TOKEN` or config |
| **Arch-Agent** | NVAUTH_PROXY_TOKEN | NVIDIA SSO | `.bashrc` |
| **CoverScout** | Azure OpenAI API key | Azure portal | `~/.my_token.yml` |
| **Arrow AI** | NVIDIA API key | NVIDIA NIM | `--api-key` flag |
| **CL2Feature** | NVBugs token | NVCARPS team | `~/.my_tokens.yaml` |
| **SmartLog MCP** | (LSF credentials) | NVIDIA LSF | LSF env |

### No Explicit Auth:

- **Carpenter**, **nv-agent**, **Nighthawk**, **WaveRunner** - Config-driven; auth depends on underlying LLM/tool
- **Stepstone**, **RTLOS AI**, **SimAI** - Build/domain-specific (auth is tool-specific)

### Service Token Setup (Recommended):

```bash
/home/nvmetrics/serviceToken/serviceToken init
# Adds token to ~/.nvauth or ~/.serviceToken
# Used by Carpenter venv, Agent Skills, ChipNeMo CLI
```

---

## Installation & Onboarding Paths

### Path 1: Command-Line Tools (Immediate Use)

```bash
# Add to PATH
export PATH=/home/nv/utils/chipnemo-cli/stg:$PATH
export PATH=/home/nv/utils/waverunner/RELEASE/bin:$PATH

# Or use directly
/home/nv/utils/waverunner/RELEASE/bin/waverunner --help
chipnemo ask "What is CUDA?"
```

### Path 2: IDE Integration (Claude Code / Cursor)

```bash
# Install NICC CLI (one-time)
npm install -g nicc-cli --registry=https://artifactory.nvidia.com/artifactory/api/npm/hw-nicc-npm-local/

# Authenticate
nicc login

# Browse skills
nicc skills list

# Install skill to IDE
nicc skills pull <ID> --target claude --location project

# Configure MCPs
nicc mcp --target claude
```

### Path 3: Agent Framework Setup (Carpenter / nv-agent)

```bash
# Carpenter is pre-packaged
/home/nv/utils/carpenter/release/carpenter --config config.yml

# nv-agent requires Python 3.12 + uv
cd /home/nv/utils/nv-agent/0.0.1
uv sync
uv run nv-agent "Your task"
```

### Path 4: Plugin Installation (Athena, Arch-Agent)

```bash
# Athena one-time setup
bash /home/nv/utils/athena-agent/0.1.12/bin/install_athena_agent.sh

# Arch-Agent setup
bash /home/nv/utils/arch-agent/2.1.1/agent/bin/install_arch_agent.sh
export NVAUTH_PROXY_TOKEN='...'

# Load plugin in Claude Code
claude --plugin-dir /home/nv/utils/arch-agent/2.1.1/agent-configs/mentis
```

---

## Key Observa

tions & Recommendations

### Strengths:

1. **Rich Ecosystem**: 50+ tools covering design, debug, coverage, productivity
2. **Standard Patterns**: SKILL.md, plugin.json, MCP configs provide consistency
3. **Centralized Discovery**: NICC CLI + NV-CARPS emerging as single discovery hub
4. **IDE Integration**: Broad support for Claude Code, Cursor, Codex
5. **Source Control**: P4 as source-of-truth, automatic NFS mirroring
6. **Versioning**: Clear versioning strategy (/version/ directories)

### Gaps & Opportunities:

1. **Documentation Fragmentation**: README/SKILL.md quality varies; some tools have minimal docs
2. **NICC Plugins Not Yet Live**: Plugin installation via NICC CLI still coming
3. **MCP Server Discovery**: No unified MCP server registry yet (use `nicc mcp` for now)
4. **Skill Testing**: Limited guidance on testing new skills before publication
5. **Cross-Tool Visibility**: Hard to discover which skills work with which agents
6. **Auth Complexity**: Multiple token types (serviceToken, NVCARPS, NVAUTH_PROXY, Azure OpenAI) — single unified auth would simplify

### Recommendations:

1. **For New AI Tools**: Follow SKILL.md / plugin.json patterns; register with NV-CARPS
2. **For Skill Authors**: Use `@instrument` decorator for observability; test locally via Carpenter
3. **For Users**: Start with `nicc skills list` to discover available capabilities
4. **For Integration**: Prefer MCP servers (standardized protocol) over custom CLI wrappers
5. **For Internal Tools**: Plan for NICC plugin support (declare nvcarps_bundle.yaml now)

---

## File Locations Reference

| Component | NFS Path | P4 Source |
|-----------|----------|-----------|
| ChipNeMo CLI | `/home/nv/utils/chipnemo-cli/stg/`, `X.Y.Z/` | `//hw/nv/utils/chipnemo-cli/` |
| NICC CLI | `/home/nv/utils/nicc-cli/X.Y.Z/` | `//hw/nv/utils/nicc-cli/` |
| Agent Skills | `/home/nv/utils/agent_skills/` | `//hw/nv/utils/agent_skills/` |
| Agent Plugins | `/home/nv/utils/agent_plugins/` | `//hw/nv/utils/agent_plugins/` |
| Carpenter | `/home/nv/utils/carpenter/release/`, `X.Y/` | `//hw/nv/utils/carpenter/` |
| nv-agent | `/home/nv/utils/nv-agent/X.Y.Z/` | (GitLab) |
| Arch-Agent | `/home/nv/utils/arch-agent/X.Y.Z/` | (Internal P4) |
| Athena Agent | `/home/nv/utils/athena-agent/X.Y.Z/` | (Internal P4) |
| Arrow AI | `/home/nv/utils/arrow_ai/X.Y.Z/`, `venv/` | `//hw/nv/utils/arrow_ai/` |
| CoverScout | `/home/nv/utils/mmplex/coverscout/X.Y/` | `//hw/nv/utils/mmplex/` |
| Nighthawk | `/home/nv/utils/mmplex/nighthawk/X.Y.Z/` | `//hw/nv/utils/mmplex/` |
| CL2Feature | `/home/nv/utils/mmplex/cl2feature/X.Y.Z/` | `//hw/nv/utils/mmplex/` |
| Agentic Skills | `/home/nv/utils/mmplex/agentic_skills/X.Y.Z/` | `//hw/nv/utils/mmplex/` |
| WaveRunner | `/home/nv/utils/waverunner/X.Y.Z/`, `RELEASE/` | `//hw/nv/utils/waverunner/` |
| SmartLog MCP | `/home/nv/utils/smartlog_mcp/X.Y.Z/` | (Internal) |
| Stepstone | `/home/nv/utils/stepstone/latest/`, `X.Y/` | `//hw/nv/utils/stepstone/` |
| SimAI | `/home/nv/utils/simai/X.Y/` | `//hw/nv/utils/simai/` |
| Coverage AI | `/home/nv/utils/coverage_ai/X.Y/` | `//hw/nv/utils/coverage_ai/` |

---

## Conclusion

The `/home/nv/utils/` AI tools ecosystem represents a mature, well-organized infrastructure for AI-assisted chip design and verification. The combination of:

- **Modular frameworks** (Carpenter, nv-agent)
- **Centralized skill library** (agent_skills, agentic_skills)
- **Discovery hub** (NICC CLI + NV-CARPS registry)
- **Domain-specific agents** (ChipNeMo, CoverScout, Nighthawk, WaveRunner)
- **IDE integration** (Claude Code, Cursor, Codex plugins)

...creates a powerful ecosystem where engineers can quickly discover, install, and use AI-powered tools for their workflows.

For an NVIDIA engineer building an AI assistant, the recommended starting points are:

1. **For discovery**: `nicc skills list`, `/home/nv/utils/agent_skills/README.md`
2. **For orchestration**: Carpenter (`/home/nv/utils/carpenter/`) or nv-agent (`/home/nv/utils/nv-agent/`)
3. **For domain-specific tasks**: ChipNeMo (Q&A), CoverScout (coverage), Nighthawk (debug), WaveRunner (waveforms)
4. **For documentation**: Individual tool READMEs + SKILL.md files
5. **For integration**: Register skills with NV-CARPS (automatic via P4 check-in)

---

**Report Generated**: April 3, 2026  
**Scope**: Deep research of `/home/nv/utils/` AI/agent/LLM tools  
**Status**: Complete

