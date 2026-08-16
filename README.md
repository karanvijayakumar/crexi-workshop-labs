# Crexi Workshop Labs — Bedrock & AgentCore for CRE

Hands-on lab code for the Bedrock & AgentCore workshop for Crexi.

## Quick Start

```bash
# Clone the repo
git clone https://zeb-ai@dev.azure.com/zeb-ai/zeb-sa-space/_git/crexi-workshop-labs
cd crexi-workshop-labs

# Install dependencies
pip install -r requirements.txt

# Verify your environment
python setup_check.py
```

## Prerequisites

- Python 3.10+
- AWS CLI v2 configured with credentials
- Bedrock model access enabled (Claude Sonnet, Amazon Nova)
- npm (for AgentCore CLI in Labs 4-5)

## Labs

| Lab | Directory | Description | Time |
|-----|-----------|-------------|------|
| 1 | `lab1_101/` | First Bedrock API call | 20 min |
| 2 | `lab2_extraction/` | Property document extraction | 10 min |
| 3 | `lab3_personalization/` | Buyer/tenant personalization | 10 min |
| 4 | `lab4_memory/` | Deal memory with AgentCore | 15 min |
| 5 | `lab5_multi_agent/` | Multi-agent CRE workflow | 15 min |

## Running Labs

Each lab is a self-contained Python script. Run from the repo root:

```bash
cd lab1_101
python hello_bedrock.py
```

## Cleanup

After the workshop, clean up any AWS resources:

```bash
python cleanup.py
```

## Workshop Site

Follow along at the workshop site for step-by-step instructions and context.

---

*Workshop by Karan Vijayakumar, Sr. Solutions Architect at zeb — AWS Premium Tier Partner*
