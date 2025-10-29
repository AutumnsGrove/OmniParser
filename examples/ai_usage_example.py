#!/usr/bin/env python3
"""
AI-Powered Document Parsing Examples for OmniParser.

This script demonstrates how to:
1. Set up secrets and configuration
2. Use different AI providers (Anthropic, OpenAI, Ollama, LM Studio)
3. Parse documents with AI-powered features:
   - Auto-tagging
   - Summarization
   - Image analysis and description
   - Quality scoring

Prerequisites:
    1. Copy secrets_template.json to secrets.json and add your API keys
    2. (Optional) Copy config_template.json to config.json to customize settings
    3. Install AI dependencies: uv sync --extra ai

Examples:
    # Use Anthropic Claude
    python examples/ai_usage_example.py --provider anthropic --file book.epub

    # Use local Ollama
    python examples/ai_usage_example.py --provider ollama --file book.epub

    # Full AI pipeline with all features
    python examples/ai_usage_example.py --provider anthropic --file book.epub --all-features
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import json
from omniparser import parse_document
from omniparser.utils.config import load_config, get_ai_options
from omniparser.utils.secrets import load_secrets

# AI processors (optional imports - will fail gracefully if not installed)
try:
    from omniparser.processors.ai_tagger import generate_tags
    from omniparser.processors.ai_summarizer import summarize_document
    from omniparser.processors.ai_image_describer import describe_document_images
    from omniparser.processors.ai_quality import score_quality
    from omniparser.processors.ai_image_analyzer import analyze_image

    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  AI features not available. Install with: uv sync --extra ai")
    print(f"   Error: {e}")
    AI_AVAILABLE = False


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_basic_parsing(file_path: Path) -> None:
    """Example 1: Basic document parsing without AI."""
    print_section("Example 1: Basic Document Parsing (No AI)")

    print(f"Parsing: {file_path}")
    doc = parse_document(file_path)

    print(f"✅ Parsed successfully!")
    print(f"   Title: {doc.metadata.title}")
    print(f"   Author: {doc.metadata.author}")
    print(f"   Chapters: {len(doc.chapters)}")
    print(f"   Total words: {sum(len(ch.content.split()) for ch in doc.chapters)}")
    print(f"   Images: {len(doc.images)}")

    return doc


def example_ai_tagging(doc, provider: str) -> list:
    """Example 2: Auto-generate tags using AI."""
    if not AI_AVAILABLE:
        print("❌ AI features not installed. Skipping tagging example.")
        return []

    print_section(f"Example 2: AI-Powered Auto-Tagging ({provider})")

    # Load config and get AI options
    config = load_config()
    ai_options = get_ai_options(provider, config)

    print(f"Generating tags with {provider}...")
    print(f"   Model: {ai_options.get('model')}")

    try:
        tags = generate_tags(doc, max_tags=10, ai_options=ai_options)
        print(f"✅ Generated {len(tags)} tags:")
        for tag in tags:
            print(f"   - {tag}")
        return tags
    except Exception as e:
        print(f"❌ Tagging failed: {e}")
        return []


def example_ai_summarization(doc, provider: str) -> dict:
    """Example 3: Generate summaries using AI."""
    if not AI_AVAILABLE:
        print("❌ AI features not installed. Skipping summarization example.")
        return {}

    print_section(f"Example 3: AI-Powered Summarization ({provider})")

    # Load config and get AI options
    config = load_config()
    ai_options = get_ai_options(provider, config)

    results = {}

    # Concise summary
    print("Generating concise summary...")
    try:
        concise = summarize_document(doc, style="concise", ai_options=ai_options)
        print(f"✅ Concise Summary ({len(concise.split())} words):")
        print(f"   {concise}\n")
        results["concise"] = concise
    except Exception as e:
        print(f"❌ Concise summary failed: {e}\n")

    # Bullet point summary
    print("Generating bullet point summary...")
    try:
        bullets = summarize_document(doc, style="bullet", ai_options=ai_options)
        print(f"✅ Bullet Points:")
        print(f"{bullets}\n")
        results["bullets"] = bullets
    except Exception as e:
        print(f"❌ Bullet summary failed: {e}\n")

    return results


def example_ai_image_description(doc, provider: str) -> dict:
    """Example 4: Describe images using AI vision models."""
    if not AI_AVAILABLE:
        print("❌ AI features not installed. Skipping image description example.")
        return {}

    print_section(f"Example 4: AI-Powered Image Description ({provider})")

    if not doc.images:
        print("   No images found in document.")
        return {}

    # Load config and get AI options
    config = load_config()
    ai_options = get_ai_options(provider, config)

    print(f"Describing {len(doc.images)} images with {provider}...")
    print(f"   Model: {ai_options.get('model')}")

    try:
        descriptions = describe_document_images(doc, ai_options=ai_options)
        print(f"✅ Generated descriptions for {len(descriptions)} images:")
        for img_id, description in list(descriptions.items())[:3]:  # Show first 3
            print(f"\n   Image: {img_id}")
            print(f"   Description: {description}")
        if len(descriptions) > 3:
            print(f"\n   ... and {len(descriptions) - 3} more")
        return descriptions
    except Exception as e:
        print(f"❌ Image description failed: {e}")
        return {}


def example_ai_quality_scoring(doc, provider: str) -> dict:
    """Example 5: Assess document quality using AI."""
    if not AI_AVAILABLE:
        print("❌ AI features not installed. Skipping quality scoring example.")
        return {}

    print_section(f"Example 5: AI-Powered Quality Scoring ({provider})")

    # Load config and get AI options
    config = load_config()
    ai_options = get_ai_options(provider, config)

    print(f"Analyzing quality with {provider}...")
    try:
        quality = score_quality(doc, ai_options=ai_options)
        print(f"✅ Quality Assessment:")
        print(f"   Overall Score: {quality['overall_score']}/100")
        print(f"   Readability: {quality['readability']}/100")
        print(f"   Structure: {quality['structure']}/100")
        print(f"   Completeness: {quality['completeness']}/100")
        print(f"   Coherence: {quality['coherence']}/100")

        if quality.get("strengths"):
            print(f"\n   Strengths:")
            for strength in quality["strengths"]:
                print(f"   ✓ {strength}")

        if quality.get("suggestions"):
            print(f"\n   Suggestions:")
            for suggestion in quality["suggestions"]:
                print(f"   • {suggestion}")

        return quality
    except Exception as e:
        print(f"❌ Quality scoring failed: {e}")
        return {}


def example_provider_comparison(doc) -> None:
    """Example 6: Compare different AI providers."""
    if not AI_AVAILABLE:
        print("❌ AI features not installed. Skipping provider comparison.")
        return

    print_section("Example 6: Provider Comparison")

    config = load_config()
    providers = ["anthropic", "openai", "ollama"]

    print("Generating concise summaries with different providers...\n")

    results = {}
    for provider in providers:
        print(f"Testing {provider}...")
        try:
            ai_options = get_ai_options(provider, config)
            summary = summarize_document(
                doc, style="concise", max_length=100, ai_options=ai_options
            )
            results[provider] = {
                "success": True,
                "summary": summary,
                "model": ai_options.get("model"),
            }
            print(f"   ✅ Success with {ai_options.get('model')}")
        except Exception as e:
            results[provider] = {"success": False, "error": str(e)}
            print(f"   ❌ Failed: {e}")

    print("\n📊 Results:")
    for provider, result in results.items():
        print(f"\n{provider.upper()}:")
        if result["success"]:
            print(f"   Model: {result['model']}")
            print(f"   Summary: {result['summary'][:100]}...")
        else:
            print(f"   Error: {result['error']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="OmniParser AI Features Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--file", type=Path, help="Document file to parse", required=True)
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai", "ollama", "lmstudio", "openrouter"],
        default="anthropic",
        help="AI provider to use (default: anthropic)",
    )
    parser.add_argument(
        "--all-features",
        action="store_true",
        help="Run all AI features (tagging, summarization, images, quality)",
    )
    parser.add_argument(
        "--tags", action="store_true", help="Generate tags only"
    )
    parser.add_argument(
        "--summarize", action="store_true", help="Generate summary only"
    )
    parser.add_argument(
        "--images", action="store_true", help="Describe images only"
    )
    parser.add_argument(
        "--quality", action="store_true", help="Score quality only"
    )
    parser.add_argument(
        "--compare", action="store_true", help="Compare providers"
    )

    args = parser.parse_args()

    # Check file exists
    if not args.file.exists():
        print(f"❌ File not found: {args.file}")
        return 1

    # Check secrets
    print_section("Configuration Check")
    secrets = load_secrets()
    config = load_config()

    provider_key = f"{args.provider}_api_key"
    if args.provider in ["anthropic", "openai", "openrouter"]:
        if not secrets.get(provider_key):
            print(f"⚠️  Warning: {provider_key} not found in secrets.json or environment")
            print(f"   Add it to secrets.json or set {provider_key.upper()}")
    elif args.provider == "ollama":
        base_url = secrets.get("ollama_base_url") or config["ai"]["ollama"]["base_url"]
        print(f"ℹ️  Ollama URL: {base_url}")
    elif args.provider == "lmstudio":
        base_url = secrets.get("lmstudio_base_url") or config["ai"]["lmstudio"]["base_url"]
        print(f"ℹ️  LM Studio URL: {base_url}")

    # Parse document
    doc = example_basic_parsing(args.file)

    # Run requested features
    if args.all_features or args.tags:
        example_ai_tagging(doc, args.provider)

    if args.all_features or args.summarize:
        example_ai_summarization(doc, args.provider)

    if args.all_features or args.images:
        example_ai_image_description(doc, args.provider)

    if args.all_features or args.quality:
        example_ai_quality_scoring(doc, args.provider)

    if args.compare:
        example_provider_comparison(doc)

    print_section("Done!")
    print("For more examples, see: https://github.com/yourusername/omniparser/tree/main/examples")

    return 0


if __name__ == "__main__":
    sys.exit(main())
