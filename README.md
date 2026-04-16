# vCon Super Repository

Welcome to the **vCon Super Repository** — the central hub for all vCon (Virtual Conversation) development projects. This repository tracks all 61 repos in the [vcon-dev](https://github.com/vcon-dev) GitHub organization as git submodules, giving you a single checkout of the entire ecosystem.

## What is vCon?

**vCon** (Virtual Conversation) is an open standard for conversation data that defines how human conversations can be shared, analyzed, and secured. Think of it as "PDFs for human conversations" — a standardized format capturing audio, transcripts, metadata, and analysis.

- IETF spec: [draft-ietf-vcon-vcon-core](https://datatracker.ietf.org/doc/draft-ietf-vcon-vcon-core/)
- Ecosystem overview: [vcon-dev.github.io](https://vcon-dev.github.io)

## Repository Overview

### Core Libraries

| Submodule | Description |
|-----------|-------------|
| [vcon-lib](vcon-lib/) | Python vCon library — reference implementation, vCon 0.4.0 spec |
| [vcon-js](vcon-js/) | TypeScript/JavaScript vCon library — vCon core-02 spec |
| [pydantic-vcon](pydantic-vcon/) | Pydantic v2 models for vCon |

### Server & Infrastructure

| Submodule | Description |
|-----------|-------------|
| [vcon-server](vcon-server/) | The Conserver — main vCon processing and storage platform |
| [vcon-server-cli](vcon-server-cli/) | CLI for managing and interacting with vcon-server |
| [vcon-mcp](vcon-mcp/) | Model Context Protocol server for vCon data |
| [mongo-redis-sync](mongo-redis-sync/) | MongoDB ↔ Redis sync service for vCon storage |
| [vcon-s3-loader](vcon-s3-loader/) | S3 batch loader for vCon files |
| [load_test](load_test/) | Load testing tools for vcon-server |

### Telephony Adapters

| Submodule | Description |
|-----------|-------------|
| [vcon-telephony-adapters](vcon-telephony-adapters/) | Umbrella repo for all telephony adapters |
| [vcon-siprec-adapter](vcon-siprec-adapter/) | SIP Recording (SIPREC) adapter |
| [sippy-conserver-adapter](sippy-conserver-adapter/) | Sippy B2BUA adapter for vcon-server |
| [signalwire_adapter](signalwire_adapter/) | SignalWire telephony adapter |
| [vcon-audio-adapter](vcon-audio-adapter/) | Generic audio file adapter |
| [vcon-fadapter](vcon-fadapter/) | File adapter for batch vCon import |
| [matrix_vcon_emitter](matrix_vcon_emitter/) | Matrix protocol vCon emitter |

### Transcription & AI

| Submodule | Description |
|-----------|-------------|
| [whisper](whisper/) | OpenAI Whisper integration for vCon transcription |
| [TTS](TTS/) | Text-to-speech integration |
| [speechmatics-link](speechmatics-link/) | Speechmatics transcription adapter |
| [vcon-eleven-labs-adapter](vcon-eleven-labs-adapter/) | ElevenLabs TTS adapter |
| [vcon-mac-wtf](vcon-mac-wtf/) | macOS World Transcription Format client |
| [wtf-server](wtf-server/) | WTF (World Transcription Format) server |
| [wtf-transcript-converter](wtf-transcript-converter/) | Converter between WTF and other transcript formats |
| [conversational_search](conversational_search/) | Semantic search over vCon data |
| [langchain](langchain/) | LangChain integration for vCon |
| [conversation-gpt](conversation-gpt/) | *(archived)* ChatGPT over vCon data via Elasticsearch |

### Developer Tools & Utilities

| Submodule | Description |
|-----------|-------------|
| [vcon-admin](vcon-admin/) | Streamlit-based admin dashboard |
| [vcon-app-template](vcon-app-template/) | Starter template for vCon applications |
| [vcon-speckit](vcon-speckit/) | Tools for working with the vCon spec |
| [vcon-desk-viewer](vcon-desk-viewer/) | Desktop vCon viewer application |
| [vscode-vcon-viewer](vscode-vcon-viewer/) | VS Code extension for viewing vCon files |
| [vcon-laptop](vcon-laptop/) | Laptop-local vCon capture tools |
| [scitt-action](scitt-action/) | GitHub Action for SCITT ledger registration |
| [scittles](scittles/) | SCITT utilities for vCon transparency |
| [ietf2vcon](ietf2vcon/) | Convert IETF meeting recordings to vCon |
| [modelcontextprotocol](modelcontextprotocol/) | MCP protocol tools for vCon |
| [vcon-sample-link](vcon-sample-link/) | Sample link resolver for vCon references |
| [vcon-zip](vcon-zip/) | vCon zip/bundle utilities |
| [tadhack-2025](tadhack-2025/) | TADHack 2025 hackathon projects |

### Privacy & Compliance

| Submodule | Description |
|-----------|-------------|
| [vcon-right-to-know](vcon-right-to-know/) | *(archived)* GDPR right-to-access and right-to-forget demo |

### Data & Testing

| Submodule | Description |
|-----------|-------------|
| [vcon-faker](vcon-faker/) | Synthetic vCon generator using OpenAI |
| [fake-vcons](fake-vcons/) | Sample/synthetic vCon files for testing |
| [ietf-meeting-vcons](ietf-meeting-vcons/) | vCons from IETF meeting recordings |
| [vcon-the-hacks](vcon-the-hacks/) | Hackathon and experimental vCon projects |

### IETF Internet-Drafts

| Submodule | Description |
|-----------|-------------|
| [draft-howe-vcon-wtf-extension](draft-howe-vcon-wtf-extension/) | World Transcription Format extension for vCon |
| [draft-howe-vcon-sip-signaling](draft-howe-vcon-sip-signaling/) | SIP signaling extension for vCon |
| [draft-howe-vcon-lawful-basis](draft-howe-vcon-lawful-basis/) | Lawful basis extension for vCon |
| [draft-howe-vcon-lifecycle](draft-howe-vcon-lifecycle/) | vCon lifecycle management draft |
| [draft-howe-sipcore-mcp-extension](draft-howe-sipcore-mcp-extension/) | SIP core MCP extension draft |
| [draft-ietf-vcon-privacy-primer](draft-ietf-vcon-privacy-primer/) | Privacy considerations for vCon |
| [draft-ietf-vcon-vcon-overview](draft-ietf-vcon-vcon-overview/) | vCon ecosystem overview draft |

### Documentation & Info

| Submodule | Description |
|-----------|-------------|
| [docs](docs/) | Developer documentation site (Mintlify) |
| [vcon-docs](vcon-docs/) | Additional vCon documentation |
| [vcon-info](vcon-info/) | Informational resources about vCon |
| [vcon-background-docs](vcon-background-docs/) | Background reading and research |
| [awesome-vcon](awesome-vcon/) | Curated list of vCon tools and resources |
| [vcon-dev.github.io](vcon-dev.github.io/) | vcon-dev GitHub Pages site |

### Packages & Distribution

| Submodule | Description |
|-----------|-------------|
| [homebrew-tap](homebrew-tap/) | Homebrew tap — index of vCon Homebrew formulas |
| [homebrew-vcon](homebrew-vcon/) | Homebrew formula for the vCon CLI tools |

### External Forks

| Submodule | Description |
|-----------|-------------|
| [pyVoIP](pyVoIP/) | Fork of pyVoIP with vCon integration |
| [rd-apmm-python-lib-rtp](rd-apmm-python-lib-rtp/) | Fork of RTP library for vCon audio |

## Quick Setup

Clone with all submodules:

```bash
git clone --recursive https://github.com/vcon-dev/vcon.git
cd vcon
```

Or initialize submodules in an existing clone:

```bash
git submodule update --init --recursive
```

Update all submodules to latest:

```bash
git submodule update --remote --recursive
```

Update a single submodule:

```bash
git submodule update --remote vcon-server
```

## Tools

The [`tools/`](tools/) directory contains local utilities:

- `update-submodules.sh` — shell script to pull all submodules to latest
- `postgres_schema.sql` — PostgreSQL schema for vcon-server storage
- `embed_streamlit_demo.html` — iframe embed snippet for Streamlit app demos

## Assets

The [`assets/docs/`](assets/docs/) directory contains standalone reference documents:

- *What is a vCon* (PDF)
- *vCons: an Open Standard for Conversation Data* (PDF)
- *Communications Design* diagram

## Automated Updates

A GitHub Action runs every Monday at 9 AM UTC, updates all submodules to their latest commits, and opens a pull request with the changes for review.

## Resources

- [IETF vCon datatracker](https://datatracker.ietf.org/doc/draft-ietf-vcon-vcon-core/)
- [vcon-dev organization](https://github.com/vcon-dev)
- [Developer docs](https://vcon-dev.github.io)
- [Community discussions](https://github.com/vcon-dev/vcon/discussions)

## License

MIT — see [LICENSE](LICENSE) for details.
