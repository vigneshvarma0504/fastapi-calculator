# Quick Start Guide - BREAD Operations

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL (or SQLite for testing)
- Playwright (for E2E tests)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

---

## 📝 Database Setup

### Run Migration
```bash
# Apply the user_id migration
alembic upgrade head
```

### Verify Migration
```bash
# Check migration status
alembic current

# You should see: 0002_add_user_id (head)
```

---

## ▶️ Running the Application

### 1. Start Backend Server
```bash
# Terminal 1
uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2. Start Frontend Server
```bash
# Terminal 2
cd frontend
python serve.py
```

**Expected Output:**
```
Serving on http://localhost:8081
```

### 3. Open Browser
Navigate to: http://localhost:8081/register.html

---

## ✅ Quick Validation

### Option 1: API Validation Script (Recommended)
```bash
# Terminal 3
python test_bread_api.py
```

**What it does:**
- ✓ Registers a test user
- ✓ Logs in and gets token
- ✓ Creates 4 calculations (Add, Sub, Multiply, Divide)
- ✓ Browses all calculations
- ✓ Reads specific calculation
- ✓ Updates calculation (PUT)
- ✓ Patches calculation (PATCH)
- ✓ Deletes calculation
- ✓ Tests division by zero
- ✓ Tests unauthorized access

**Expected Result:** All tests pass with ✓ marks

### Option 2: Manual Testing
1. Go to http://localhost:8081/register.html
2. Register: username, email, password
3. Login with your credentials
4. Try all operations:
   - Add calculation
   - View in table
   - Edit calculation
   - Delete calculation

### Option 3: E2E Tests
```bash
# Run all E2E tests
pytest tests/e2e/test_calculator_bread.py -v

# Run specific test class
pytest tests/e2e/test_calculator_bread.py::TestCalculatorBREADPositive -v

# Run specific test
pytest tests/e2e/test_calculator_bread.py::TestCalculatorBREADPositive::test_add_calculation_success -v
```

---

## 🧪 Testing Commands

### Run All Tests
```bash
# All tests
pytest -v

# E2E tests only
pytest tests/e2e/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest --cov=app --cov-report=html
```

### Test Individual Operations

**Browse:**
```bash
curl -X GET "http://localhost:8000/calculations" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Add:**
```bash
curl -X POST "http://localhost:8000/calculations" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"a": 10, "b": 5, "type": "Add"}'
```

**Read:**
```bash
curl -X GET "http://localhost:8000/calculations/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Edit (PUT):**
```bash
curl -X PUT "http://localhost:8000/calculations/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"a": 20, "b": 4, "type": "Multiply"}'
```

**Edit (PATCH):**
```bash
curl -X PATCH "http://localhost:8000/calculations/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"b": 10}'
```

**Delete:**
```bash
curl -X DELETE "http://localhost:8000/calculations/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔍 Troubleshooting

### Issue: "Cannot connect to server"
**Solution:**
```bash
# Check if backend is running
lsof -i :8000

# Start backend if not running
uvicorn app.main:app --reload --port 8000
```

### Issue: "Frontend not loading"
**Solution:**
```bash
# Check if frontend is running
lsof -i :8081

# Start frontend if not running
cd frontend && python serve.py
```

### Issue: "Database error"
**Solution:**
```bash
# Check database connection
# For PostgreSQL:
psql -U your_user -d your_database -c "SELECT 1"

# Run migration
alembic upgrade head

# Check migration status
alembic current
```

### Issue: "Playwright tests failing"
**Solution:**
```bash
# Install/reinstall Playwright
playwright install

# Check if servers are running
lsof -i :8000  # Backend
lsof -i :8081  # Frontend
```

### Issue: "Token expired"
**Solution:**
- Log out and log in again
- Clear localStorage: `localStorage.clear()` in browser console
- Close and reopen browser

### Issue: "Division by zero error"
**Expected behavior** - This is correct!
- Server returns 400 Bad Request
- Client prevents submission

---

## 📊 Expected Test Results

### API Validation Script
```
==============================================================
  1. Creating Test User
==============================================================
Register Status: 201
...

==============================================================
  ✓ ALL TESTS COMPLETED
==============================================================

Summary:
  • User registration and login: ✓
  • ADD (POST /calculations): ✓
  • BROWSE (GET /calculations): ✓
  • READ (GET /calculations/{id}): ✓
  • EDIT PUT (PUT /calculations/{id}): ✓
  • EDIT PATCH (PATCH /calculations/{id}): ✓
  • DELETE (DELETE /calculations/{id}): ✓
  • Division by zero validation: ✓
  • Unauthorized access protection: ✓
```

### E2E Tests
```
tests/e2e/test_calculator_bread.py::TestCalculatorBREADPositive::test_add_calculation_success PASSED
tests/e2e/test_calculator_bread.py::TestCalculatorBREADPositive::test_add_calculation_subtract PASSED
tests/e2e/test_calculator_bread.py::TestCalculatorBREADPositive::test_add_calculation_multiply PASSED
...
tests/e2e/test_calculator_bread.py::TestCalculatorBREADNegative::test_division_by_zero PASSED
tests/e2e/test_calculator_bread.py::TestCalculatorBREADNegative::test_unauthorized_access PASSED
...

===================== 20 passed in 45.67s =====================
```

---

## 🎯 Quick Checklist

Before considering implementation complete:

- [ ] Backend server starts without errors
- [ ] Frontend server starts without errors
- [ ] Database migration applied successfully
- [ ] Can register a new user
- [ ] Can log in successfully
- [ ] Can create calculation (Add)
- [ ] Can view all calculations (Browse)
- [ ] Can view specific calculation (Read)
- [ ] Can update calculation (Edit)
- [ ] Can delete calculation (Delete)
- [ ] Division by zero is prevented
- [ ] Unauthorized access is blocked
- [ ] API validation script passes
- [ ] E2E tests pass

---

## 📚 Documentation Files

- **BREAD_IMPLEMENTATION.md** - Complete API and usage guide
- **BREAD_COMPLETE_SUMMARY.md** - Implementation summary
- **This file (QUICK_START.md)** - Quick start guide
- **README.md** - Project overview

---

## 🆘 Getting Help

1. **Check error messages** - They usually tell you what's wrong
2. **Review server logs** - Check terminal output for errors
3. **Browser console** - F12 → Console tab
4. **Network tab** - F12 → Network tab to see API calls
5. **Test with curl** - Isolate frontend vs backend issues

---

## 🎉 Success Indicators

You'll know everything is working when:

✅ Backend starts and shows "Application startup complete"  
✅ Frontend serves on port 8081  
✅ You can register and login  
✅ Calculator page loads after login  
✅ All BREAD operations work in UI  
✅ `python test_bread_api.py` shows all ✓ marks  
✅ Playwright tests pass  

---

**Ready to go? Start with:**
```bash
# Terminal 1
uvicorn app.main:app --reload --port 8000

# Terminal 2
python frontend/serve.py

# Terminal 3
python test_bread_api.py
```

**🚀 Happy calculating!**
