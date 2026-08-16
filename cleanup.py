#!/usr/bin/env python3
"""
Workshop Cleanup Script
========================
Removes any AgentCore resources created during the workshop.
Safe to run multiple times (idempotent).
"""
import boto3
import sys


REGION = "us-east-1"


def cleanup_harnesses():
    """Delete any Harness agents created during the workshop."""
    print("\n[Harness Cleanup]")
    
    try:
        client = boto3.client("bedrock-agentcore-control", region_name=REGION)
        
        # List all harnesses
        response = client.list_harnesses()
        harnesses = response.get("harnessSummaries", [])
        
        workshop_harnesses = [
            h for h in harnesses 
            if h.get("harnessName", "").startswith("Crexi")
        ]
        
        if not workshop_harnesses:
            print("  No workshop Harness agents found. Nothing to clean up.")
            return
        
        print(f"  Found {len(workshop_harnesses)} workshop Harness agent(s):")
        for h in workshop_harnesses:
            name = h.get("harnessName", "unknown")
            hid = h.get("harnessId", "unknown")
            print(f"    • {name} ({hid})")
        
        # Delete each
        for h in workshop_harnesses:
            hid = h.get("harnessId")
            name = h.get("harnessName", "unknown")
            try:
                client.delete_harness(harnessId=hid)
                print(f"  ✓ Deleted: {name}")
            except Exception as e:
                print(f"  ⚠ Could not delete {name}: {e}")
    
    except Exception as e:
        print(f"  ⚠ Could not list harnesses: {e}")
        print("    (This is OK if you haven't run Labs 4-5 yet)")


def cleanup_iam_role():
    """Remove the workshop IAM role."""
    print("\n[IAM Role Cleanup]")
    
    iam = boto3.client("iam")
    role_name = "CrexiWorkshopHarnessRole"
    
    try:
        # Delete inline policies first
        policies = iam.list_role_policies(RoleName=role_name)
        for policy_name in policies.get("PolicyNames", []):
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
        
        # Delete the role
        iam.delete_role(RoleName=role_name)
        print(f"  ✓ Deleted IAM role: {role_name}")
    
    except iam.exceptions.NoSuchEntityException:
        print(f"  No workshop IAM role found. Nothing to clean up.")
    except Exception as e:
        print(f"  ⚠ Could not delete role: {e}")


def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Crexi Workshop — Resource Cleanup                     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    cleanup_harnesses()
    cleanup_iam_role()
    
    print("\n" + "=" * 60)
    print("✅ Cleanup complete!")
    print("=" * 60)
    print()
    print("All workshop resources have been removed.")
    print("Your AWS account should have no lingering charges from this workshop.")
    print()


if __name__ == "__main__":
    main()
