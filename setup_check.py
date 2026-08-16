#!/usr/bin/env python3
"""
Workshop Environment Verification
==================================
Run this script to verify your environment is ready for the workshop.
"""
import sys
import subprocess
import importlib


def check_python_version():
    """Check Python version >= 3.10"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro} — need 3.10+")
        return False


def check_boto3():
    """Check boto3 is installed"""
    try:
        import boto3
        print(f"  ✓ boto3 {boto3.__version__}")
        return True
    except ImportError:
        print("  ✗ boto3 not installed — run: pip install boto3")
        return False


def check_aws_cli():
    """Check AWS CLI is installed and version 2"""
    try:
        result = subprocess.run(
            ["aws", "--version"], capture_output=True, text=True, timeout=10
        )
        version_str = result.stdout.strip() or result.stderr.strip()
        if "aws-cli/2" in version_str:
            print(f"  ✓ AWS CLI v2 detected")
            return True
        else:
            print(f"  ⚠ AWS CLI found but not v2: {version_str}")
            return True  # Still usable
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  ✗ AWS CLI not found — install from https://aws.amazon.com/cli/")
        return False


def check_aws_credentials():
    """Check AWS credentials are configured"""
    try:
        import boto3
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        account = identity["Account"]
        arn = identity["Arn"]
        print(f"  ✓ AWS credentials configured")
        print(f"    Account: {account}")
        print(f"    Identity: {arn}")
        return True
    except Exception as e:
        print(f"  ✗ AWS credentials not configured: {e}")
        print("    Run: aws configure (or set up SSO)")
        return False


def check_bedrock_access():
    """Check Bedrock model access"""
    try:
        import boto3
        bedrock = boto3.client("bedrock", region_name="us-east-1")
        models = bedrock.list_foundation_models()
        model_count = len(models.get("modelSummaries", []))
        
        # Check for Claude specifically
        claude_available = any(
            "claude" in m.get("modelId", "").lower()
            for m in models.get("modelSummaries", [])
        )
        
        if claude_available:
            print(f"  ✓ Bedrock access confirmed ({model_count} models available, Claude found)")
            return True
        else:
            print(f"  ⚠ Bedrock accessible but Claude not found — enable model access in console")
            return False
    except Exception as e:
        print(f"  ✗ Cannot access Bedrock: {e}")
        print("    Ensure your IAM role has bedrock:ListFoundationModels permission")
        return False


def check_region():
    """Check AWS region is set"""
    try:
        import boto3
        session = boto3.session.Session()
        region = session.region_name
        if region:
            print(f"  ✓ AWS Region: {region}")
            return True
        else:
            print("  ⚠ No default region set — will use us-east-1")
            return True
    except Exception:
        print("  ⚠ Cannot determine region")
        return True


def main():
    print("=" * 60)
    print("  Crexi Workshop — Environment Check")
    print("=" * 60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("boto3 Library", check_boto3),
        ("AWS CLI", check_aws_cli),
        ("AWS Credentials", check_aws_credentials),
        ("AWS Region", check_region),
        ("Bedrock Access", check_bedrock_access),
    ]

    results = []
    for name, check_fn in checks:
        print(f"[{name}]")
        results.append(check_fn())
        print()

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"  All checks passed ({passed}/{total}) — you're ready! 🎉")
    else:
        print(f"  {passed}/{total} checks passed — fix the issues above")
    print("=" * 60)


if __name__ == "__main__":
    main()
