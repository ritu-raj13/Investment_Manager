import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  FormControl,
  InputLabel,
  Select,
  InputAdornment,
} from '@mui/material';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line
} from 'recharts';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { incomeAPI, expensesAPI, budgetsAPI } from '../services/api';

const COLORS = ['#60a5fa', '#a78bfa', '#4ade80', '#fbbf24', '#f87171', '#fb923c', '#ec4899', '#8b5cf6'];

function IncomeExpenses() {
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Income state
  const [incomeTransactions, setIncomeTransactions] = useState([]);
  const [incomeSummary, setIncomeSummary] = useState(null);
  const [incomeCategories, setIncomeCategories] = useState([]);

  // Expense state
  const [expenseTransactions, setExpenseTransactions] = useState([]);
  const [expenseSummary, setExpenseSummary] = useState(null);
  const [expenseCategories, setExpenseCategories] = useState([]);
  const [expenseTrends, setExpenseTrends] = useState([]);

  // Budget state
  const [budgets, setBudgets] = useState([]);
  const [budgetStatus, setBudgetStatus] = useState([]);

  // Dialog states
  const [openIncomeDialog, setOpenIncomeDialog] = useState(false);
  const [openExpenseDialog, setOpenExpenseDialog] = useState(false);
  const [openBudgetDialog, setOpenBudgetDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  // Form states
  const [incomeForm, setIncomeForm] = useState({
    category: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    description: '',
    source: '',
  });

  const [expenseForm, setExpenseForm] = useState({
    category: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    description: '',
    payment_method: '',
  });

  const [budgetForm, setBudgetForm] = useState({
    category: '',
    amount: '',
    period: 'monthly',
    month: new Date().toISOString().slice(0, 7),
  });

  useEffect(() => {
    fetchData();
  }, [currentTab]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (currentTab === 0) {
        // Fetch Income data
        const [transactionsRes, summaryRes, categoriesRes] = await Promise.all([
          incomeAPI.getTransactions(),
          incomeAPI.getSummary(),
          incomeAPI.getCategories(),
        ]);
        setIncomeTransactions(transactionsRes.data);
        setIncomeSummary(summaryRes.data);
        
        // Convert categories object to array
        const categoriesArray = Object.entries(categoriesRes.data || {}).map(([category, total]) => ({
          category,
          total
        }));
        setIncomeCategories(categoriesArray);
      } else if (currentTab === 1) {
        // Fetch Expense data
        const [transactionsRes, summaryRes, categoriesRes, trendsRes] = await Promise.all([
          expensesAPI.getTransactions(),
          expensesAPI.getSummary(),
          expensesAPI.getCategories(),
          expensesAPI.getTrends(),
        ]);
        setExpenseTransactions(transactionsRes.data);
        setExpenseSummary(summaryRes.data);
        
        // Convert categories object to array
        const categoriesArray = Object.entries(categoriesRes.data || {}).map(([category, data]) => ({
          category,
          total: data.total || 0,
          count: data.count || 0
        }));
        setExpenseCategories(categoriesArray);
        setExpenseTrends(trendsRes.data);
      } else if (currentTab === 2) {
        // Fetch Budget data
        const [budgetsRes, statusRes] = await Promise.all([
          budgetsAPI.getAll(),
          budgetsAPI.getStatus(),
        ]);
        setBudgets(budgetsRes.data);
        setBudgetStatus(statusRes.data);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load data');
      console.error('Data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Income handlers
  const handleOpenIncomeDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setIncomeForm({
        category: item.category,
        amount: item.amount,
        date: item.date,
        description: item.description || '',
        source: item.source || '',
      });
    } else {
      setEditingItem(null);
      setIncomeForm({
        category: '',
        amount: '',
        date: new Date().toISOString().split('T')[0],
        description: '',
        source: '',
      });
    }
    setOpenIncomeDialog(true);
  };

  const handleSaveIncome = async () => {
    try {
      if (editingItem) {
        await incomeAPI.updateTransaction(editingItem.id, incomeForm);
      } else {
        await incomeAPI.createTransaction(incomeForm);
      }
      setOpenIncomeDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save income transaction');
    }
  };

  const handleDeleteIncome = async (id) => {
    if (window.confirm('Are you sure you want to delete this income transaction?')) {
      try {
        await incomeAPI.deleteTransaction(id);
        fetchData();
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to delete income transaction');
      }
    }
  };

  // Expense handlers
  const handleOpenExpenseDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setExpenseForm({
        category: item.category,
        amount: item.amount,
        date: item.date,
        description: item.description || '',
        payment_method: item.payment_method || '',
      });
    } else {
      setEditingItem(null);
      setExpenseForm({
        category: '',
        amount: '',
        date: new Date().toISOString().split('T')[0],
        description: '',
        payment_method: '',
      });
    }
    setOpenExpenseDialog(true);
  };

  const handleSaveExpense = async () => {
    try {
      if (editingItem) {
        await expensesAPI.updateTransaction(editingItem.id, expenseForm);
      } else {
        await expensesAPI.createTransaction(expenseForm);
      }
      setOpenExpenseDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save expense transaction');
    }
  };

  const handleDeleteExpense = async (id) => {
    if (window.confirm('Are you sure you want to delete this expense transaction?')) {
      try {
        await expensesAPI.deleteTransaction(id);
        fetchData();
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to delete expense transaction');
      }
    }
  };

  // Budget handlers
  const handleOpenBudgetDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setBudgetForm({
        category: item.category,
        amount: item.amount,
        period: item.period,
        month: item.month || new Date().toISOString().slice(0, 7),
      });
    } else {
      setEditingItem(null);
      setBudgetForm({
        category: '',
        amount: '',
        period: 'monthly',
        month: new Date().toISOString().slice(0, 7),
      });
    }
    setOpenBudgetDialog(true);
  };

  const handleSaveBudget = async () => {
    try {
      if (editingItem) {
        await budgetsAPI.update(editingItem.id, budgetForm);
      } else {
        await budgetsAPI.create(budgetForm);
      }
      setOpenBudgetDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save budget');
    }
  };

  const handleDeleteBudget = async (id) => {
    if (window.confirm('Are you sure you want to delete this budget?')) {
      try {
        await budgetsAPI.delete(id);
        fetchData();
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to delete budget');
      }
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Render Income Tab
  const renderIncomeTab = () => {
    const categoryData = incomeCategories.map(cat => ({
      name: cat.category,
      value: cat.total,
    }));

    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <TrendingUpIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Total Income
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  ₹{incomeSummary?.total?.toLocaleString('en-IN') || '0'}
                </Typography>
                <Typography variant="caption" color="white" sx={{ opacity: 0.8 }}>
                  {incomeSummary?.count || 0} transactions
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  This Month
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  ₹{incomeSummary?.this_month?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Last Month
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  ₹{incomeSummary?.last_month?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Category Breakdown */}
        {categoryData.length > 0 && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Income by Category
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={categoryData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {categoryData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Category Breakdown
                  </Typography>
                  <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                    {incomeCategories.map((cat, index) => (
                      <Box key={index} sx={{ mb: 2 }}>
                        <Box display="flex" justifyContent="space-between" mb={0.5}>
                          <Typography variant="body2">{cat.category}</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            ₹{cat.total.toLocaleString('en-IN')}
                          </Typography>
                        </Box>
                        <Box
                          sx={{
                            width: '100%',
                            height: 8,
                            bgcolor: 'background.default',
                            borderRadius: 1,
                            overflow: 'hidden',
                          }}
                        >
                          <Box
                            sx={{
                              width: `${(cat.total / incomeSummary?.total) * 100}%`,
                              height: '100%',
                              bgcolor: COLORS[index % COLORS.length],
                              transition: 'width 0.3s ease',
                            }}
                          />
                        </Box>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Transactions Table */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Income Transactions</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenIncomeDialog()}
              >
                Add Income
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell>Source</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {incomeTransactions.map((transaction) => (
                    <TableRow key={transaction.id}>
                      <TableCell>{new Date(transaction.date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Chip label={transaction.category} size="small" color="primary" />
                      </TableCell>
                      <TableCell>
                        <Typography color="success.main" fontWeight="bold">
                          ₹{transaction.amount.toLocaleString('en-IN')}
                        </Typography>
                      </TableCell>
                      <TableCell>{transaction.source || '-'}</TableCell>
                      <TableCell>{transaction.description || '-'}</TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenIncomeDialog(transaction)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteIncome(transaction.id)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {incomeTransactions.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No income transactions yet. Click "Add Income" to get started.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };

  // Render Expense Tab
  const renderExpenseTab = () => {
    const categoryData = expenseCategories.map(cat => ({
      name: cat.category,
      value: cat.total,
    }));

    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <TrendingDownIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Total Expenses
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  ₹{expenseSummary?.total?.toLocaleString('en-IN') || '0'}
                </Typography>
                <Typography variant="caption" color="white" sx={{ opacity: 0.8 }}>
                  {expenseSummary?.count || 0} transactions
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  This Month
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="error.main">
                  ₹{expenseSummary?.this_month?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Last Month
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  ₹{expenseSummary?.last_month?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Spending Trends */}
        {expenseTrends.length > 0 && (
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Spending Trends (Last 6 Months)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={expenseTrends.slice(-6)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="total"
                    stroke="#f87171"
                    strokeWidth={2}
                    name="Total Expenses"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Category Breakdown */}
        {categoryData.length > 0 && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Expenses by Category
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={categoryData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {categoryData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Category Breakdown
                  </Typography>
                  <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                    {expenseCategories.map((cat, index) => (
                      <Box key={index} sx={{ mb: 2 }}>
                        <Box display="flex" justifyContent="space-between" mb={0.5}>
                          <Typography variant="body2">{cat.category}</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            ₹{cat.total.toLocaleString('en-IN')}
                          </Typography>
                        </Box>
                        <Box
                          sx={{
                            width: '100%',
                            height: 8,
                            bgcolor: 'background.default',
                            borderRadius: 1,
                            overflow: 'hidden',
                          }}
                        >
                          <Box
                            sx={{
                              width: `${(cat.total / expenseSummary?.total) * 100}%`,
                              height: '100%',
                              bgcolor: COLORS[index % COLORS.length],
                              transition: 'width 0.3s ease',
                            }}
                          />
                        </Box>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Transactions Table */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Expense Transactions</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenExpenseDialog()}
              >
                Add Expense
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell>Payment Method</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {expenseTransactions.map((transaction) => (
                    <TableRow key={transaction.id}>
                      <TableCell>{new Date(transaction.date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Chip label={transaction.category} size="small" color="secondary" />
                      </TableCell>
                      <TableCell>
                        <Typography color="error.main" fontWeight="bold">
                          ₹{transaction.amount.toLocaleString('en-IN')}
                        </Typography>
                      </TableCell>
                      <TableCell>{transaction.payment_method || '-'}</TableCell>
                      <TableCell>{transaction.description || '-'}</TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenExpenseDialog(transaction)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteExpense(transaction.id)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {expenseTransactions.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No expense transactions yet. Click "Add Expense" to get started.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };

  // Render Budget Tab
  const renderBudgetTab = () => {
    return (
      <Box>
        {/* Budget Status Overview */}
        {budgetStatus.length > 0 && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {budgetStatus.map((status, index) => {
              const percentage = (status.spent / status.budget) * 100;
              const isOverBudget = percentage > 100;
              const isNearLimit = percentage > 80 && percentage <= 100;

              return (
                <Grid item xs={12} md={6} lg={4} key={index}>
                  <Card>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="h6">{status.category}</Typography>
                        {isOverBudget ? (
                          <WarningIcon color="error" />
                        ) : isNearLimit ? (
                          <WarningIcon color="warning" />
                        ) : (
                          <CheckCircleIcon color="success" />
                        )}
                      </Box>
                      
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2" color="text.secondary">
                          Spent
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          ₹{status.spent.toLocaleString('en-IN')}
                        </Typography>
                      </Box>
                      
                      <Box display="flex" justifyContent="space-between" mb={2}>
                        <Typography variant="body2" color="text.secondary">
                          Budget
                        </Typography>
                        <Typography variant="body2">
                          ₹{status.budget.toLocaleString('en-IN')}
                        </Typography>
                      </Box>

                      <Box
                        sx={{
                          width: '100%',
                          height: 10,
                          bgcolor: 'background.default',
                          borderRadius: 1,
                          overflow: 'hidden',
                          mb: 1,
                        }}
                      >
                        <Box
                          sx={{
                            width: `${Math.min(percentage, 100)}%`,
                            height: '100%',
                            bgcolor: isOverBudget ? 'error.main' : isNearLimit ? 'warning.main' : 'success.main',
                            transition: 'width 0.3s ease',
                          }}
                        />
                      </Box>

                      <Typography
                        variant="caption"
                        color={isOverBudget ? 'error.main' : isNearLimit ? 'warning.main' : 'success.main'}
                      >
                        {percentage.toFixed(1)}% used
                        {isOverBudget && ` (₹${(status.spent - status.budget).toLocaleString('en-IN')} over)`}
                        {!isOverBudget && ` (₹${(status.budget - status.spent).toLocaleString('en-IN')} remaining)`}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        )}

        {/* Budgets Table */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Budgets</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenBudgetDialog()}
              >
                Add Budget
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Category</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell>Period</TableCell>
                    <TableCell>Month</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {budgets.map((budget) => (
                    <TableRow key={budget.id}>
                      <TableCell>
                        <Chip label={budget.category} size="small" />
                      </TableCell>
                      <TableCell>
                        <Typography fontWeight="bold">
                          ₹{budget.amount.toLocaleString('en-IN')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={budget.period}
                          size="small"
                          color={budget.period === 'monthly' ? 'primary' : 'secondary'}
                        />
                      </TableCell>
                      <TableCell>{budget.month || 'N/A'}</TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenBudgetDialog(budget)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteBudget(budget.id)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {budgets.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No budgets set yet. Click "Add Budget" to get started.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 'bold' }}>
        Income & Expenses
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, val) => setCurrentTab(val)}>
          <Tab label="Income" />
          <Tab label="Expenses" />
          <Tab label="Budgets" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {currentTab === 0 && renderIncomeTab()}
      {currentTab === 1 && renderExpenseTab()}
      {currentTab === 2 && renderBudgetTab()}

      {/* Income Dialog */}
      <Dialog open={openIncomeDialog} onClose={() => setOpenIncomeDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Income' : 'Add Income'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Category"
                value={incomeForm.category}
                onChange={(e) => setIncomeForm({ ...incomeForm, category: e.target.value })}
                select
              >
                <MenuItem value="Salary">Salary</MenuItem>
                <MenuItem value="Bonus">Bonus</MenuItem>
                <MenuItem value="Investment">Investment Income</MenuItem>
                <MenuItem value="Freelance">Freelance</MenuItem>
                <MenuItem value="Business">Business</MenuItem>
                <MenuItem value="Rental">Rental Income</MenuItem>
                <MenuItem value="Other">Other</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={incomeForm.amount}
                onChange={(e) => setIncomeForm({ ...incomeForm, amount: e.target.value })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Date"
                type="date"
                value={incomeForm.date}
                onChange={(e) => setIncomeForm({ ...incomeForm, date: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Source (Optional)"
                value={incomeForm.source}
                onChange={(e) => setIncomeForm({ ...incomeForm, source: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description (Optional)"
                multiline
                rows={2}
                value={incomeForm.description}
                onChange={(e) => setIncomeForm({ ...incomeForm, description: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenIncomeDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveIncome} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Expense Dialog */}
      <Dialog open={openExpenseDialog} onClose={() => setOpenExpenseDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Expense' : 'Add Expense'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Category"
                value={expenseForm.category}
                onChange={(e) => setExpenseForm({ ...expenseForm, category: e.target.value })}
                select
              >
                <MenuItem value="Food">Food & Dining</MenuItem>
                <MenuItem value="Transportation">Transportation</MenuItem>
                <MenuItem value="Shopping">Shopping</MenuItem>
                <MenuItem value="Entertainment">Entertainment</MenuItem>
                <MenuItem value="Bills">Bills & Utilities</MenuItem>
                <MenuItem value="Healthcare">Healthcare</MenuItem>
                <MenuItem value="Education">Education</MenuItem>
                <MenuItem value="Travel">Travel</MenuItem>
                <MenuItem value="Personal">Personal Care</MenuItem>
                <MenuItem value="Other">Other</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={expenseForm.amount}
                onChange={(e) => setExpenseForm({ ...expenseForm, amount: e.target.value })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Date"
                type="date"
                value={expenseForm.date}
                onChange={(e) => setExpenseForm({ ...expenseForm, date: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Payment Method (Optional)"
                value={expenseForm.payment_method}
                onChange={(e) => setExpenseForm({ ...expenseForm, payment_method: e.target.value })}
                select
              >
                <MenuItem value="">None</MenuItem>
                <MenuItem value="Cash">Cash</MenuItem>
                <MenuItem value="Credit Card">Credit Card</MenuItem>
                <MenuItem value="Debit Card">Debit Card</MenuItem>
                <MenuItem value="UPI">UPI</MenuItem>
                <MenuItem value="Net Banking">Net Banking</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description (Optional)"
                multiline
                rows={2}
                value={expenseForm.description}
                onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenExpenseDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveExpense} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Budget Dialog */}
      <Dialog open={openBudgetDialog} onClose={() => setOpenBudgetDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Budget' : 'Add Budget'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Category"
                value={budgetForm.category}
                onChange={(e) => setBudgetForm({ ...budgetForm, category: e.target.value })}
                select
              >
                <MenuItem value="Food">Food & Dining</MenuItem>
                <MenuItem value="Transportation">Transportation</MenuItem>
                <MenuItem value="Shopping">Shopping</MenuItem>
                <MenuItem value="Entertainment">Entertainment</MenuItem>
                <MenuItem value="Bills">Bills & Utilities</MenuItem>
                <MenuItem value="Healthcare">Healthcare</MenuItem>
                <MenuItem value="Education">Education</MenuItem>
                <MenuItem value="Travel">Travel</MenuItem>
                <MenuItem value="Personal">Personal Care</MenuItem>
                <MenuItem value="Other">Other</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Budget Amount"
                type="number"
                value={budgetForm.amount}
                onChange={(e) => setBudgetForm({ ...budgetForm, amount: e.target.value })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Period"
                value={budgetForm.period}
                onChange={(e) => setBudgetForm({ ...budgetForm, period: e.target.value })}
                select
              >
                <MenuItem value="monthly">Monthly</MenuItem>
                <MenuItem value="annual">Annual</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Month"
                type="month"
                value={budgetForm.month}
                onChange={(e) => setBudgetForm({ ...budgetForm, month: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenBudgetDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveBudget} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default IncomeExpenses;

