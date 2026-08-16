"""
Bedrock Helper Utilities
=========================
Common utilities for interacting with Amazon Bedrock.
Used across all workshop labs.
"""
import boto3
from typing import Optional


# Default region — change if needed
DEFAULT_REGION = "us-east-1"

# Model IDs — using cross-region inference profiles for availability
MODEL_CLAUDE_SONNET = "us.anthropic.claude-sonnet-4-20250514"
MODEL_NOVA_MICRO = "us.amazon.nova-micro-v1:0"


def get_bedrock_client(region: str = DEFAULT_REGION):
    """Get a Bedrock Runtime client for model invocation."""
    return boto3.client("bedrock-runtime", region_name=region)


def get_agentcore_client(region: str = DEFAULT_REGION):
    """Get an AgentCore data plane client for invoking harnesses."""
    return boto3.client("bedrock-agentcore", region_name=region)


def get_agentcore_control_client(region: str = DEFAULT_REGION):
    """Get an AgentCore control plane client for creating/managing harnesses."""
    return boto3.client("bedrock-agentcore-control", region_name=region)


def converse(
    model_id: str,
    messages: list,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    region: str = DEFAULT_REGION,
) -> dict:
    """
    Call a Bedrock model using the Converse API.
    
    Args:
        model_id: The model ID or inference profile ID
        messages: List of message dicts [{"role": "user", "content": [{"text": "..."}]}]
        system_prompt: Optional system prompt text
        max_tokens: Maximum tokens to generate (ALWAYS set explicitly!)
        temperature: Sampling temperature (0-1)
        region: AWS region
    
    Returns:
        The full Converse API response dict
    """
    client = get_bedrock_client(region)
    
    kwargs = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
        },
    }
    
    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]
    
    response = client.converse(**kwargs)
    return response


def converse_stream(
    model_id: str,
    messages: list,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    region: str = DEFAULT_REGION,
):
    """
    Call a Bedrock model using the Converse API with streaming.
    
    Yields text chunks as they arrive.
    
    Args:
        model_id: The model ID or inference profile ID
        messages: List of message dicts
        system_prompt: Optional system prompt text
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        region: AWS region
    
    Yields:
        Text chunks from the model response
    """
    client = get_bedrock_client(region)
    
    kwargs = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
        },
    }
    
    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]
    
    response = client.converse_stream(**kwargs)
    
    for event in response["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            if "text" in delta:
                yield delta["text"]


def get_response_text(response: dict) -> str:
    """Extract the text content from a Converse API response."""
    output = response.get("output", {})
    message = output.get("message", {})
    content = message.get("content", [])
    
    texts = []
    for block in content:
        if "text" in block:
            texts.append(block["text"])
    
    return "\n".join(texts)


def get_token_usage(response: dict) -> dict:
    """Extract token usage from a Converse API response."""
    usage = response.get("usage", {})
    return {
        "input_tokens": usage.get("inputTokens", 0),
        "output_tokens": usage.get("outputTokens", 0),
        "total_tokens": usage.get("totalTokens", 0),
    }


def print_usage(response: dict):
    """Print token usage in a formatted way."""
    usage = get_token_usage(response)
    print(f"  Tokens — Input: {usage['input_tokens']}, Output: {usage['output_tokens']}, Total: {usage['total_tokens']}")
