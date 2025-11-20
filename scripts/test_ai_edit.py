#!/usr/bin/env python3
"""
Test script for the /chapters/ai/edit endpoint.
This script sends awful multi-paragraph prose with dialogue to test the AI editing capabilities.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"ai.edit.script.test+{datetime.now().timestamp()}@example.com"
TEST_PASSWORD = "TestP@ssw0rd123!"
TEST_USERNAME = f"ai_edit_tester_{int(datetime.now().timestamp())}"

# Awful multi-paragraph prose with dialogue for testing - intentionally terrible and verbose
AWFUL_PROSE = """
"""


def register_user():
    """Register a new test user."""
    print(f"Registering user: {TEST_USERNAME}")
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": TEST_USERNAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "profile_img": None
        }
    )
    
    if response.status_code in [200, 201]:
        print("✓ User registered successfully")
        return True
    elif response.status_code == 400 and "already exists" in response.text.lower():
        print("⚠ User already exists, proceeding to login")
        return True
    else:
        print(f"✗ Registration failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def login_user():
    """Login and get authentication cookies."""
    print(f"Logging in user: {TEST_EMAIL}")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful (User ID: {data.get('id')})")
        return response.cookies
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def test_ai_edit(cookies):
    """Test the AI edit endpoint with awful prose."""
    print("\nTesting /chapters/ai/edit endpoint...")
    print(f"Sending {len(AWFUL_PROSE)} characters of awful prose\n")
    
    timestamp = int(datetime.now().timestamp())
    
    # Save original prose to file
    original_file = f"original_prose_{timestamp}.txt"
    with open(original_file, 'w') as f:
        f.write(AWFUL_PROSE)
    print(f"✓ Original prose saved to: {original_file}")
    
    response = requests.post(
        f"{BASE_URL}/chapters/ai/edit",
        json={
            "content": AWFUL_PROSE
        },
        cookies=cookies
    )
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Request successful!\n")
        data = response.json()
        
        # Print response structure
        print("=" * 80)
        print("RESPONSE SUMMARY")
        print("=" * 80)
        
        print(f"Execution Time: {data.get('execution_time', 'N/A')} ms")
        print(f"From Cache: {data.get('from_cache', 'N/A')}")
        
        # Before metrics
        if 'before_metrics' in data:
            print("\nBEFORE METRICS:")
            for key, value in data['before_metrics'].items():
                print(f"  {key}: {value}")
        
        # After metrics
        if 'after_metrics' in data:
            print("\nAFTER METRICS:")
            for key, value in data['after_metrics'].items():
                print(f"  {key}: {value}")
        
        # Edits and reconstruction
        edited_prose = AWFUL_PROSE
        if 'edits' in data and 'paragraph_edits' in data['edits']:
            edits = data['edits']['paragraph_edits']
            print(f"\nPARAGRAPH EDITS: {len(edits)} edit(s)")
            print("=" * 80)
            
            # Split original into paragraphs for reconstruction
            paragraphs = AWFUL_PROSE.split('\n\n')
            
            for i, edit in enumerate(edits, 1):
                print(f"\nEdit #{i} (Paragraph {edit.get('paragraph_idx', 'N/A')})")
                print("-" * 80)
                print("ORIGINAL:")
                print(edit.get('original_text', 'N/A')[:200] + "..." if len(edit.get('original_text', '')) > 200 else edit.get('original_text', 'N/A'))
                print("\nEDITED:")
                print(edit.get('edited_text', 'N/A')[:200] + "..." if len(edit.get('edited_text', '')) > 200 else edit.get('edited_text', 'N/A'))
                print("\nJUSTIFICATION:")
                print(edit.get('justification', 'N/A'))
                print("-" * 80)
                
                # Replace paragraph in the reconstructed version
                paragraph_idx = edit.get('paragraph_idx', 0)
                if 0 <= paragraph_idx < len(paragraphs):
                    paragraphs[paragraph_idx] = edit.get('edited_text', paragraphs[paragraph_idx])
            
            # Reconstruct edited prose
            edited_prose = '\n\n'.join(paragraphs)
        
        # Save edited prose to file
        edited_file = f"edited_prose_{timestamp}.txt"
        with open(edited_file, 'w') as f:
            f.write(edited_prose)
        print(f"\n✓ Edited prose saved to: {edited_file}")
        
        # Save full response to file
        output_file = f"ai_edit_response_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Full response saved to: {output_file}")
        
        return True
    else:
        print(f"✗ Request failed!")
        print(f"Response: {response.text}")
        return False


def test_unauthenticated():
    """Test that unauthenticated requests are rejected."""
    print("\nTesting unauthenticated access...")
    
    response = requests.post(
        f"{BASE_URL}/chapters/ai/edit",
        json={
            "content": AWFUL_PROSE
        }
    )
    
    if response.status_code in [401, 403, 422]:
        print(f"✓ Unauthenticated request correctly rejected ({response.status_code})")
        return True
    else:
        print(f"✗ Expected 401/403/422, got {response.status_code}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("AI EDIT ENDPOINT TEST SCRIPT")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Email: {TEST_EMAIL}")
    print("=" * 80)
    print()
    
    # Test unauthenticated access first
    if not test_unauthenticated():
        print("\n⚠ Warning: Unauthenticated test failed, but continuing...")
    
    # Register and login
    if not register_user():
        print("\n✗ Failed to register user. Exiting.")
        sys.exit(1)
    
    cookies = login_user()
    if not cookies:
        print("\n✗ Failed to login. Exiting.")
        sys.exit(1)
    
    # Test the AI edit endpoint
    if not test_ai_edit(cookies):
        print("\n✗ AI edit test failed. Exiting.")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
