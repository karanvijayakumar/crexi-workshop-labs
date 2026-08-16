#!/usr/bin/env python3
"""
Lab 1: Your First Bedrock API Call
===================================
This lab introduces the Converse API — Bedrock's unified interface
for calling any foundation model.

What you'll learn:
- How to call a model using the Converse API
- How to switch models without changing code structure
- How streaming works for real-time responses
- Token usage tracking

Estimated time: 20 minutes
"""
import sys
sys.path.insert(0, '..')
from shared.bedrock_helpers import (
    converse, converse_stream, get_response_text, 
    get_token_usage, print_usage,
    MODEL_CLAUDE_SONNET, MODEL_NOVA_MICRO
)


def step1_call_claude():
    """Step 1: Call Claude Sonnet via the Converse API"""
    print("=" * 60)
    print("STEP 1: Calling Claude Sonnet")
    print("=" * 60)
    print()
    
    messages = [
        {
            "role": "user",
            "content": [{"text": "What are the top 5 factors to consider when evaluating a commercial real estate investment? Be concise."}]
        }
    ]
    
    print(f"Model: {MODEL_CLAUDE_SONNET}")
    print(f"Prompt: {messages[0]['content'][0]['text']}")
    print()
    print("Response:")
    print("-" * 40)
    
    response = converse(
        model_id=MODEL_CLAUDE_SONNET,
        messages=messages,
        max_tokens=512,
    )
    
    print(get_response_text(response))
    print("-" * 40)
    print_usage(response)
    print()


def step2_call_nova():
    """Step 2: Same prompt, different model — demonstrates portability"""
    print("=" * 60)
    print("STEP 2: Same Prompt → Amazon Nova Micro")
    print("=" * 60)
    print()
    
    messages = [
        {
            "role": "user",
            "content": [{"text": "What are the top 5 factors to consider when evaluating a commercial real estate investment? Be concise."}]
        }
    ]
    
    print(f"Model: {MODEL_NOVA_MICRO}")
    print(f"Prompt: (same as Step 1)")
    print()
    print("Response:")
    print("-" * 40)
    
    response = converse(
        model_id=MODEL_NOVA_MICRO,
        messages=messages,
        max_tokens=512,
    )
    
    print(get_response_text(response))
    print("-" * 40)
    print_usage(response)
    print()
    print("💡 Notice: Same code, same prompt, different model — that's the")
    print("   power of the Converse API. Switch models by changing one parameter.")
    print()


def step3_streaming():
    """Step 3: Streaming response for real-time output"""
    print("=" * 60)
    print("STEP 3: Streaming Response")
    print("=" * 60)
    print()
    
    messages = [
        {
            "role": "user",
            "content": [{"text": "Write a brief market analysis for the Dallas, TX commercial office real estate market. Include trends, vacancy rates, and outlook. Keep it to 2 paragraphs."}]
        }
    ]
    
    print(f"Model: {MODEL_CLAUDE_SONNET}")
    print(f"Prompt: Market analysis request (longer response)")
    print()
    print("Streaming response (tokens appear as generated):")
    print("-" * 40)
    
    for chunk in converse_stream(
        model_id=MODEL_CLAUDE_SONNET,
        messages=messages,
        max_tokens=1024,
    ):
        print(chunk, end="", flush=True)
    
    print()
    print("-" * 40)
    print()
    print("💡 Streaming is essential for chat UIs — users see tokens as they")
    print("   generate rather than waiting for the full response.")
    print()


def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Lab 1: Your First Bedrock API Call                    ║")
    print("║   Bedrock & AgentCore Workshop for Crexi                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    try:
        step1_call_claude()
        step2_call_nova()
        step3_streaming()
        
        print("=" * 60)
        print("✅ Lab 1 Complete!")
        print("=" * 60)
        print()
        print("Key takeaways:")
        print("  • The Converse API provides a unified interface for all models")
        print("  • Switch models by changing the model_id parameter")
        print("  • Always set maxTokens explicitly to avoid quota issues")
        print("  • Use streaming for interactive/chat applications")
        print()
        print("Next: Lab 2 — Property Document Extraction")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  • AccessDeniedException → Enable model access in Bedrock console")
        print("  • ThrottlingException → Wait a moment and retry")
        print("  • InvalidEndpointException → Check your AWS region")
        raise


if __name__ == "__main__":
    main()
