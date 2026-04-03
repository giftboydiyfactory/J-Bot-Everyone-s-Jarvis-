# NVIDIA AI Tool Catalog

## MMPLEX Tools (`/home/nv/utils/mmplex/`, 85 directories)

| Tool | Purpose | Path |
|------|---------|------|
| agentic_skills | 50 agent skills (1.7/day growth) | `agentic_skills/latest/` |
| aris | AI design automation (96% CVDP) | `aris/` |
| nighthawk | 11-step assertion root cause debug | `nighthawk/latest/` |
| coverscout | AI coverage→POR mapping | `coverscout/latest/` |
| cl2feature | CL→feature mapping | `cl2feature/latest/` |
| mxp4db | MySQL P4 analytics + AI summaries | `mxp4db/latest/` |
| waveinsight | FSDB waveform analysis (107 versions) | `waveinsight/latest/` |
| eureka | Bug staleness analysis (3-stage) | `eureka/latest/` |
| mrag | Modular RAG (FAISS+BM25+RRF) | `mrag/latest/` |
| fixme_ai | AI FIXME/TODO triage | `fixme_ai/latest/` |
| docuraven | MAS document generation | `docuraven/latest/` |
| common_bug_repro | NL bug reproduction automation | `common_bug_repro/latest/` |
| p4sum | P4 CL description generator | `p4sum/latest/` |
| mxai (MIAO) | Multi-agent AI assistant | `mxai/latest/` |

## Agent Infrastructure

| Tool | Purpose | Path |
|------|---------|------|
| agent_plugins | CC plugin bundles (Skills+MCP+Hooks+Agents) | `/home/nv/utils/agent_plugins/` |
| agent_skills | 186 ChipNeMo skills | `/home/nv/utils/agent_skills/` |
| arch-agent | Mentis v2.1 (LangGraph, PerfSim) | `/home/nv/utils/arch-agent/` |
| athena-agent | GPU arch sim assistant | `/home/nv/utils/athena-agent/` |
| nv-agent | Carpenter Code successor | `/home/nv/utils/nv-agent/` |
| assertionagent | Assertion debug (Carpenter+Claude Sonnet) | `/home/nv/utils/assertionagent/` |
| ai_telemetry | OTEL→Astra→Datadog | `/home/nv/utils/ai_telemetry/` |
| chipnemo-cli | Terminal copilot access | `/home/nv/utils/chipnemo-cli/` |
| nicc-cli | NVIDIA coding companion CLI | `/home/nv/utils/nicc-cli/` |
| coding_ai_rules | Domain-specific CC/Cursor rules | `/home/nv/utils/coding_ai_rules/` |

## MCP Servers

| Server | Purpose | Status |
|--------|---------|--------|
| NVBugs | Bug queries | Production |
| Confluence | Wiki CRUD | Production |
| SmartLog | Cadence log analysis | Production |
| Speedforce | Architecture FD/IAS docs | Production |
| ChipNemo copilots | Arch/ISA knowledge | Production |
| ARMS | Regression data | Available |
| hwsoc-mcp | SoC tools (Maglev, Jira) | Deployed |
| fcshell_mcp | Fullchip sim shell | Deployed |
| Simlog | UVM log analysis | Deploying |
| Verdi | Waveform analysis | Trial |

## GPU HW Agents

| Agent | Scope | Status |
|-------|-------|--------|
| CDAF | AS2 collision detection | Production |
| CIG | tmake failure triage | Production |
| Mentis | Fullchip DV (FModel/PerfSim) | Production |
| KFA | NVCI auto-rerun | Production |
| R2D2 | SM DV RCA | Beta→CC v3 |
| CLTA | Log triage library | Beta |
| WSAgent | P4 workspace ops | Beta |
