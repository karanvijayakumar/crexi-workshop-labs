#!/usr/bin/env python3
"""
Lab 2: Property Document Extraction
=====================================
Extract structured data from a CRE offering memorandum using
prompt engineering and the Converse API.

What you'll learn:
- System prompts for structured JSON extraction
- Handling complex document content
- Comparing extraction quality across models

Estimated time: 10 minutes
"""
import sys
import json
import os

sys.path.insert(0, '..')
from shared.bedrock_helpers import (
    converse, get_response_text, print_usage,
    MODEL_CLAUDE_SONNET, MODEL_NOVA_MICRO
)


# System prompt for extraction
EXTRACTION_PROMPT = """You are a commercial real estate document analyst. 
Your job is to extract structured data from offering memorandums.

Given the document text, extract the following information and return ONLY valid JSON (no markdown, no explanation):

{
  "property_name": "string",
  "address": "full street address",
  "city": "string",
  "state": "string (2-letter code)",
  "property_type": "string",
  "total_sqft": number,
  "year_built": number,
  "asking_price": number,
  "price_per_sqft": number,
  "noi": number,
  "cap_rate": number (as percentage, e.g., 6.5),
  "occupancy_rate": number (as percentage, e.g., 92),
  "tenants": [
    {
      "name": "string",
      "sqft": number,
      "lease_expiration": "string (Month Year)",
      "annual_rent": number,
      "rent_per_sqft": number
    }
  ],
  "highlights": ["string - key investment highlights"],
  "market_vacancy_rate": number (if mentioned)
}

Extract ALL tenants listed. For numeric values, use raw numbers (no commas or dollar signs).
If a field is not available in the document, use null."""


def load_offering_memo():
    """Load the sample offering memorandum."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_offering_memo.txt')
    with open(data_path, 'r') as f:
        return f.read()


def extract_with_model(document: str, model_id: str, model_name: str):
    """Extract structured data using a specific model."""
    print(f"\n{'=' * 60}")
    print(f"Extracting with: {model_name}")
    print(f"Model ID: {model_id}")
    print(f"{'=' * 60}\n")
    
    messages = [
        {
            "role": "user",
            "content": [{"text": f"Extract structured data from this offering memorandum:\n\n{document}"}]
        }
    ]
    
    response = converse(
        model_id=model_id,
        messages=messages,
        system_prompt=EXTRACTION_PROMPT,
        max_tokens=2048,
        temperature=0.1,  # Low temperature for consistent extraction
    )
    
    raw_text = get_response_text(response)
    
    # Parse JSON from response
    try:
        # Handle potential markdown code blocks in response
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0]
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0]
        
        extracted = json.loads(raw_text.strip())
        print("✅ Valid JSON extracted!\n")
        print(json.dumps(extracted, indent=2))
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parsing issue: {e}")
        print("Raw response:")
        print(raw_text[:500])
        extracted = None
    
    print()
    print_usage(response)
    return extracted


def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Lab 2: Property Document Extraction                   ║")
    print("║   Bedrock & AgentCore Workshop for Crexi                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # Load the document
    print("Loading offering memorandum...")
    document = load_offering_memo()
    print(f"  Document length: {len(document)} characters")
    print(f"  First line: {document.split(chr(10))[0].strip()}")
    
    try:
        # Extract with Claude Sonnet
        result = extract_with_model(document, MODEL_CLAUDE_SONNET, "Claude Sonnet")
        
        if result:
            print("\n" + "=" * 60)
            print("EXTRACTION SUMMARY")
            print("=" * 60)
            print(f"  Property: {result.get('property_name')}")
            print(f"  Location: {result.get('address')}, {result.get('city')}, {result.get('state')}")
            print(f"  Type: {result.get('property_type')}")
            print(f"  Size: {result.get('total_sqft'):,} SF")
            print(f"  Price: ${result.get('asking_price'):,.0f} (${result.get('price_per_sqft'):,.2f}/SF)")
            print(f"  Cap Rate: {result.get('cap_rate')}%")
            print(f"  NOI: ${result.get('noi'):,.0f}")
            print(f"  Occupancy: {result.get('occupancy_rate')}%")
            print(f"  Tenants: {len(result.get('tenants', []))}")
            for t in result.get('tenants', []):
                print(f"    • {t['name']} — {t['sqft']:,} SF, expires {t['lease_expiration']}")
        
        print("\n" + "=" * 60)
        print("✅ Lab 2 Complete!")
        print("=" * 60)
        print()
        print("Key takeaways:")
        print("  • System prompts define the extraction schema")
        print("  • Low temperature (0.1) produces consistent output")
        print("  • The Converse API handles the document as context")
        print("  • In production, use Knowledge Bases for large document sets")
        print()
        print("Next: Lab 3 — Tenant/Buyer Personalization")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  • Ensure Claude Sonnet model access is enabled")
        print("  • Check that ../data/sample_offering_memo.txt exists")
        raise


if __name__ == "__main__":
    main()
