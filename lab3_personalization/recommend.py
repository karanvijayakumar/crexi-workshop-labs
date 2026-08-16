#!/usr/bin/env python3
"""
Lab 3: Tenant & Buyer Personalization
=======================================
Generate personalized property recommendations for different buyer profiles.

What you'll learn:
- System prompts as persona/behavior control
- Structuring complex context for the model
- How different prompts produce different recommendation styles

Estimated time: 10 minutes
"""
import sys
import json
import os

sys.path.insert(0, '..')
from shared.bedrock_helpers import (
    converse, get_response_text, print_usage,
    MODEL_CLAUDE_SONNET
)


RECOMMENDATION_PROMPT = """You are a senior CRE investment advisor at a top commercial real estate brokerage.

Your role is to analyze a buyer's investment criteria and recommend the top 3 properties from the available listings that best match their strategy.

For each recommendation:
1. State the property name and key metrics (price, cap rate, sqft, occupancy)
2. Explain specifically WHY it matches the buyer's criteria (reference their stated preferences)
3. Note any risks or considerations
4. Give a confidence score (High/Medium/Low) for the match

Format your response clearly with numbered recommendations.
Be specific — reference actual numbers from both the buyer's criteria and the property data."""


def load_data():
    """Load property listings and buyer profiles."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    with open(os.path.join(data_dir, 'property_listings.json'), 'r') as f:
        listings = json.load(f)
    
    with open(os.path.join(data_dir, 'buyer_profiles.json'), 'r') as f:
        buyers = json.load(f)
    
    return listings, buyers


def recommend_for_buyer(buyer: dict, listings: list):
    """Generate recommendations for a single buyer profile."""
    print(f"\n{'=' * 60}")
    print(f"BUYER: {buyer['name']}")
    print(f"Type: {buyer['type']} | Strategy: {buyer['strategy']}")
    print(f"Budget: ${buyer['preferences']['budget_min']:,.0f} - ${buyer['preferences']['budget_max']:,.0f}")
    print(f"Target: {', '.join(buyer['preferences']['property_types'])}")
    print(f"Priority: {buyer['preferences']['priority']}")
    print(f"{'=' * 60}")
    
    # Build the context message
    user_message = f"""BUYER PROFILE:
Name: {buyer['name']}
Type: {buyer['type']}
Strategy: {buyer['strategy']}
Budget: ${buyer['preferences']['budget_min']:,.0f} - ${buyer['preferences']['budget_max']:,.0f}
Target Property Types: {', '.join(buyer['preferences']['property_types'])}
Target Markets: {', '.join(buyer['preferences']['target_markets'])}
Minimum Cap Rate: {buyer['preferences']['target_cap_rate_min']}%
Priority: {buyer['preferences']['priority']}

AVAILABLE PROPERTIES:
{json.dumps(listings, indent=2)}

Based on this buyer's specific criteria, recommend the top 3 properties and explain why each is a strong match."""
    
    messages = [{"role": "user", "content": [{"text": user_message}]}]
    
    response = converse(
        model_id=MODEL_CLAUDE_SONNET,
        messages=messages,
        system_prompt=RECOMMENDATION_PROMPT,
        max_tokens=1500,
        temperature=0.3,
    )
    
    print()
    print(get_response_text(response))
    print()
    print_usage(response)


def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Lab 3: Tenant & Buyer Personalization                 ║")
    print("║   Bedrock & AgentCore Workshop for Crexi                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    try:
        # Load data
        print("Loading property listings and buyer profiles...")
        listings, buyers = load_data()
        print(f"  {len(listings)} properties loaded")
        print(f"  {len(buyers)} buyer profiles loaded")
        
        # Generate recommendations for each buyer
        for buyer in buyers:
            recommend_for_buyer(buyer, listings)
        
        print("\n" + "=" * 60)
        print("✅ Lab 3 Complete!")
        print("=" * 60)
        print()
        print("Key takeaways:")
        print("  • System prompts control recommendation style and format")
        print("  • Structured context (JSON) helps the model reason precisely")
        print("  • Different buyer profiles get different recommendations")
        print("  • In production, use Knowledge Bases for larger catalogs")
        print("  • Temperature 0.3 balances creativity with consistency")
        print()
        print("Next: Lab 4 — Deal Memory with AgentCore")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
