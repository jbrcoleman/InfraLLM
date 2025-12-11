#!/usr/bin/env python3
"""
Quick diagnostic script to test Anthropic API connection and available models.
"""

import os
import anthropic

# Load API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ ANTHROPIC_API_KEY not set")
    exit(1)

print(f"✓ API Key found: {api_key[:20]}...")
print()

# Test different model names
models_to_try = [
    # Claude Sonnet 4.5 (newest)
    "claude-sonnet-4.5",
    "claude-sonnet-4-5",
    "claude-4-5-sonnet",
    "claude-4.5-sonnet",
    "claude-sonnet-4.5-20250514",
    "claude-sonnet-4-5-20250514",

    # Claude Sonnet 4
    "claude-sonnet-4",
    "claude-sonnet-4.0",
    "claude-4-sonnet",
    "claude-4.0-sonnet",
    "claude-sonnet-4-20250514",
    "claude-sonnet-4.0-20250514",

    # Claude 3.5 Sonnet
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",

    # Claude 3 (what we know works)
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]

client = anthropic.Anthropic(api_key=api_key)

print("Testing models...")
print("=" * 60)

for model in models_to_try:
    try:
        print(f"\nTrying: {model}")
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Hello"}
            ]
        )
        print(f"✓ SUCCESS! Model '{model}' is available")
        print(f"  Response: {response.content[0].text}")
        break  # Stop after first success
    except anthropic.NotFoundError as e:
        print(f"  ❌ Not found: {model}")
    except anthropic.AuthenticationError as e:
        print(f"  ❌ Authentication error: {e}")
        print("  Your API key may not have access to the Messages API")
        break
    except anthropic.PermissionDeniedError as e:
        print(f"  ❌ Permission denied: {e}")
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("\nSDK Info:")
print(f"  anthropic version: {anthropic.__version__}")
