# 🏠 vCon Super Repository

Welcome to the **vCon Super Repository** - the central hub for all vCon (Virtual Conversation) development projects. This repository serves as a parent repository that tracks and manages all major vCon-related projects, making it easy to stay up-to-date with the latest developments across the entire vCon ecosystem.

## 🎯 What is vCon?

**vCon** (Virtual Conversation) is an open standard for conversation data that defines how human conversations can be shared, analyzed, and secured. Think of it as "PDFs for human conversations" - a standardized format that captures all aspects of conversations including audio, transcripts, metadata, and analysis.

The vCon ecosystem consists of two primary components:
- **The Python vCon Package**: For constructing and operating on vCon objects
- **The Conserver**: A domain-specific data platform for storing, managing, and manipulating vCon objects

## 📚 Repository Overview

This super repository contains the following projects, each serving a specific role in the vCon ecosystem:

### 🐰 Core Infrastructure

#### [vcon-server](vcon-server/) - **Main vCon Server**
The heart of the vCon ecosystem - a powerful conversation processing and storage system that enables advanced analysis and management of conversation data.

**Key Features:**
- Flexible processing pipeline with multiple storage backends (PostgreSQL, S3, Elasticsearch, Milvus)
- Real-time conversation processing and analysis
- Webhook integrations and API endpoints
- Docker-based deployment with automated installation
- Support for dynamic module installation

**Quick Start:**
```bash
# Automated installation
curl -O https://raw.githubusercontent.com/vcon-dev/vcon-server/main/scripts/install_conserver.sh
chmod +x install_conserver.sh
sudo ./install_conserver.sh --domain your-domain.com --email your-email@example.com
```

### 🛠️ Development & Testing Tools

#### [vcon-faker](vcon-faker/) - **Synthetic Data Generator**
Generates realistic fake conversations for testing and development purposes using OpenAI's language models and text-to-speech capabilities.

**Key Features:**
- AI-powered conversation generation with customizable prompts
- Audio synthesis for each conversation line
- vCon file creation with metadata and audio URLs
- S3 integration for storage
- Streamlit web interface for easy management

**Quick Start:**
```bash
cd vcon-faker
pip install -r requirements.txt
streamlit run main.py
```

#### [fake-vcons](fake-vcons/) - **Sample vCon Data**
A collection of synthetic vCon files created using vcon-faker, perfect for testing, demos, and development.

**Use Cases:**
- Training customer service agents
- Testing conversational AI systems
- Demonstrating vCon capabilities
- Development and testing of vCon processing applications

### 🔧 Administrative Tools

#### [vcon-admin](vcon-admin/) - **Administrative Dashboard**
A comprehensive Streamlit-based administrative toolkit for vCon developers, testers, and operators.

**Key Features:**
- Import/export vCons from various storages (Redis, S3, JSONL, JSON, MongoDB)
- Real-time system monitoring and Docker container management
- Elasticsearch and vector database integration
- ChatGPT prompt testing on vCon subsets
- Data analysis and visualization tools
- vCon inspector and workbench functionality

**Quick Start:**
```bash
cd vcon-admin
docker compose up -d
# Visit http://localhost:8501
```

### 🤖 AI & Analytics

#### [conversation-gpt](conversation-gpt/) - **AI Conversation Assistant**
A Streamlit app that uses OpenAI's assistant API and Elasticsearch to enable ChatGPT over conversational data.

**Key Features:**
- Direct conversation analysis with GPT
- Conversation identification and filtering
- Thread management with vCon tracking
- Export capabilities for analyzed conversations
- Integration with vCon format for seamless data flow

**Use Cases:**
- Writing follow-up emails based on conversations
- Analyzing customer interactions
- Extracting insights from conversation data
- Automated conversation processing

### 🔒 Privacy & Compliance

#### [vcon-right-to-know](vcon-right-to-know/) - **Privacy Compliance Tool**
A Python demo application that implements GDPR compliance features for vCon data, specifically the Right to Access and Right to be Forgotten.

**Key Features:**
- Customer data access requests
- Data deletion requests
- MongoDB-based vCon search functionality
- Email and phone number matching
- Privacy law compliance demonstration

**Quick Start:**
```bash
cd vcon-right-to-know
pip install -r requirements.txt
streamlit run right-to-know.py
```

### 🛠️ Utilities

#### [tools/](tools/) - **Development Utilities**
- `update-submodules.sh`: Automated script for updating all submodules
- `postgres_schema.sql`: Database schema for PostgreSQL storage
- `embed_streamlit_demo.html`: Demo embedding for Streamlit applications

## 🚀 Getting Started

### Prerequisites
- Git
- Docker and Docker Compose (for most components)
- Python 3.12+ (for development)
- OpenAI API key (for AI features)
- AWS credentials (for S3 storage)

### Quick Setup

1. **Clone the super repository:**
   ```bash
   git clone --recursive https://github.com/vcon-dev/vcon.git
   cd vcon
   ```

2. **Initialize all submodules:**
   ```bash
   git submodule update --init --recursive
   ```

3. **Choose your starting point:**
   - For **production deployment**: Start with `vcon-server`
   - For **development and testing**: Use `vcon-faker` and `fake-vcons`
   - For **administration**: Deploy `vcon-admin`
   - For **AI integration**: Explore `conversation-gpt`

## 🔄 Managing Submodules

This repository uses Git submodules to track all the individual projects. The submodules are automatically updated to ensure you have the latest versions of all vCon projects.

### Automated Updates

A GitHub Action automatically checks for updates in all submodules every Monday at 9 AM UTC. When updates are available, it creates a pull request with the changes for your review.

### Manual Updates

You can also update submodules manually using the provided script:

```bash
./tools/update-submodules.sh
```

Or use standard git commands:

```bash
# Update all submodules to latest versions
git submodule update --remote --recursive

# Commit the updates
git add .
git commit -m "chore: update submodules to latest versions"
git push
```

### Working with Submodules

**Initial Setup**: If you're cloning this repository for the first time:
```bash
git clone --recursive https://github.com/vcon-dev/vcon.git
```

**Existing Clone**: If you already have the repository cloned:
```bash
git submodule update --init --recursive
```

**Updating a Specific Submodule**: To update just one submodule:
```bash
git submodule update --remote <submodule-name>
```

## 📖 Documentation & Resources

### Presentations & Whitepapers
- [Birds of a Feather session at IETF 116, Yokohama](https://youtu.be/EF2OMbo6Qj4)
- [Presentation at TADSummit](https://youtu.be/ZBRJ6FcVblc)
- [Presentation at IETF](https://youtu.be/dJsPzZITr_g?t=243)
- [Presentation at IIT](https://youtu.be/s-pjgpBOQqc)

### Technical Documentation
- [IETF draft proposal](https://datatracker.ietf.org/doc/html/draft-petrie-vcon-01)
- [White paper](https://docs.google.com/document/d/1TV8j29knVoOJcZvMHVFDaan0OVfraH_-nrS5gW4-DEA/edit?usp=sharing)
- [vCon Library Quick Start for Python](https://github.com/vcon-dev/vcon/wiki/Library-Quick-Start)

### Keynote & Blog Posts
- [Keynote proposal for vCons](https://blog.tadsummit.com/2021/12/08/strolid-keynote-vcons/)

## 🧪 Testing

### Testing the vCon Package
```bash
pytest -v -rP tests
pytest -v -rP tests/test_vcon_cli.py
```

### Testing the Conserver
```bash
cd vcon-server
source .env
pytest -v -rP tests
```

## 🤝 Contributing

Each submodule has its own contribution guidelines. Please refer to the individual repository READMEs for specific contribution instructions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Use the GitHub Issues page of the specific submodule
- **Discussions**: Join the [vCon community discussions](https://github.com/vcon-dev/vcon/discussions)
- **Documentation**: Check the individual repository READMEs for detailed documentation

---

**🎉 Welcome to the vCon ecosystem! Start exploring the repositories above to build powerful conversation-based applications.**

