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
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { mutualFundsAPI } from '../services/api';

const COLORS = ['#60a5fa', '#a78bfa', '#4ade80', '#fbbf24', '#f87171', '#fb923c', '#ec4899', '#8b5cf6'];

function MutualFunds() {
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Schemes state
  const [schemes, setSchemes] = useState([]);
  
  // Transactions state
  const [transactions, setTransactions] = useState([]);
  
  // Holdings state
  const [holdings, setHoldings] = useState([]);
  const [holdingsSummary, setHoldingsSummary] = useState(null);

  // Dialog states
  const [openSchemeDialog, setOpenSchemeDialog] = useState(false);
  const [openTransactionDialog, setOpenTransactionDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  // Form states
  const [schemeForm, setSchemeForm] = useState({
    name: '',
    scheme_code: '',
    category: '',
    sub_category: '',
    amc: '',
    nav: '',
    expense_ratio: '',
  });

  const [transactionForm, setTransactionForm] = useState({
    scheme_id: '',
    transaction_type: 'BUY',
    units: '',
    nav: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    is_sip: false,
  });

  useEffect(() => {
    fetchData();
  }, [currentTab]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (currentTab === 0) {
        // Fetch Schemes
        const schemesRes = await mutualFundsAPI.getSchemes();
        setSchemes(schemesRes.data);
      } else if (currentTab === 1) {
        // Fetch Transactions and Schemes (needed for dropdown)
        const [transactionsRes, schemesRes] = await Promise.all([
          mutualFundsAPI.getTransactions(),
          mutualFundsAPI.getSchemes(),
        ]);
        setTransactions(transactionsRes.data);
        setSchemes(schemesRes.data);
      } else if (currentTab === 2) {
        // Fetch Holdings
        const holdingsRes = await mutualFundsAPI.getHoldings();
        setHoldings(holdingsRes.data);
        
        // Calculate summary
        const summary = {
          total_invested: holdingsRes.data.reduce((sum, h) => sum + (h.invested || 0), 0),
          current_value: holdingsRes.data.reduce((sum, h) => sum + (h.current_value || 0), 0),
          total_units: holdingsRes.data.reduce((sum, h) => sum + (h.units || 0), 0),
        };
        summary.unrealized_pl = summary.current_value - summary.total_invested;
        summary.return_percent = summary.total_invested > 0 
          ? ((summary.unrealized_pl / summary.total_invested) * 100).toFixed(2)
          : 0;
        setHoldingsSummary(summary);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load data');
      console.error('Data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Scheme handlers
  const handleOpenSchemeDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setSchemeForm({
        name: item.name,
        scheme_code: item.scheme_code || '',
        category: item.category,
        sub_category: item.sub_category || '',
        amc: item.amc || '',
        nav: item.nav || '',
        expense_ratio: item.expense_ratio || '',
      });
    } else {
      setEditingItem(null);
      setSchemeForm({
        name: '',
        scheme_code: '',
        category: '',
        sub_category: '',
        amc: '',
        nav: '',
        expense_ratio: '',
      });
    }
    setOpenSchemeDialog(true);
  };

  const handleSaveScheme = async () => {
    try {
      if (editingItem) {
        await mutualFundsAPI.updateScheme(editingItem.id, schemeForm);
      } else {
        await mutualFundsAPI.createScheme(schemeForm);
      }
      setOpenSchemeDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save scheme');
    }
  };

  const handleDeleteScheme = async (id) => {
    if (window.confirm('Are you sure you want to delete this scheme? This will also delete all associated transactions.')) {
      try {
        await mutualFundsAPI.deleteScheme(id);
        fetchData();
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to delete scheme');
      }
    }
  };

  // Transaction handlers
  const handleOpenTransactionDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setTransactionForm({
        scheme_id: item.scheme_id,
        transaction_type: item.transaction_type,
        units: item.units,
        nav: item.nav,
        amount: item.amount,
        date: item.date,
        is_sip: item.is_sip || false,
      });
    } else {
      setEditingItem(null);
      setTransactionForm({
        scheme_id: '',
        transaction_type: 'BUY',
        units: '',
        nav: '',
        amount: '',
        date: new Date().toISOString().split('T')[0],
        is_sip: false,
      });
    }
    setOpenTransactionDialog(true);
  };

  const handleSaveTransaction = async () => {
    try {
      if (editingItem) {
        await mutualFundsAPI.updateTransaction(editingItem.id, transactionForm);
      } else {
        await mutualFundsAPI.createTransaction(transactionForm);
      }
      setOpenTransactionDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save transaction');
    }
  };

  const handleDeleteTransaction = async (id) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      try {
        await mutualFundsAPI.deleteTransaction(id);
        fetchData();
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to delete transaction');
      }
    }
  };

  // Calculate amount from units and NAV
  const handleUnitsOrNavChange = (field, value) => {
    const newForm = { ...transactionForm, [field]: value };
    if (newForm.units && newForm.nav) {
      newForm.amount = (parseFloat(newForm.units) * parseFloat(newForm.nav)).toFixed(2);
    }
    setTransactionForm(newForm);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Render Schemes Tab
  const renderSchemesTab = () => {
    const categoryData = schemes.reduce((acc, scheme) => {
      const cat = scheme.category || 'Other';
      if (!acc[cat]) acc[cat] = 0;
      acc[cat]++;
      return acc;
    }, {});

    const chartData = Object.entries(categoryData).map(([name, value]) => ({ name, value }));

    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <ShowChartIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Total Schemes
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  {schemes.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Category Distribution */}
        {chartData.length > 0 && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Schemes by Category
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Schemes Table */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Mutual Fund Schemes</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenSchemeDialog()}
              >
                Add Scheme
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Scheme Name</TableCell>
                    <TableCell>Code</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>AMC</TableCell>
                    <TableCell>Current NAV</TableCell>
                    <TableCell>Expense Ratio</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {schemes.map((scheme) => (
                    <TableRow key={scheme.id}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {scheme.name}
                        </Typography>
                        {scheme.sub_category && (
                          <Typography variant="caption" color="text.secondary">
                            {scheme.sub_category}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{scheme.scheme_code || '-'}</TableCell>
                      <TableCell>
                        <Chip label={scheme.category} size="small" color="primary" />
                      </TableCell>
                      <TableCell>{scheme.amc || '-'}</TableCell>
                      <TableCell>₹{scheme.nav || '-'}</TableCell>
                      <TableCell>{scheme.expense_ratio ? `${scheme.expense_ratio}%` : '-'}</TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenSchemeDialog(scheme)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteScheme(scheme.id)}
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

            {schemes.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No schemes added yet. Click "Add Scheme" to get started.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };

  // Render Transactions Tab
  const renderTransactionsTab = () => {
    const sipTransactions = transactions.filter(t => t.is_sip);
    const regularTransactions = transactions.filter(t => !t.is_sip);

    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Transactions
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {transactions.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  BUY Transactions
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  {transactions.filter(t => t.transaction_type === 'BUY').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  SELL Transactions
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="error.main">
                  {transactions.filter(t => t.transaction_type === 'SELL').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  SIP Transactions
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="primary.main">
                  {sipTransactions.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Transactions Table */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Transactions</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenTransactionDialog()}
              >
                Add Transaction
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Scheme</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Units</TableCell>
                    <TableCell>NAV</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell>SIP</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transactions.map((transaction) => {
                    const scheme = schemes.find(s => s.id === transaction.scheme_id);
                    return (
                      <TableRow key={transaction.id}>
                        <TableCell>{new Date(transaction.date).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {scheme?.name || 'Unknown Scheme'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={transaction.transaction_type}
                            size="small"
                            color={transaction.transaction_type === 'BUY' ? 'success' : 'error'}
                          />
                        </TableCell>
                        <TableCell>{transaction.units}</TableCell>
                        <TableCell>₹{transaction.nav}</TableCell>
                        <TableCell>
                          <Typography fontWeight="bold">
                            ₹{transaction.amount.toLocaleString('en-IN')}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {transaction.is_sip && <Chip label="SIP" size="small" color="primary" />}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => handleOpenTransactionDialog(transaction)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteTransaction(transaction.id)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>

            {transactions.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No transactions yet. Click "Add Transaction" to get started.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };

  // Render Holdings Tab
  const renderHoldingsTab = () => {
    const categoryAllocation = holdings.reduce((acc, holding) => {
      const scheme = schemes.find(s => s.id === holding.scheme_id);
      const category = scheme?.category || 'Other';
      if (!acc[category]) acc[category] = 0;
      acc[category] += holding.current_value || 0;
      return acc;
    }, {});

    const chartData = Object.entries(categoryAllocation).map(([name, value]) => ({ name, value }));

    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <AccountBalanceWalletIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Total Invested
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  ₹{holdingsSummary?.total_invested?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <ShowChartIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Current Value
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  ₹{holdingsSummary?.current_value?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: holdingsSummary?.unrealized_pl >= 0 
              ? 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
              : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
            }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <TrendingUpIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Unrealized P/L
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  {holdingsSummary?.unrealized_pl >= 0 ? '+' : ''}
                  ₹{holdingsSummary?.unrealized_pl?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Return %
                </Typography>
                <Typography 
                  variant="h4" 
                  fontWeight="bold"
                  color={holdingsSummary?.return_percent >= 0 ? 'success.main' : 'error.main'}
                >
                  {holdingsSummary?.return_percent >= 0 ? '+' : ''}
                  {holdingsSummary?.return_percent || '0'}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Category Allocation */}
        {chartData.length > 0 && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Category Allocation
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {chartData.map((entry, index) => (
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
                    {Object.entries(categoryAllocation).map(([category, value], index) => (
                      <Box key={index} sx={{ mb: 2 }}>
                        <Box display="flex" justifyContent="space-between" mb={0.5}>
                          <Typography variant="body2">{category}</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            ₹{value.toLocaleString('en-IN')}
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
                              width: `${(value / holdingsSummary?.current_value) * 100}%`,
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

        {/* Holdings Table */}
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>
              Current Holdings
            </Typography>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Scheme</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Units</TableCell>
                    <TableCell align="right">Avg NAV</TableCell>
                    <TableCell align="right">Current NAV</TableCell>
                    <TableCell align="right">Invested</TableCell>
                    <TableCell align="right">Current Value</TableCell>
                    <TableCell align="right">P/L</TableCell>
                    <TableCell align="right">Return %</TableCell>
                    <TableCell align="right">XIRR</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {holdings.map((holding) => {
                    const scheme = schemes.find(s => s.id === holding.scheme_id);
                    const pl = (holding.current_value || 0) - (holding.invested || 0);
                    const returnPercent = holding.invested > 0 
                      ? ((pl / holding.invested) * 100).toFixed(2)
                      : 0;

                    return (
                      <TableRow key={holding.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {scheme?.name || 'Unknown Scheme'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={scheme?.category || 'N/A'} size="small" />
                        </TableCell>
                        <TableCell align="right">{holding.units?.toFixed(3) || 0}</TableCell>
                        <TableCell align="right">₹{holding.avg_nav?.toFixed(2) || 0}</TableCell>
                        <TableCell align="right">₹{holding.current_nav?.toFixed(2) || scheme?.nav || 0}</TableCell>
                        <TableCell align="right">
                          ₹{holding.invested?.toLocaleString('en-IN') || 0}
                        </TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold">
                            ₹{holding.current_value?.toLocaleString('en-IN') || 0}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography color={pl >= 0 ? 'success.main' : 'error.main'} fontWeight="bold">
                            {pl >= 0 ? '+' : ''}₹{pl.toLocaleString('en-IN')}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography color={returnPercent >= 0 ? 'success.main' : 'error.main'}>
                            {returnPercent >= 0 ? '+' : ''}{returnPercent}%
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {holding.xirr ? (
                            <Typography color={holding.xirr >= 0 ? 'success.main' : 'error.main'}>
                              {holding.xirr >= 0 ? '+' : ''}{holding.xirr}%
                            </Typography>
                          ) : (
                            <Typography color="text.secondary">N/A</Typography>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>

            {holdings.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No holdings yet. Add schemes and transactions to see your holdings.
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
        Mutual Funds
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, val) => setCurrentTab(val)}>
          <Tab label="Schemes" />
          <Tab label="Transactions" />
          <Tab label="Holdings" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {currentTab === 0 && renderSchemesTab()}
      {currentTab === 1 && renderTransactionsTab()}
      {currentTab === 2 && renderHoldingsTab()}

      {/* Scheme Dialog */}
      <Dialog open={openSchemeDialog} onClose={() => setOpenSchemeDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Scheme' : 'Add Scheme'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Scheme Name"
                value={schemeForm.name}
                onChange={(e) => setSchemeForm({ ...schemeForm, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Scheme Code (Optional)"
                value={schemeForm.scheme_code}
                onChange={(e) => setSchemeForm({ ...schemeForm, scheme_code: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="AMC (Optional)"
                value={schemeForm.amc}
                onChange={(e) => setSchemeForm({ ...schemeForm, amc: e.target.value })}
                placeholder="e.g., HDFC, ICICI, SBI"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Category"
                value={schemeForm.category}
                onChange={(e) => setSchemeForm({ ...schemeForm, category: e.target.value })}
                select
                required
              >
                <MenuItem value="Equity">Equity</MenuItem>
                <MenuItem value="Debt">Debt</MenuItem>
                <MenuItem value="Hybrid">Hybrid</MenuItem>
                <MenuItem value="Index">Index</MenuItem>
                <MenuItem value="ELSS">ELSS</MenuItem>
                <MenuItem value="Liquid">Liquid</MenuItem>
                <MenuItem value="Other">Other</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Sub-Category (Optional)"
                value={schemeForm.sub_category}
                onChange={(e) => setSchemeForm({ ...schemeForm, sub_category: e.target.value })}
                placeholder="e.g., Large Cap, Mid Cap"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Current NAV (Optional)"
                type="number"
                value={schemeForm.nav}
                onChange={(e) => setSchemeForm({ ...schemeForm, nav: e.target.value })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Expense Ratio (Optional)"
                type="number"
                value={schemeForm.expense_ratio}
                onChange={(e) => setSchemeForm({ ...schemeForm, expense_ratio: e.target.value })}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenSchemeDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveScheme} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Transaction Dialog */}
      <Dialog open={openTransactionDialog} onClose={() => setOpenTransactionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Transaction' : 'Add Transaction'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Scheme"
                value={transactionForm.scheme_id}
                onChange={(e) => setTransactionForm({ ...transactionForm, scheme_id: e.target.value })}
                select
                required
              >
                {schemes.map((scheme) => (
                  <MenuItem key={scheme.id} value={scheme.id}>
                    {scheme.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Transaction Type"
                value={transactionForm.transaction_type}
                onChange={(e) => setTransactionForm({ ...transactionForm, transaction_type: e.target.value })}
                select
                required
              >
                <MenuItem value="BUY">BUY</MenuItem>
                <MenuItem value="SELL">SELL</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Date"
                type="date"
                value={transactionForm.date}
                onChange={(e) => setTransactionForm({ ...transactionForm, date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Units"
                type="number"
                value={transactionForm.units}
                onChange={(e) => handleUnitsOrNavChange('units', e.target.value)}
                required
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="NAV"
                type="number"
                value={transactionForm.nav}
                onChange={(e) => handleUnitsOrNavChange('nav', e.target.value)}
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={transactionForm.amount}
                onChange={(e) => setTransactionForm({ ...transactionForm, amount: e.target.value })}
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
                helperText="Auto-calculated"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Is this a SIP transaction?</InputLabel>
                <Select
                  value={transactionForm.is_sip}
                  onChange={(e) => setTransactionForm({ ...transactionForm, is_sip: e.target.value })}
                  label="Is this a SIP transaction?"
                >
                  <MenuItem value={false}>No</MenuItem>
                  <MenuItem value={true}>Yes</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenTransactionDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveTransaction} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default MutualFunds;

