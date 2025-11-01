# Contributing to Personal Finance Manager

Thank you for your interest in contributing! This document provides guidelines for extending and improving the platform.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Current Implementation Status](#current-implementation-status)
3. [Adding New Components](#adding-new-components)
4. [Adding New API Endpoints](#adding-new-api-endpoints)
5. [Code Style & Patterns](#code-style--patterns)
6. [Testing Requirements](#testing-requirements)
7. [Pull Request Process](#pull-request-process)

---

## Development Setup

**For complete installation instructions**, see [GETTING_STARTED.md](GETTING_STARTED.md).

**Quick version:**
```bash
# Backend: cd backend → create venv → activate → pip install -r requirements.txt → python app.py
# Frontend: cd frontend → npm install → npm start
```

Once both servers are running, you're ready to develop!

---

## Current Implementation Status

### Phase 1: Backend Foundation ✅ **COMPLETE**

- ✅ 14 database models (all asset types)
- ✅ 96 REST API endpoints
- ✅ Utility functions (FIFO, XIRR, cash flow, net worth)
- ✅ Database migration scripts
- ✅ API services configured in frontend

### Phase 2: Frontend Components ✅ **COMPLETE**

All major components implemented with 900-1200+ lines each:
- ✅ Dashboard (net worth, allocation, cash flow)
- ✅ Stocks (full CRUD, tracking)
- ✅ Portfolio (transactions, P/L)
- ✅ Analytics (charts, insights)
- ✅ Health (concentration, diversification)
- ✅ Recommendations (rebalancing)
- ✅ Settings (import/export, backup)
- ✅ Income & Expenses (1100+ lines, full budget management)
- ✅ Mutual Funds (1000+ lines, schemes, transactions, holdings, SIP)
- ✅ Fixed Income (1200+ lines, FD/EPF/NPS tabs)
- ✅ Accounts (1200+ lines, Savings/Lending/Other investments)
- ✅ Reports (900+ lines, trends & export)

### Phase 3: Enhanced Features 🔨 **IN PROGRESS (83% - 15/18 items)**

**Completed:**
- ✅ Settings expansion (global allocation targets, emergency fund config)
- ✅ Health updates (debt-to-income ratio, savings rate, financial health score)
- ✅ Unified XIRR calculation across all asset types
- ✅ All backend utilities and calculations

**Remaining:**
- ⏭️ Recommendations updates (moved to Phase 5)
- ⚠️ Documentation updates (in progress)
- ⚠️ Comprehensive testing (61% API coverage)

**See [ROADMAP.md](docs/ROADMAP.md) for detailed timeline.**
   - Lending tracker
   - Other investments (gold, bonds, crypto)

5. **Reports** - Priority 4 (Week 4-5)
   - Net worth trends
   - Tax summary
   - Export to PDF/Excel

### Phase 3: Enhanced Features 📋 **PLANNED**

- Settings enhancements (global allocation targets)
- Health enhancements (debt-to-income, emergency fund)
- Recommendations enhancements (budget optimization)
- Unified XIRR (across all assets)

---

## Adding New Components

### Step-by-Step Guide

Use this pattern when adding any new component (e.g., `MutualFunds.js`):

#### 1. Create Component File

Create `frontend/src/components/YourComponent.js`:

```javascript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
} from '@mui/material';
import { yourAPI } from '../services/api';

function YourComponent() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await yourAPI.getAll();
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load data');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Your Component Title
      </Typography>
      {/* Your component content */}
    </Box>
  );
}

export default YourComponent;
```

#### 2. Update App.js

Replace the placeholder in `frontend/src/App.js`:

```javascript
// Add import at top
import YourComponent from './components/YourComponent';

// Remove placeholder line:
// const YourComponent = () => <div>Coming Soon</div>;

// The tab panel already exists - your component will now render
```

#### 3. Test the Component

```bash
# Start servers
cd backend && python app.py
cd frontend && npm start

# Navigate to your tab in browser
# Check browser console for errors
# Test CRUD operations
# Verify responsive design
```

### Reference Components

Study these existing components for patterns:

| Component | Best For Learning |
|-----------|-------------------|
| `StockTracking.js` | Complete CRUD, forms, modals, search/filter |
| `Portfolio.js` | Transaction management, tabs, sortable tables |
| `Dashboard.js` | Chart visualization, API aggregation |
| `Analytics.js` | Recharts implementation, tooltips |
| `Settings.js` | Form handling, file uploads, validation |

---

## Adding New API Endpoints

### Backend Implementation

#### 1. Add Database Model (if needed)

In `backend/app.py`:

```python
class YourModel(db.Model):
    __tablename__ = 'your_table'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'amount': self.amount,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

#### 2. Create API Endpoints

In `backend/app.py`:

```python
@app.route('/api/your-resource', methods=['GET'])
@login_required
def get_your_resources():
    try:
        resources = YourModel.query.all()
        return jsonify([r.to_dict() for r in resources]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/your-resource', methods=['POST'])
@login_required
def create_your_resource():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        # Create
        resource = YourModel(
            name=data['name'],
            amount=data.get('amount', 0.0)
        )
        db.session.add(resource)
        db.session.commit()
        
        return jsonify(resource.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
```

#### 3. Add Frontend API Service

In `frontend/src/services/api.js`:

```javascript
export const yourAPI = {
  getAll: () => api.get('/your-resource'),
  create: (data) => api.post('/your-resource', data),
  update: (id, data) => api.put(`/your-resource/${id}`, data),
  delete: (id) => api.delete(`/your-resource/${id}`),
};
```

---

## Code Style & Patterns

### Python (Backend)

**Follow existing patterns:**

```python
# ✅ Good: Use utility functions
from utils import calculate_holdings, parse_zone

# ✅ Good: Consistent error handling
try:
    result = some_operation()
    return jsonify(result), 200
except Exception as e:
    db.session.rollback()
    return jsonify({'error': str(e)}), 500

# ✅ Good: Use to_dict() for serialization
return jsonify([model.to_dict() for model in models])

# ❌ Bad: Inline calculations, no utility functions
# ❌ Bad: Missing error handling
# ❌ Bad: Returning raw model objects
```

**Utility Function Organization:**

- `utils/holdings.py` - Portfolio calculations (FIFO, P/L)
- `utils/mutual_funds.py` - MF-specific logic
- `utils/cash_flow.py` - Income/expense analysis
- `utils/net_worth.py` - Net worth aggregation
- `utils/zones.py` - Price zone parsing
- `utils/helpers.py` - General utilities

### JavaScript (Frontend)

**Follow existing patterns:**

```javascript
// ✅ Good: useState for state management
const [data, setData] = useState([]);
const [loading, setLoading] = useState(true);

// ✅ Good: useEffect for data fetching
useEffect(() => {
  fetchData();
}, []);

// ✅ Good: Async/await with try-catch
const fetchData = async () => {
  try {
    const response = await api.getAll();
    setData(response.data);
  } catch (error) {
    console.error('Error:', error);
  }
};

// ✅ Good: Material-UI components
import { Card, Button, TextField } from '@mui/material';

// ❌ Bad: Inline styles (use sx prop instead)
// ❌ Bad: No loading/error states
// ❌ Bad: Synchronous API calls
```

### Material-UI Styling

Use `sx` prop for styling:

```javascript
<Box sx={{ mt: 3, mb: 2, p: 2 }}>
  <Card sx={{ 
    borderRadius: 2,
    bgcolor: 'background.paper'
  }}>
    <CardContent>
      <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
        Title
      </Typography>
    </CardContent>
  </Card>
</Box>
```

---

## Testing Requirements

### Component Testing Checklist

Before submitting a PR, verify:

#### Development
- [ ] Component renders without errors
- [ ] API calls work (check browser console)
- [ ] Loading state displays while fetching
- [ ] Error messages display correctly
- [ ] Forms validate inputs (client-side)
- [ ] CRUD operations work (Create, Read, Update, Delete)

#### UI/UX
- [ ] Matches existing dark theme
- [ ] Responsive on mobile (use browser dev tools, 375px width)
- [ ] Tables are scrollable if content exceeds viewport
- [ ] Buttons are clearly labeled
- [ ] Success messages appear after actions
- [ ] Consistent spacing (use Material-UI spacing scale)

#### Functionality
- [ ] Data persists across page refresh
- [ ] Calculations are accurate (verify with known values)
- [ ] Date formats are consistent (use ISO format in API)
- [ ] Currency formatted correctly (₹ symbol, comma separators)
- [ ] Search/filter works (if applicable)
- [ ] Sorting works (if applicable)

### Manual Testing

```bash
# 1. Start clean
rm backend/instance/investment_manager.db
cd backend && python app.py

# 2. Add test data via UI
# 3. Verify calculations
# 4. Test edge cases (empty states, max values, etc.)
# 5. Check browser console for errors
```

---

## Pull Request Process

### Before Submitting

1. **Test your changes** (use checklist above)
2. **Update documentation** if adding new features
3. **Check for linter errors** (if using ESLint/Pylint)
4. **Verify existing features** still work

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Enhancement
- [ ] Documentation update

## What was changed?
- File 1: Description
- File 2: Description

## How to test?
1. Step 1
2. Step 2
3. Expected result

## Screenshots (if UI changes)
[Attach screenshots]

## Checklist
- [ ] Code follows existing patterns
- [ ] Component tested manually
- [ ] Documentation updated
- [ ] No breaking changes
```

### Review Process

1. Submit PR with descriptive title
2. Maintainer reviews code
3. Address feedback if any
4. PR merged after approval

---

## Development Tips

### Debugging

```javascript
// Frontend: Check API calls
console.log('API Response:', response.data);

// Backend: Check request data
print(f"Received data: {request.get_json()}")
```

### Common Pitfalls

1. **Forgot to activate venv** → Backend imports fail
2. **Wrong API endpoint** → Check `frontend/src/services/api.js`
3. **CORS errors** → Backend must be running
4. **Database locked** → Close other backend instances
5. **Port in use** → Kill existing process (see [GETTING_STARTED.md](GETTING_STARTED.md))

### Useful Commands

```bash
# Backend: Check if API endpoint exists
curl http://localhost:5000/api/your-endpoint

# Frontend: Clear npm cache
cd frontend && rm -rf node_modules && npm install

# Database: Reset and start fresh
rm backend/instance/investment_manager.db
cd backend && python app.py
```

---

## Questions or Help?

- **Architecture questions**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API documentation**: See [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **Feature details**: See [docs/FEATURES.md](docs/FEATURES.md)
- **Implementation roadmap**: See [ROADMAP.md](ROADMAP.md)

---

## Code of Conduct

- Be respectful and constructive
- Follow existing code patterns
- Test thoroughly before submitting
- Document new features
- Ask questions if unclear

---

**Happy coding! We appreciate your contributions!** 🚀

