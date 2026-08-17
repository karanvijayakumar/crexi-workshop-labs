#!/usr/bin/env python3
"""
Lab 4: Deal Memory with AgentCore Harness
==========================================
Build a stateful CRE deal assistant using AgentCore Harness + Memory.

What you'll learn:
- Creating an AgentCore Harness agent (config-based, no code)
- Enabling memory for multi-turn context
- Session management (same session = remembers, new session = fresh)
- Cleaning up resources

Estimated time: 15 minutes

Prerequisites:
- AgentCore CLI installed: npm install -g @aws/agentcore@preview
- IAM role with Bedrock and AgentCore permissions
"""
import sys
import time
import uuid
import json

sys.path.insert(0, '..')

import boto3


# Configuration
REGION = "us-east-1"

def get_unique_suffix():
    """Generate a short unique suffix from the caller's IAM identity.
    
    This ensures 40 people on the same AWS account don't collide on
    Harness names. Uses the last 6 chars of the IAM username/role session.
    """
    import hashlib
    sts = boto3.client("sts", region_name=REGION)
    identity = sts.get_caller_identity()
    # Use the ARN to derive a short, stable, per-user suffix
    arn = identity["Arn"]
    # Extract the username/session part (e.g., "john.doe" or "Karan.Vijayakumar@zeb.co")
    user_part = arn.split("/")[-1].split("@")[0].replace(".", "")
    # Take first 8 chars to keep harness name under 40 char limit
    return user_part[:8]

USER_SUFFIX = get_unique_suffix()
HARNESS_NAME = f"CrexiDeal_{USER_SUFFIX}"

SYSTEM_PROMPT = """You are a CRE deal analyst for a commercial real estate brokerage. 

Your role:
- Help brokers track active deals and remember property details discussed in conversation
- Recall key terms, pricing, and negotiation history from this session
- Provide financial analysis (cap rates, price per SF, NOI calculations) when asked
- Give concise, professional responses

When asked about a property, recall ALL details previously mentioned in this conversation.
When doing calculations, show your work clearly."""


def get_account_id():
    """Get the current AWS account ID."""
    sts = boto3.client("sts", region_name=REGION)
    return sts.get_caller_identity()["Account"]


def create_execution_role(account_id: str) -> str:
    """Create a least-privilege IAM role for the Harness (or return existing one).
    
    This role is scoped to:
    - Invoke Bedrock models (Anthropic + Amazon families only)
    - AgentCore harness invocation in this account
    - CloudWatch logs for the AgentCore log group only
    """
    iam = boto3.client("iam")
    role_name = "CrexiWorkshopHarnessRole"
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ]
    }
    
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "InvokeModelsOnly",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/anthropic.*",
                    "arn:aws:bedrock:*::foundation-model/amazon.*",
                    f"arn:aws:bedrock:*:{account_id}:inference-profile/*"
                ]
            },
            {
                "Sid": "AgentCoreRuntime",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:InvokeHarness",
                    "bedrock-agentcore:InvokeAgentRuntime",
                    "bedrock-agentcore:ListEvents",
                    "bedrock-agentcore:CreateEvent",
                    "bedrock-agentcore:GetMemory",
                    "bedrock-agentcore:CreateMemory",
                    "bedrock-agentcore:ListSessions",
                    "bedrock-agentcore:GetSession",
                    "bedrock-agentcore:CreateSession",
                    "bedrock-agentcore:DeleteSession"
                ],
                "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:*"
            },
            {
                "Sid": "CloudWatchLogs",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": f"arn:aws:logs:{REGION}:{account_id}:log-group:/aws/bedrock-agentcore/*"
            }
        ]
    }
    
    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Least-privilege execution role for Crexi Workshop AgentCore Harness",
        )
        role_arn = response["Role"]["Arn"]
        print(f"  Created IAM role: {role_name}")
        
        # Attach least-privilege permissions
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="BedrockAgentCoreAccess",
            PolicyDocument=json.dumps(permissions_policy),
        )
        
        # Wait for role propagation
        print("  Waiting for IAM role propagation (10s)...")
        time.sleep(10)
        
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        print(f"  Using existing IAM role: {role_name}")
    
    return role_arn


def create_harness(role_arn: str) -> str:
    """Create an AgentCore Harness. If one with the same name exists, delete and recreate."""
    client = boto3.client("bedrock-agentcore-control", region_name=REGION)
    
    print(f"\n  Creating Harness: {HARNESS_NAME}")
    
    try:
        response = client.create_harness(
            harnessName=HARNESS_NAME,
            executionRoleArn=role_arn,
        )
    except client.exceptions.ConflictException:
        print(f"  ⚠ {HARNESS_NAME} already exists — deleting and recreating...")
        existing = client.list_harnesses()
        for h in existing.get("harnesses", []):
            if h.get("harnessName") == HARNESS_NAME:
                try:
                    client.delete_harness(harnessId=h["harnessId"])
                except Exception:
                    pass
        time.sleep(10)
        response = client.create_harness(
            harnessName=HARNESS_NAME,
            executionRoleArn=role_arn,
        )
    
    harness_data = response.get("harness", response)
    harness_id = harness_data["harnessId"]
    print(f"  Harness ID: {harness_id}")
    return harness_id


def wait_for_ready(harness_id: str, timeout: int = 180):
    """Poll until the Harness is READY."""
    client = boto3.client("bedrock-agentcore-control", region_name=REGION)
    
    print("\n  Waiting for Harness to be READY", end="")
    start = time.time()
    
    while time.time() - start < timeout:
        response = client.get_harness(harnessId=harness_id)
        harness = response.get("harness", response)
        status = harness.get("status", "UNKNOWN")
        
        if status == "READY":
            print(f"\n  ✓ Harness is READY! (took {int(time.time() - start)}s)")
            return harness.get("arn")
        elif "FAILED" in status:
            reason = harness.get("failureReason", "unknown")
            print(f"\n  ✗ Harness creation failed: {status}")
            print(f"    Reason: {reason}")
            raise Exception(f"Harness failed: {status} — {reason}")
        
        print(".", end="", flush=True)
        time.sleep(5)
    
    raise TimeoutError("Harness did not become READY within timeout")


def invoke_harness(harness_arn: str, session_id: str, message: str) -> str:
    """Invoke the Harness and return the response text."""
    client = boto3.client("bedrock-agentcore", region_name=REGION)
    
    response = client.invoke_harness(
        harnessArn=harness_arn,
        runtimeSessionId=session_id,
        messages=[{"role": "user", "content": [{"text": message}]}],
        systemPrompt=[{"text": SYSTEM_PROMPT}],
    )
    
    # Read streaming response
    full_text = ""
    for event in response.get("stream", []):
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            if "text" in delta:
                full_text += delta["text"]
    
    return full_text


def delete_harness(harness_id: str):
    """Clean up the Harness."""
    client = boto3.client("bedrock-agentcore-control", region_name=REGION)
    
    try:
        client.delete_harness(harnessId=harness_id)
        print(f"  ✓ Deleted Harness: {harness_id}")
    except Exception as e:
        print(f"  ⚠ Could not delete Harness: {e}")


def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Lab 4: Deal Memory with AgentCore Harness             ║")
    print("║   Bedrock & AgentCore Workshop for Crexi                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    harness_id = None
    
    try:
        # Setup
        print("[1/6] Setting up IAM role...")
        account_id = get_account_id()
        role_arn = create_execution_role(account_id)
        
        # Create Harness
        print("\n[2/6] Creating AgentCore Harness...")
        harness_id = create_harness(role_arn)
        
        # Wait for READY
        print("\n[3/6] Waiting for deployment...")
        harness_arn = wait_for_ready(harness_id)
        
        # Multi-turn conversation with SAME session
        session_id = str(uuid.uuid4())  # 36 chars with hyphens, meets >=33 requirement
        print(f"\n[4/6] Multi-turn conversation (session: {session_id[:8]}...)")
        print("=" * 60)
        
        conversations = [
            "I'm evaluating a deal for Oakwood Business Park — a 75,000 sqft office complex in Dallas listed at $18.5M. Current NOI is $1.2M with 92% occupancy. The anchor tenant TechVentures has a lease through 2029.",
            "The seller just countered at $17M. What's the new cap rate assuming the same NOI? Is that a better deal for us?",
            "Summarize everything we know about this deal so far — property details, financials, and where we stand in negotiations.",
        ]
        
        for i, msg in enumerate(conversations, 1):
            print(f"\n--- Turn {i} ---")
            print(f"You: {msg}")
            print()
            
            response_text = invoke_harness(harness_arn, session_id, msg)
            print(f"Agent: {response_text}")
        
        # New session — demonstrates memory boundary
        print(f"\n\n[5/6] New session (memory boundary test)")
        print("=" * 60)
        new_session_id = str(uuid.uuid4())
        print(f"New session: {new_session_id[:8]}...")
        
        msg = "What property are we discussing?"
        print(f"\nYou: {msg}")
        response_text = invoke_harness(harness_arn, new_session_id, msg)
        print(f"\nAgent: {response_text}")
        print("\n💡 Notice: The agent has no memory of the previous session!")
        
        # Cleanup
        print(f"\n\n[6/6] Cleaning up...")
        delete_harness(harness_id)
        harness_id = None
        
        print("\n" + "=" * 60)
        print("✅ Lab 4 Complete!")
        print("=" * 60)
        print()
        print("Key takeaways:")
        print("  • AgentCore Harness = config-based agent, no code needed")
        print("  • Same session ID = agent remembers context across turns")
        print("  • New session ID = fresh conversation, no prior memory")
        print("  • In production, use long-term memory for cross-session knowledge")
        print("  • Always clean up Harness resources when done")
        print()
        print("Next: Lab 5 — Multi-Agent CRE Workflow")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  • AccessDeniedException → Check IAM role permissions")
        print("  • Harness not READY → Wait longer or check CloudTrail")
        print("  • InvokeHarness error → Ensure runtimeSessionId >= 33 chars")
        
        if harness_id:
            print(f"\nCleaning up Harness {harness_id}...")
            delete_harness(harness_id)
        raise


if __name__ == "__main__":
    main()
