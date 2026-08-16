#!/usr/bin/env python3
"""
Lab 5: Multi-Agent CRE Workflow
================================
Orchestrate specialized agents for comprehensive property evaluation.

What you'll learn:
- Creating multiple specialized Harness agents
- Agent-to-agent delegation pattern
- Synthesizing outputs from multiple AI perspectives
- Multi-agent cleanup

Estimated time: 15 minutes

Architecture:
  Property Input → Market Analyst Agent → ┐
                 → Underwriter Agent    → ├→ Orchestrator → Final Recommendation
"""
import sys
import time
import uuid
import json

sys.path.insert(0, '..')

import boto3


# Configuration
REGION = "us-east-1"
TIMESTAMP = int(time.time()) % 10000

# Agent definitions
AGENTS = {
    "market_analyst": {
        "name": f"CrexiMarketAnalyst{TIMESTAMP}",
        "system_prompt": """You are a CRE market analyst specializing in commercial real estate market research.

When given a property, analyze:
1. Market conditions in the submarket (supply/demand, vacancy trends)
2. Comparable sales and rental rates
3. Location strengths and weaknesses
4. Growth trajectory and demographic trends
5. Risk factors (oversupply, economic sensitivity)

Be specific with data points. Provide a market rating: Strong / Moderate / Weak.
Keep your analysis to 3-4 concise paragraphs."""
    },
    "underwriter": {
        "name": f"CrexiUnderwriter{TIMESTAMP}",
        "system_prompt": """You are a CRE underwriter specializing in investment analysis.

When given a property, analyze:
1. Cap rate relative to market (is it priced fairly?)
2. NOI sustainability and growth potential
3. Rent roll risk (tenant concentration, lease expirations)
4. Debt service analysis (assume 65% LTV, 6.5% rate, 25-year amort)
5. Value-add potential (vacancy fill, rent bumps, repositioning)

Calculate key metrics: DSCR, cash-on-cash return, price per SF vs replacement cost.
Provide a recommendation: Strong Buy / Buy / Hold / Pass.
Keep your analysis to 3-4 concise paragraphs with specific numbers."""
    },
    "orchestrator": {
        "name": f"CrexiOrchestrator{TIMESTAMP}",
        "system_prompt": """You are a senior CRE investment director at a major real estate investment firm.

You receive market analysis and underwriting analysis from your team. Your job is to:
1. Synthesize both perspectives into a unified view
2. Identify where the analysts agree and disagree
3. Weigh the risks against the opportunity
4. Provide a final investment recommendation with conviction level (High/Medium/Low)
5. Suggest key due diligence items before proceeding

Be decisive. Executives need a clear recommendation, not equivocation.
Keep your recommendation to 3-4 concise paragraphs."""
    }
}

# Property to evaluate
PROPERTY_BRIEF = """PROPERTY FOR EVALUATION:

Sunset Plaza — Retail Center
Location: 2200 Commerce Drive, Scottsdale, AZ
Size: 45,000 SF retail center
Asking Price: $12,000,000 ($267/SF)
NOI: $780,000
Cap Rate: 6.5%
Occupancy: 85% (6,750 SF vacant)
Year Built: 2005
Anchor Tenant: Southwest Fitness (15,000 SF) — lease expires in 18 months
Other Tenants: Mix of local restaurants and service retail
Parking: 5.0 spaces per 1,000 SF
Location: High-traffic corridor in affluent Scottsdale area
Demographics: Average HHI $145,000 within 3 miles"""


def get_account_id():
    """Get the current AWS account ID."""
    sts = boto3.client("sts", region_name=REGION)
    return sts.get_caller_identity()["Account"]


def get_role_arn(account_id: str) -> str:
    """Get or create the execution role."""
    iam = boto3.client("iam")
    role_name = "CrexiWorkshopHarnessRole"
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {"aws:SourceAccount": account_id},
                "ArnLike": {"aws:SourceArn": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:harness/*"}
            }
        }]
    }
    
    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for Crexi Workshop AgentCore Harness",
        )
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="BedrockAgentCoreAccess",
            PolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {"Effect": "Allow", "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"], "Resource": "*"},
                    {"Effect": "Allow", "Action": ["bedrock-agentcore:*"], "Resource": "*"}
                ]
            })
        )
        print("  Created IAM role, waiting for propagation (10s)...")
        time.sleep(10)
    except iam.exceptions.EntityAlreadyExistsException:
        pass
    
    return f"arn:aws:iam::{account_id}:role/{role_name}"


def create_agent(control_client, agent_key: str, role_arn: str) -> str:
    """Create a single Harness agent."""
    agent_config = AGENTS[agent_key]
    
    response = control_client.create_harness(
        harnessName=agent_config["name"],
        executionRoleArn=role_arn,
    )
    
    harness_id = response["harnessId"]
    print(f"  Created {agent_key}: {agent_config['name']} (ID: {harness_id})")
    return harness_id


def wait_all_ready(control_client, harness_ids: dict, timeout: int = 180):
    """Wait for all Harness agents to be READY."""
    print("\n  Waiting for all agents to be READY", end="")
    start = time.time()
    arns = {}
    
    while time.time() - start < timeout:
        all_ready = True
        for key, hid in harness_ids.items():
            if key in arns:
                continue
            response = control_client.get_harness(harnessId=hid)
            status = response.get("status", "UNKNOWN")
            if status == "READY":
                arns[key] = response.get("harnessArn")
            elif "FAILED" in status:
                raise Exception(f"{key} failed: {status}")
            else:
                all_ready = False
        
        if all_ready or len(arns) == len(harness_ids):
            print(f"\n  ✓ All agents READY! (took {int(time.time() - start)}s)")
            return arns
        
        print(".", end="", flush=True)
        time.sleep(5)
    
    raise TimeoutError("Not all agents became READY within timeout")


def invoke_agent(data_client, harness_arn: str, system_prompt: str, message: str) -> str:
    """Invoke a Harness agent and return response text."""
    session_id = str(uuid.uuid4())
    
    response = data_client.invoke_harness(
        harnessArn=harness_arn,
        runtimeSessionId=session_id,
        messages=[{"role": "user", "content": [{"text": message}]}],
        systemPrompt=[{"text": system_prompt}],
    )
    
    full_text = ""
    for event in response.get("stream", []):
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            if "text" in delta:
                full_text += delta["text"]
    
    return full_text


def cleanup_agents(control_client, harness_ids: dict):
    """Delete all Harness agents."""
    for key, hid in harness_ids.items():
        try:
            control_client.delete_harness(harnessId=hid)
            print(f"  ✓ Deleted {key}: {hid}")
        except Exception as e:
            print(f"  ⚠ Could not delete {key}: {e}")


def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Lab 5: Multi-Agent CRE Workflow                       ║")
    print("║   Bedrock & AgentCore Workshop for Crexi                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    control_client = boto3.client("bedrock-agentcore-control", region_name=REGION)
    data_client = boto3.client("bedrock-agentcore", region_name=REGION)
    harness_ids = {}
    
    try:
        # Setup
        print("[1/7] Setting up IAM role...")
        account_id = get_account_id()
        role_arn = get_role_arn(account_id)
        
        # Create all agents
        print("\n[2/7] Creating specialized agents...")
        for agent_key in AGENTS:
            harness_ids[agent_key] = create_agent(control_client, agent_key, role_arn)
        
        # Wait for all READY
        print("\n[3/7] Waiting for deployment...")
        arns = wait_all_ready(control_client, harness_ids)
        
        # Step 1: Market Analysis
        print(f"\n[4/7] Market Analyst evaluating property...")
        print("=" * 60)
        print("📊 MARKET ANALYSIS")
        print("=" * 60)
        
        market_analysis = invoke_agent(
            data_client,
            arns["market_analyst"],
            AGENTS["market_analyst"]["system_prompt"],
            PROPERTY_BRIEF
        )
        print(market_analysis)
        
        # Step 2: Underwriting
        print(f"\n[5/7] Underwriter evaluating financials...")
        print("=" * 60)
        print("💰 UNDERWRITING ANALYSIS")
        print("=" * 60)
        
        underwriting = invoke_agent(
            data_client,
            arns["underwriter"],
            AGENTS["underwriter"]["system_prompt"],
            PROPERTY_BRIEF
        )
        print(underwriting)
        
        # Step 3: Orchestrator synthesizes
        print(f"\n[6/7] Investment Director synthesizing recommendation...")
        print("=" * 60)
        print("🎯 FINAL INVESTMENT RECOMMENDATION")
        print("=" * 60)
        
        orchestrator_input = f"""{PROPERTY_BRIEF}

---

MARKET ANALYSIS (from your market analyst):
{market_analysis}

---

UNDERWRITING ANALYSIS (from your underwriter):
{underwriting}

---

Based on both analyses above, provide your final investment recommendation."""
        
        recommendation = invoke_agent(
            data_client,
            arns["orchestrator"],
            AGENTS["orchestrator"]["system_prompt"],
            orchestrator_input
        )
        print(recommendation)
        
        # Cleanup
        print(f"\n\n[7/7] Cleaning up agents...")
        cleanup_agents(control_client, harness_ids)
        harness_ids = {}
        
        print("\n" + "=" * 60)
        print("✅ Lab 5 Complete!")
        print("=" * 60)
        print()
        print("Key takeaways:")
        print("  • Specialized agents produce focused, expert analysis")
        print("  • Orchestration pattern: decompose → analyze → synthesize")
        print("  • Each agent has its own system prompt defining its expertise")
        print("  • In production: use Gateway for real data, A2A for direct communication")
        print("  • Multi-agent systems scale human expertise across deal volume")
        print()
        print("🎉 Workshop Complete! Head to the Cleanup & Next Steps page.")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  • If agents fail to create, check IAM role permissions")
        print("  • If invocation fails, ensure Harness is READY")
        print("  • Timeout? AgentCore may be under load — try again")
        
        if harness_ids:
            print("\nCleaning up...")
            cleanup_agents(control_client, harness_ids)
        raise


if __name__ == "__main__":
    main()
