# Crexi Workshop Labs — Bedrock & AgentCore for CRE

Hands-on lab code for the Bedrock & AgentCore workshop for Crexi.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/karanvijayakumar/crexi-workshop-labs.git
cd crexi-workshop-labs

# Create virtual environment
python -m venv .venv

# Activate (choose your OS)
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows (cmd)
.venv\Scripts\Activate.ps1      # Windows (PowerShell)

# Install dependencies
pip install -r requirements.txt

# Set AWS credentials
export AWS_ACCESS_KEY_ID=<your-key>           # macOS / Linux
export AWS_SECRET_ACCESS_KEY=<your-secret>    # macOS / Linux
export AWS_SESSION_TOKEN=<your-token>         # macOS / Linux
export AWS_DEFAULT_REGION=us-west-2           # macOS / Linux

set AWS_ACCESS_KEY_ID=<your-key>              # Windows (cmd)
set AWS_SECRET_ACCESS_KEY=<your-secret>       # Windows (cmd)
set AWS_SESSION_TOKEN=<your-token>            # Windows (cmd)
set AWS_DEFAULT_REGION=us-west-2              # Windows (cmd)

# Verify your environment
python setup_check.py
```

## Prerequisites

- Python 3.10–3.12 (3.13+ has issues on macOS)
- AWS CLI v2 configured with credentials
- Bedrock model access enabled (Claude Sonnet 4, Amazon Nova Micro)
- Region: `us-west-2`

## Platform Notes

| | macOS / Linux | Windows (cmd) | Windows (PowerShell) |
|---|---|---|---|
| Activate venv | `source .venv/bin/activate` | `.venv\Scripts\activate` | `.venv\Scripts\Activate.ps1` |
| Set env var | `export KEY=value` | `set KEY=value` | `$env:KEY="value"` |
| Run script | `python hello_bedrock.py` | `python hello_bedrock.py` | `python hello_bedrock.py` |

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

*Workshop by Karan Vijayakumar, Sr. Solutions Architect at zeb — AWS Premier Tier Partner*
