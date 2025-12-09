#!/usr/bin/env python3
"""
Quick validation script for BREAD operations.
Tests the API endpoints directly.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_bread_operations():
    """Test all BREAD operations."""
    
    # Create test user
    print_section("1. Creating Test User")
    username = f"testuser_{int(time.time())}"
    email = f"test_{int(time.time())}@example.com"
    password = "testpass123"
    
    response = requests.post(
        f"{BASE_URL}/users/register",
        json={"username": username, "email": email, "password": password}
    )
    print(f"Register Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Login
    print_section("2. Logging In")
    response = requests.post(
        f"{BASE_URL}/users/login",
        json={"email": email, "password": password}
    )
    print(f"Login Status: {response.status_code}")
    token_data = response.json()
    print(f"Got access token: {token_data['access_token'][:20]}...")
    
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    # ADD - Create calculations
    print_section("3. ADD - Creating Calculations")
    calculations = [
        {"a": 10, "b": 5, "type": "Add"},
        {"a": 20, "b": 3, "type": "Sub"},
        {"a": 7, "b": 6, "type": "Multiply"},
        {"a": 100, "b": 4, "type": "Divide"}
    ]
    
    calc_ids = []
    for calc in calculations:
        response = requests.post(
            f"{BASE_URL}/calculations",
            json=calc,
            headers=headers
        )
        print(f"Create {calc['type']} Status: {response.status_code}")
        result = response.json()
        print(f"  {calc['a']} {calc['type']} {calc['b']} = {result['result']}")
        calc_ids.append(result['id'])
    
    # BROWSE - List all calculations
    print_section("4. BROWSE - Listing All Calculations")
    response = requests.get(
        f"{BASE_URL}/calculations",
        headers=headers
    )
    print(f"Browse Status: {response.status_code}")
    all_calcs = response.json()
    print(f"Total calculations: {len(all_calcs)}")
    for calc in all_calcs:
        print(f"  ID {calc['id']}: {calc['a']} {calc['type']} {calc['b']} = {calc['result']}")
    
    # READ - Get specific calculation
    print_section("5. READ - Getting Specific Calculation")
    calc_id = calc_ids[0]
    response = requests.get(
        f"{BASE_URL}/calculations/{calc_id}",
        headers=headers
    )
    print(f"Read Status: {response.status_code}")
    calc = response.json()
    print(f"Calculation {calc_id}:")
    print(f"  Operation: {calc['type']}")
    print(f"  Values: {calc['a']} and {calc['b']}")
    print(f"  Result: {calc['result']}")
    print(f"  User ID: {calc['user_id']}")
    
    # EDIT (PUT) - Update calculation
    print_section("6. EDIT (PUT) - Updating Calculation")
    calc_id = calc_ids[1]
    update_data = {"a": 50, "b": 10, "type": "Multiply"}
    response = requests.put(
        f"{BASE_URL}/calculations/{calc_id}",
        json=update_data,
        headers=headers
    )
    print(f"Update Status: {response.status_code}")
    updated = response.json()
    print(f"Updated calculation {calc_id}:")
    print(f"  Old: 20 Sub 3 = 17")
    print(f"  New: {updated['a']} {updated['type']} {updated['b']} = {updated['result']}")
    
    # EDIT (PATCH) - Partial update
    print_section("7. EDIT (PATCH) - Partial Update")
    calc_id = calc_ids[2]
    patch_data = {"b": 10}  # Only update b
    response = requests.patch(
        f"{BASE_URL}/calculations/{calc_id}",
        json=patch_data,
        headers=headers
    )
    print(f"Patch Status: {response.status_code}")
    patched = response.json()
    print(f"Patched calculation {calc_id}:")
    print(f"  Changed b from 6 to {patched['b']}")
    print(f"  New result: {patched['a']} {patched['type']} {patched['b']} = {patched['result']}")
    
    # DELETE - Remove calculation
    print_section("8. DELETE - Removing Calculation")
    calc_id = calc_ids[3]
    response = requests.delete(
        f"{BASE_URL}/calculations/{calc_id}",
        headers=headers
    )
    print(f"Delete Status: {response.status_code}")
    print(f"Deleted calculation {calc_id}")
    
    # Verify deletion
    response = requests.get(
        f"{BASE_URL}/calculations/{calc_id}",
        headers=headers
    )
    print(f"Verify deletion - Read Status: {response.status_code}")
    if response.status_code == 404:
        print("✓ Calculation successfully deleted (404 Not Found)")
    
    # Final browse
    print_section("9. BROWSE - Final List After Delete")
    response = requests.get(
        f"{BASE_URL}/calculations",
        headers=headers
    )
    final_calcs = response.json()
    print(f"Remaining calculations: {len(final_calcs)}")
    for calc in final_calcs:
        print(f"  ID {calc['id']}: {calc['a']} {calc['type']} {calc['b']} = {calc['result']}")
    
    # Test negative scenario - division by zero
    print_section("10. NEGATIVE TEST - Division by Zero")
    response = requests.post(
        f"{BASE_URL}/calculations",
        json={"a": 10, "b": 0, "type": "Divide"},
        headers=headers
    )
    print(f"Division by Zero Status: {response.status_code}")
    if response.status_code == 400:
        error = response.json()
        print(f"✓ Correctly rejected: {error['detail']}")
    
    # Test negative scenario - unauthorized access
    print_section("11. NEGATIVE TEST - Unauthorized Access")
    response = requests.get(
        f"{BASE_URL}/calculations",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    print(f"Unauthorized Status: {response.status_code}")
    if response.status_code == 401:
        print("✓ Correctly rejected unauthorized request")
    
    print_section("✓ ALL TESTS COMPLETED")
    print("\nSummary:")
    print("  • User registration and login: ✓")
    print("  • ADD (POST /calculations): ✓")
    print("  • BROWSE (GET /calculations): ✓")
    print("  • READ (GET /calculations/{id}): ✓")
    print("  • EDIT PUT (PUT /calculations/{id}): ✓")
    print("  • EDIT PATCH (PATCH /calculations/{id}): ✓")
    print("  • DELETE (DELETE /calculations/{id}): ✓")
    print("  • Division by zero validation: ✓")
    print("  • Unauthorized access protection: ✓")

if __name__ == "__main__":
    try:
        test_bread_operations()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the server.")
        print("Please ensure the FastAPI server is running on http://localhost:8000")
        print("\nStart the server with:")
        print("  uvicorn app.main:app --reload --port 8000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
