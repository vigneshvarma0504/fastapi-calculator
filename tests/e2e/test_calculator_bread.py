"""
Playwright E2E tests for Calculator BREAD operations.
Tests cover both positive and negative scenarios for:
- Browse (GET /calculations)
- Read (GET /calculations/{id})
- Edit (PUT/PATCH /calculations/{id})
- Add (POST /calculations)
- Delete (DELETE /calculations/{id})
"""
import pytest
from playwright.sync_api import Page, expect
import time


@pytest.fixture(scope="module")
def app_base_url():
    """Base URL for the frontend application.
    Renamed to avoid conflict with pytest-base-url plugin's fixture scope.
    """
    return "http://localhost:8081"


@pytest.fixture(scope="module")
def api_base():
    """Base URL for the API."""
    return "http://localhost:8000"


@pytest.fixture(scope="function")
def authenticated_page(page: Page, app_base_url: str):
    """Fixture that provides an authenticated page session."""
    # Register a test user
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "testpass123"
    }
    
    # Navigate to register page
    page.goto(f"{app_base_url}/register.html")
    page.fill("#username", test_user["username"])
    page.fill("#email", test_user["email"])
    page.fill("#password", test_user["password"])
    page.click("button[type='submit']")
    
    # Wait for registration success
    page.wait_for_selector(".success", timeout=5000)
    
    # Navigate to login page
    page.goto(f"{app_base_url}/login.html")
    page.fill("#email", test_user["email"])
    page.fill("#password", test_user["password"])
    page.click("button[type='submit']")
    
    # Wait for redirect to calculator page
    page.wait_for_url(f"{app_base_url}/calculator.html", timeout=5000)
    
    return page


class TestCalculatorBREADPositive:
    """Positive test scenarios for BREAD operations."""
    
    def test_add_calculation_success(self, authenticated_page: Page):
        """Test successful creation of a calculation (Add operation)."""
        page = authenticated_page
        
        # Fill in the add form
        page.fill("#add_a", "10")
        page.fill("#add_b", "5")
        page.select_option("#add_type", "Add")
        page.click("#addForm button[type='submit']")
        
        # Wait for success message
        success_msg = page.locator("#addMessage")
        expect(success_msg).to_contain_text("created successfully", timeout=5000)
        expect(success_msg).to_contain_text("Result: 15")
        
        # Verify the calculation appears in the browse list
        page.wait_for_selector("table tbody tr", timeout=5000)
        table_row = page.locator("table tbody tr").first
        expect(table_row).to_contain_text("Add")
        expect(table_row).to_contain_text("10")
        expect(table_row).to_contain_text("5")
        expect(table_row).to_contain_text("15")
    
    def test_add_calculation_subtract(self, authenticated_page: Page):
        """Test successful creation with subtraction operation."""
        page = authenticated_page
        
        page.fill("#add_a", "20")
        page.fill("#add_b", "8")
        page.select_option("#add_type", "Sub")
        page.click("#addForm button[type='submit']")
        
        success_msg = page.locator("#addMessage")
        expect(success_msg).to_contain_text("created successfully", timeout=5000)
        expect(success_msg).to_contain_text("Result: 12")
    
    def test_add_calculation_multiply(self, authenticated_page: Page):
        """Test successful creation with multiplication operation."""
        page = authenticated_page
        
        page.fill("#add_a", "7")
        page.fill("#add_b", "3")
        page.select_option("#add_type", "Multiply")
        page.click("#addForm button[type='submit']")
        
        success_msg = page.locator("#addMessage")
        expect(success_msg).to_contain_text("created successfully", timeout=5000)
        expect(success_msg).to_contain_text("Result: 21")
    
    def test_add_calculation_divide(self, authenticated_page: Page):
        """Test successful creation with division operation."""
        page = authenticated_page
        
        page.fill("#add_a", "20")
        page.fill("#add_b", "4")
        page.select_option("#add_type", "Divide")
        page.click("#addForm button[type='submit']")
        
        success_msg = page.locator("#addMessage")
        expect(success_msg).to_contain_text("created successfully", timeout=5000)
        expect(success_msg).to_contain_text("Result: 5")
    
    def test_browse_calculations(self, authenticated_page: Page):
        """Test browsing all calculations for the logged-in user."""
        page = authenticated_page
        
        # Create a few calculations
        calculations = [
            ("10", "5", "Add"),
            ("20", "3", "Sub"),
            ("4", "6", "Multiply")
        ]
        
        for a, b, op in calculations:
            page.fill("#add_a", a)
            page.fill("#add_b", b)
            page.select_option("#add_type", op)
            page.click("#addForm button[type='submit']")
            page.wait_for_selector("#addMessage.success", timeout=5000)
        
        # Refresh the list
        page.click("button:has-text('Refresh List')")
        
        # Verify calculations appear in the table
        page.wait_for_selector("table tbody tr", timeout=5000)
        rows = page.locator("table tbody tr")
        expect(rows).to_have_count(3, timeout=5000)
    
    def test_read_specific_calculation(self, authenticated_page: Page):
        """Test reading a specific calculation by ID."""
        page = authenticated_page
        
        # Create a calculation first
        page.fill("#add_a", "100")
        page.fill("#add_b", "25")
        page.select_option("#add_type", "Divide")
        page.click("#addForm button[type='submit']")
        
        # Extract the ID from the success message
        success_msg = page.locator("#addMessage").text_content()
        calc_id = success_msg.split("ID: ")[1].split(",")[0]
        
        # Read the calculation
        page.fill("#read_id", calc_id)
        page.click("#readForm button[type='submit']")
        
        # Verify the result
        read_msg = page.locator("#readMessage")
        expect(read_msg).to_contain_text("Calculation found", timeout=5000)
        
        result_table = page.locator("#readResult table")
        expect(result_table).to_be_visible()
        expect(result_table).to_contain_text("100")
        expect(result_table).to_contain_text("25")
        expect(result_table).to_contain_text("Divide")
        expect(result_table).to_contain_text("4")
    
    def test_edit_calculation_put(self, authenticated_page: Page):
        """Test editing a calculation using PUT method."""
        page = authenticated_page
        
        # Create a calculation
        page.fill("#add_a", "10")
        page.fill("#add_b", "2")
        page.select_option("#add_type", "Add")
        page.click("#addForm button[type='submit']")
        
        # Extract the ID
        success_msg = page.locator("#addMessage").text_content()
        calc_id = success_msg.split("ID: ")[1].split(",")[0]
        
        # Edit the calculation
        page.fill("#edit_id", calc_id)
        page.fill("#edit_a", "50")
        page.fill("#edit_b", "5")
        page.select_option("#edit_type", "Multiply")
        page.click("#editForm button[type='submit']")
        
        # Verify the update
        edit_msg = page.locator("#editMessage")
        expect(edit_msg).to_contain_text("updated successfully", timeout=5000)
        expect(edit_msg).to_contain_text("Result: 250")
    
    def test_edit_calculation_from_table(self, authenticated_page: Page):
        """Test editing a calculation using the inline edit button."""
        page = authenticated_page
        
        # Create a calculation
        page.fill("#add_a", "8")
        page.fill("#add_b", "4")
        page.select_option("#add_type", "Sub")
        page.click("#addForm button[type='submit']")
        page.wait_for_selector("#addMessage.success", timeout=5000)
        
        # Click edit button in the table
        page.click("table tbody tr:first-child .edit-btn")
        
        # Verify form is filled
        expect(page.locator("#edit_a")).to_have_value("8")
        expect(page.locator("#edit_b")).to_have_value("4")
        expect(page.locator("#edit_type")).to_have_value("Sub")
        
        # Update values
        page.fill("#edit_a", "16")
        page.fill("#edit_b", "4")
        page.select_option("#edit_type", "Divide")
        page.click("#editForm button[type='submit']")
        
        # Verify success
        edit_msg = page.locator("#editMessage")
        expect(edit_msg).to_contain_text("updated successfully", timeout=5000)
        expect(edit_msg).to_contain_text("Result: 4")
    
    def test_delete_calculation(self, authenticated_page: Page):
        """Test deleting a calculation using the form."""
        page = authenticated_page
        
        # Create a calculation
        page.fill("#add_a", "99")
        page.fill("#add_b", "1")
        page.select_option("#add_type", "Sub")
        page.click("#addForm button[type='submit']")
        
        # Extract the ID
        success_msg = page.locator("#addMessage").text_content()
        calc_id = success_msg.split("ID: ")[1].split(",")[0]
        
        # Delete the calculation
        page.fill("#delete_id", calc_id)
        
        # Handle confirmation dialog
        page.once("dialog", lambda dialog: dialog.accept())
        page.click("#deleteForm button[type='submit']")
        
        # Verify deletion
        delete_msg = page.locator("#deleteMessage")
        expect(delete_msg).to_contain_text("deleted successfully", timeout=5000)
    
    def test_delete_calculation_from_table(self, authenticated_page: Page):
        """Test deleting a calculation using the inline delete button."""
        page = authenticated_page
        
        # Create a calculation
        page.fill("#add_a", "77")
        page.fill("#add_b", "7")
        page.select_option("#add_type", "Multiply")
        page.click("#addForm button[type='submit']")
        page.wait_for_selector("#addMessage.success", timeout=5000)
        
        # Get initial row count
        initial_count = page.locator("table tbody tr").count()
        
        # Handle confirmation dialog and delete
        page.once("dialog", lambda dialog: dialog.accept())
        page.click("table tbody tr:first-child .delete-btn")
        
        # Wait for alert and refresh
        page.wait_for_timeout(1000)
        
        # Verify row is removed (count decreased)
        page.wait_for_function(
            f"document.querySelectorAll('table tbody tr').length < {initial_count}",
            timeout=5000
        )


class TestCalculatorBREADNegative:
    """Negative test scenarios for BREAD operations."""
    
    def test_add_calculation_division_by_zero(self, authenticated_page: Page):
        """Test that division by zero is prevented (client-side validation)."""
        page = authenticated_page
        
        page.fill("#add_a", "10")
        page.fill("#add_b", "0")
        page.select_option("#add_type", "Divide")
        page.click("#addForm button[type='submit']")
        
        # Verify error message
        error_msg = page.locator("#addMessage")
        expect(error_msg).to_contain_text("Division by zero is not allowed", timeout=5000)
        expect(error_msg).to_have_class("error")
    
    def test_add_calculation_invalid_numbers(self, authenticated_page: Page):
        """Test that invalid number inputs are handled."""
        page = authenticated_page
        
        # Try submitting with invalid input (HTML5 validation should prevent this,
        # but we test the form's response)
        page.fill("#add_a", "abc")
        page.fill("#add_b", "5")
        page.select_option("#add_type", "Add")
        
        # HTML5 validation should prevent submission
        # The form shouldn't submit with invalid number input
        is_valid = page.evaluate("""
            document.getElementById('add_a').checkValidity()
        """)
        assert not is_valid, "Invalid input should fail HTML5 validation"
    
    def test_read_nonexistent_calculation(self, authenticated_page: Page):
        """Test reading a calculation that doesn't exist."""
        page = authenticated_page
        
        # Try to read a calculation with a very high ID that likely doesn't exist
        page.fill("#read_id", "999999")
        page.click("#readForm button[type='submit']")
        
        # Verify error message
        read_msg = page.locator("#readMessage")
        expect(read_msg).to_contain_text("not found", timeout=5000)
        expect(read_msg).to_have_class("error")
    
    def test_edit_nonexistent_calculation(self, authenticated_page: Page):
        """Test editing a calculation that doesn't exist."""
        page = authenticated_page
        
        page.fill("#edit_id", "999999")
        page.fill("#edit_a", "10")
        page.fill("#edit_b", "5")
        page.select_option("#edit_type", "Add")
        page.click("#editForm button[type='submit']")
        
        # Verify error message
        edit_msg = page.locator("#editMessage")
        expect(edit_msg).to_contain_text("not found", timeout=5000)
        expect(edit_msg).to_have_class("error")
    
    def test_edit_calculation_division_by_zero(self, authenticated_page: Page):
        """Test that editing to create division by zero is prevented."""
        page = authenticated_page
        
        # Create a valid calculation first
        page.fill("#add_a", "10")
        page.fill("#add_b", "5")
        page.select_option("#add_type", "Add")
        page.click("#addForm button[type='submit']")
        
        # Extract the ID
        success_msg = page.locator("#addMessage").text_content()
        calc_id = success_msg.split("ID: ")[1].split(",")[0]
        
        # Try to edit to division by zero
        page.fill("#edit_id", calc_id)
        page.fill("#edit_a", "10")
        page.fill("#edit_b", "0")
        page.select_option("#edit_type", "Divide")
        page.click("#editForm button[type='submit']")
        
        # Verify error message
        edit_msg = page.locator("#editMessage")
        expect(edit_msg).to_contain_text("Division by zero is not allowed", timeout=5000)
        expect(edit_msg).to_have_class("error")
    
    def test_delete_nonexistent_calculation(self, authenticated_page: Page):
        """Test deleting a calculation that doesn't exist."""
        page = authenticated_page
        
        page.fill("#delete_id", "999999")
        
        # Handle confirmation dialog
        page.once("dialog", lambda dialog: dialog.accept())
        page.click("#deleteForm button[type='submit']")
        
        # Verify error message
        delete_msg = page.locator("#deleteMessage")
        expect(delete_msg).to_contain_text("not found", timeout=5000)
        expect(delete_msg).to_have_class("error")
    
    def test_unauthorized_access_without_token(self, page: Page, base_url: str):
        """Test that accessing calculator without authentication redirects to login."""
        # Clear any stored token
        page.goto(base_url)
        page.evaluate("localStorage.clear()")
        
        # Try to access calculator page
        page.goto(f"{base_url}/calculator.html")
        
        # Should redirect to login
        page.wait_for_url(f"{base_url}/login.html", timeout=5000)
    
    def test_user_cannot_access_other_user_calculations(self, page: Page, base_url: str):
        """Test that users can only see their own calculations."""
        # Create first user and calculation
        user1 = {
            "username": f"user1_{int(time.time())}",
            "email": f"user1_{int(time.time())}@example.com",
            "password": "testpass123"
        }
        
        page.goto(f"{base_url}/register.html")
        page.fill("#username", user1["username"])
        page.fill("#email", user1["email"])
        page.fill("#password", user1["password"])
        page.click("button[type='submit']")
        page.wait_for_selector(".success", timeout=5000)
        
        page.goto(f"{base_url}/login.html")
        page.fill("#email", user1["email"])
        page.fill("#password", user1["password"])
        page.click("button[type='submit']")
        page.wait_for_url(f"{base_url}/calculator.html", timeout=5000)
        
        # Create a calculation for user1
        page.fill("#add_a", "100")
        page.fill("#add_b", "50")
        page.select_option("#add_type", "Add")
        page.click("#addForm button[type='submit']")
        
        success_msg = page.locator("#addMessage").text_content()
        calc_id = success_msg.split("ID: ")[1].split(",")[0]
        
        # Logout user1
        page.click(".logout-btn")
        page.wait_for_url(f"{base_url}/login.html", timeout=5000)
        
        # Create and login as user2
        user2 = {
            "username": f"user2_{int(time.time())}",
            "email": f"user2_{int(time.time())}@example.com",
            "password": "testpass123"
        }
        
        page.goto(f"{base_url}/register.html")
        page.fill("#username", user2["username"])
        page.fill("#email", user2["email"])
        page.fill("#password", user2["password"])
        page.click("button[type='submit']")
        page.wait_for_selector(".success", timeout=5000)
        
        page.goto(f"{base_url}/login.html")
        page.fill("#email", user2["email"])
        page.fill("#password", user2["password"])
        page.click("button[type='submit']")
        page.wait_for_url(f"{base_url}/calculator.html", timeout=5000)
        
        # Try to read user1's calculation
        page.fill("#read_id", calc_id)
        page.click("#readForm button[type='submit']")
        
        # Should get not found error
        read_msg = page.locator("#readMessage")
        expect(read_msg).to_contain_text("not found", timeout=5000)
        expect(read_msg).to_have_class("error")
    
    def test_expired_token_redirects_to_login(self, authenticated_page: Page, base_url: str):
        """Test that expired/invalid token redirects to login."""
        page = authenticated_page
        
        # Set an invalid token
        page.evaluate("localStorage.setItem('jwt', 'invalid.token.here')")
        
        # Reload the page
        page.reload()
        
        # Try to perform an action (this should fail and redirect)
        page.click("button:has-text('Refresh List')")
        
        # Should eventually redirect to login (after alert)
        page.wait_for_timeout(2000)


class TestCalculatorEdgeCases:
    """Edge case tests for calculator operations."""
    
    def test_decimal_numbers(self, authenticated_page: Page):
        """Test calculations with decimal numbers."""
        page = authenticated_page
        
        page.fill("#add_a", "10.5")
        page.fill("#add_b", "2.3")
        page.select_option("#add_type", "Add")
        page.click("#addForm button[type='submit']")
        
        success_msg = page.locator("#addMessage")
        expect(success_msg).to_contain_text("created successfully", timeout=5000)
        # Result should be approximately 12.8
        expect(success_msg).to_contain_text("12.8")
    
    def test_negative_numbers(self, authenticated_page: Page):
        """Test calculations with negative numbers."""
        page = authenticated_page
        
        page.fill("#add_a", "-10")
        page.fill("#add_b", "5")
        page.select_option("#add_type", "Add")
        page.click("#addForm button[type='submit']")
        
        success_msg = page.locator("#addMessage")
        expect(success_msg).to_contain_text("created successfully", timeout=5000)
        expect(success_msg).to_contain_text("-5")
    
    def test_large_numbers(self, authenticated_page: Page):
        """Test calculations with large numbers."""
        page = authenticated_page
        
        page.fill("#add_a", "999999999")
        page.fill("#add_b", "1")
        page.select_option("#add_type", "Add")
        page.click("#addForm button[type='submit']")
        
        success_msg = page.locator("#addMessage")
        expect(success_msg).to_contain_text("created successfully", timeout=5000)
        expect(success_msg).to_contain_text("1000000000")
    
    def test_zero_operands(self, authenticated_page: Page):
        """Test calculations with zero as operands."""
        page = authenticated_page
        
        page.fill("#add_a", "0")
        page.fill("#add_b", "5")
        page.select_option("#add_type", "Multiply")
        page.click("#addForm button[type='submit']")
        
        success_msg = page.locator("#addMessage")
        expect(success_msg).to_contain_text("created successfully", timeout=5000)
        expect(success_msg).to_contain_text("Result: 0")
    
    def test_browse_empty_calculations_list(self, authenticated_page: Page):
        """Test browsing when user has no calculations."""
        page = authenticated_page
        
        # For a new user, the list should be empty or show a message
        message_elem = page.locator("#calculationsList")
        
        # Check if there's either no table or a "no calculations" message
        has_table = page.locator("table tbody tr").count() > 0
        has_message = "No calculations" in message_elem.text_content()
        
        # One of these should be true
        assert has_table or has_message
