import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Alert,
  Snackbar,
  Card,
  CardContent,
  Tabs,
  Tab,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import FilterListIcon from '@mui/icons-material/FilterList';
import { portfolioAPI } from '../services/api';

const Portfolio = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('pct_of_total'); // pct_of_total, unrealized_pnl, unrealized_pnl_pct, holding_period_days
  const [sortOrder, setSortOrder] = useState('desc'); // asc or desc
  const [openDialog, setOpenDialog] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [totalAmount, setTotalAmount] = useState(0);
  const [editingTotalAmount, setEditingTotalAmount] = useState(false);
  const [tempTotalAmount, setTempTotalAmount] = useState('');
  const [formData, setFormData] = useState({
    stock_symbol: '',
    stock_name: '',
    transaction_type: 'BUY',
    quantity: '',
    price: '',
    transaction_date: new Date().toISOString().split('T')[0],
    reason: '',
  });

  useEffect(() => {
    fetchTransactions();
    fetchSummary();
    fetchSettings();
  }, []);

  const fetchTransactions = async () => {
    try {
      const response = await portfolioAPI.getTransactions();
      setTransactions(response.data);
    } catch (error) {
      showSnackbar('Error fetching transactions', 'error');
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await portfolioAPI.getSummary();
      setSummary(response.data);
    } catch (error) {
      showSnackbar('Error fetching portfolio summary', 'error');
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await portfolioAPI.getSettings();
      setTotalAmount(response.data.total_amount || 0);
      setTempTotalAmount(response.data.total_amount || 0);
    } catch (error) {
      showSnackbar('Error fetching portfolio settings', 'error');
    }
  };

  const handleSaveTotalAmount = async () => {
    try {
      await portfolioAPI.updateSettings({ total_amount: parseFloat(tempTotalAmount) || 0 });
      setTotalAmount(parseFloat(tempTotalAmount) || 0);
      setEditingTotalAmount(false);
      showSnackbar('Total amount updated successfully', 'success');
    } catch (error) {
      showSnackbar('Error updating total amount', 'error');
    }
  };

  const handleOpenDialog = (transaction = null) => {
    if (transaction) {
      setEditingTransaction(transaction);
      setFormData({
        stock_symbol: transaction.stock_symbol,
        stock_name: transaction.stock_name,
        transaction_type: transaction.transaction_type,
        quantity: transaction.quantity,
        price: transaction.price,
        transaction_date: transaction.transaction_date.split('T')[0],
        reason: transaction.reason || '',
      });
    } else {
      setEditingTransaction(null);
      setFormData({
        stock_symbol: '',
        stock_name: '',
        transaction_type: 'BUY',
        quantity: '',
        price: '',
        transaction_date: new Date().toISOString().split('T')[0],
        reason: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingTransaction(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    // Validate required fields
    if (!formData.stock_symbol || !formData.stock_symbol.trim()) {
      showSnackbar('Stock symbol is required', 'error');
      return;
    }
    
    if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
      showSnackbar('Quantity must be greater than 0', 'error');
      return;
    }
    
    if (!formData.price || parseFloat(formData.price) <= 0) {
      showSnackbar('Price must be greater than 0', 'error');
      return;
    }
    
    if (!formData.transaction_date) {
      showSnackbar('Transaction date is required', 'error');
      return;
    }
    
    // Auto-populate stock name from symbol if not provided
    const submitData = {
      ...formData,
      stock_name: formData.stock_name || formData.stock_symbol.replace('.NS', '').replace('.BO', '')
    };
    
    try {
      if (editingTransaction) {
        await portfolioAPI.updateTransaction(editingTransaction.id, submitData);
        showSnackbar('Transaction updated successfully', 'success');
      } else {
        await portfolioAPI.createTransaction(submitData);
        showSnackbar('Transaction added successfully', 'success');
      }
      fetchTransactions();
      fetchSummary();
      handleCloseDialog();
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Error saving transaction';
      showSnackbar(errorMessage, 'error');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      try {
        await portfolioAPI.deleteTransaction(id);
        showSnackbar('Transaction deleted successfully', 'success');
        fetchTransactions();
        fetchSummary();
      } catch (error) {
        showSnackbar('Error deleting transaction', 'error');
      }
    }
  };

  const showSnackbar = (message, severity) => {
    setSnackbar({ open: true, message, severity });
  };

  const formatCurrency = (value) => {
    return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const getAllocationColor = (marketCap, percentage) => {
    // Determine threshold based on market cap
    let threshold;
    if (marketCap === 'Large') {
      threshold = 5;
    } else if (marketCap === 'Mid') {
      threshold = 3;
    } else if (marketCap === 'Small' || marketCap === 'Micro') {
      threshold = 2;
    } else {
      // Default threshold if market cap is not set
      return { bgcolor: '#60a5fa', color: 'white' }; // Blue (default)
    }

    // Color logic: Green includes up to +0.5% above threshold
    if (percentage > threshold + 0.5) {
      return { bgcolor: '#ef4444', color: 'white' }; // Red - over allocated (more than +0.5% above threshold)
    } else if (percentage >= threshold) {
      return { bgcolor: '#22c55e', color: 'white' }; // Green - good allocation (threshold to threshold+0.5%)
    } else {
      return { bgcolor: '#f59e0b', color: 'white' }; // Orange/Yellow - under allocated
    }
  };
  
  // Filter transactions by search term
  const filteredTransactions = transactions.filter(transaction =>
    transaction.stock_symbol?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatHoldingPeriod = (days) => {
    if (!days || days === 0) return '-';
    
    if (days < 30) {
      return `${days}D`;
    } else if (days < 365) {
      const months = Math.floor(days / 30);
      const remainingDays = days % 30;
      return remainingDays > 0 ? `${months}M ${remainingDays}D` : `${months}M`;
    } else {
      const years = Math.floor(days / 365);
      const months = Math.floor((days % 365) / 30);
      if (months > 0) {
        return `${years}Y ${months}M`;
      }
      return `${years}Y`;
    }
  };

  const handleSort = (column) => {
    if (sortBy === column) {
      // Toggle sort order
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // New column, default to descending
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const getSortedHoldings = () => {
    if (!summary || !summary.holdings) return [];
    
    const sorted = [...summary.holdings];
    sorted.sort((a, b) => {
      let aVal, bVal;
      
      if (sortBy === 'unrealized_pnl') {
        aVal = a.unrealized_pnl;
        bVal = b.unrealized_pnl;
      } else if (sortBy === 'unrealized_pnl_pct') {
        aVal = a.unrealized_pnl_pct;
        bVal = b.unrealized_pnl_pct;
      } else if (sortBy === 'pct_of_total') {
        // Calculate % of total for sorting
        aVal = totalAmount > 0 ? (a.invested_amount / totalAmount) * 100 : 0;
        bVal = totalAmount > 0 ? (b.invested_amount / totalAmount) * 100 : 0;
      } else if (sortBy === 'holding_period_days') {
        aVal = a.holding_period_days || 0;
        bVal = b.holding_period_days || 0;
      }
      
      if (sortOrder === 'asc') {
        return aVal - bVal;
      } else {
        return bVal - aVal;
      }
    });
    
    return sorted;
  };

  return (
    <Box>
      {/* Total Amount Setting */}
      <Box sx={{ mb: 3 }}>
        <Card sx={{ borderRadius: 3, bgcolor: 'rgba(96, 165, 250, 0.05)', border: '1px solid rgba(96, 165, 250, 0.2)' }}>
          <CardContent sx={{ py: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body1" fontWeight="bold">
                  Total Portfolio Amount (for % calculation):
                </Typography>
                {editingTotalAmount ? (
                  <TextField
                    size="small"
                    type="number"
                    value={tempTotalAmount}
                    onChange={(e) => setTempTotalAmount(e.target.value)}
                    placeholder="Enter total amount"
                    sx={{ width: 200 }}
                    InputProps={{
                      startAdornment: <Typography sx={{ mr: 1 }}>₹</Typography>
                    }}
                  />
                ) : (
                  <Chip
                    label={`₹${totalAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
                    color="primary"
                    sx={{ fontSize: '1rem', fontWeight: 'bold', px: 1 }}
                  />
                )}
              </Box>
              <Box>
                {editingTotalAmount ? (
                  <>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={handleSaveTotalAmount}
                      sx={{ mr: 1 }}
                    >
                      Save
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => {
                        setEditingTotalAmount(false);
                        setTempTotalAmount(totalAmount);
                      }}
                    >
                      Cancel
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={() => setEditingTotalAmount(true)}
                  >
                    Edit
                  </Button>
                )}
              </Box>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              This amount is used to calculate the % allocation of each stock in your portfolio
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Portfolio Summary Cards */}
      {summary && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ borderRadius: 3, height: '100%' }}>
              <CardContent>
                <Typography color="text.secondary" gutterBottom variant="body2">
                  Total Invested
                </Typography>
                <Typography variant="h6" component="div" fontWeight="bold">
                  {formatCurrency(summary.total_invested)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ borderRadius: 3, height: '100%' }}>
              <CardContent>
                <Typography color="text.secondary" gutterBottom variant="body2">
                  Current Value
                </Typography>
                <Typography variant="h6" component="div" fontWeight="bold">
                  {formatCurrency(summary.total_current_value)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ 
              borderRadius: 3,
              height: '100%',
              bgcolor: summary.total_realized_pnl >= 0 ? 'rgba(74, 222, 128, 0.1)' : 'rgba(248, 113, 113, 0.1)',
              border: `1px solid ${summary.total_realized_pnl >= 0 ? 'rgba(74, 222, 128, 0.3)' : 'rgba(248, 113, 113, 0.3)'}`,
            }}>
              <CardContent>
                <Typography color="text.secondary" gutterBottom variant="body2">
                  💰 Realized P/L
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography 
                    variant="h6" 
                    component="div"
                    fontWeight="bold"
                    color={summary.total_realized_pnl >= 0 ? 'success.main' : 'error.main'}
                  >
                    {formatCurrency(summary.total_realized_pnl)}
                  </Typography>
                  {summary.total_realized_pnl >= 0 ? (
                    <TrendingUpIcon color="success" sx={{ ml: 0.5, fontSize: 20 }} />
                  ) : (
                    <TrendingDownIcon color="error" sx={{ ml: 0.5, fontSize: 20 }} />
                  )}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Booked profit/loss
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ 
              borderRadius: 3,
              height: '100%',
              bgcolor: summary.total_unrealized_pnl >= 0 ? 'rgba(74, 222, 128, 0.1)' : 'rgba(248, 113, 113, 0.1)',
              border: `1px solid ${summary.total_unrealized_pnl >= 0 ? 'rgba(74, 222, 128, 0.3)' : 'rgba(248, 113, 113, 0.3)'}`,
            }}>
              <CardContent>
                <Typography color="text.secondary" gutterBottom variant="body2">
                  📈 Unrealized P/L
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography 
                    variant="h6" 
                    component="div"
                    fontWeight="bold"
                    color={summary.total_unrealized_pnl >= 0 ? 'success.main' : 'error.main'}
                  >
                    {formatCurrency(summary.total_unrealized_pnl)}
                  </Typography>
                  {summary.total_unrealized_pnl >= 0 ? (
                    <TrendingUpIcon color="success" sx={{ ml: 0.5, fontSize: 20 }} />
                  ) : (
                    <TrendingDownIcon color="error" sx={{ ml: 0.5, fontSize: 20 }} />
                  )}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {summary.total_unrealized_pnl_pct >= 0 ? '+' : ''}{summary.total_unrealized_pnl_pct.toFixed(2)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ 
              borderRadius: 3,
              height: '100%',
              bgcolor: summary.portfolio_day_change_pct >= 0 ? 'rgba(74, 222, 128, 0.1)' : 'rgba(248, 113, 113, 0.1)',
              border: `1px solid ${summary.portfolio_day_change_pct >= 0 ? 'rgba(74, 222, 128, 0.3)' : 'rgba(248, 113, 113, 0.3)'}`,
            }}>
              <CardContent>
                <Typography color="text.secondary" gutterBottom variant="body2">
                  1 Day Change
                </Typography>
                <Typography 
                  variant="h6" 
                  component="div"
                  fontWeight="bold"
                  color={summary.portfolio_day_change_pct >= 0 ? 'success.main' : 'error.main'}
                >
                  {summary.portfolio_day_change_pct >= 0 ? '+' : ''}{summary.portfolio_day_change_pct.toFixed(2)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ 
              borderRadius: 3,
              height: '100%',
              bgcolor: 'rgba(139, 92, 246, 0.1)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
            }}>
              <CardContent>
                <Typography color="text.secondary" gutterBottom variant="body2">
                  📊 XIRR
                </Typography>
                <Typography 
                  variant="h6" 
                  component="div"
                  fontWeight="bold"
                  color={summary.xirr && summary.xirr >= 0 ? 'success.main' : 'error.main'}
                >
                  {summary.xirr !== null && summary.xirr !== undefined ? 
                    `${summary.xirr >= 0 ? '+' : ''}${summary.xirr.toFixed(2)}%` : 
                    'N/A'
                  }
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Annualized return
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h5" component="h2" fontWeight="bold">
              My Portfolio
            </Typography>
            <Box sx={{ display: 'flex', gap: 3, mt: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h6" color="primary" fontWeight="bold">
                  {summary?.holdings?.length || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Holdings
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h6" color="primary" fontWeight="bold">
                  {transactions?.length || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Transactions
                </Typography>
              </Box>
            </Box>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ borderRadius: 2 }}
          >
            Add Transaction
          </Button>
        </Box>

        {/* Search Bar */}
        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Search by stock symbol..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <Box sx={{ display: 'flex', alignItems: 'center', mr: 1 }}>
                  <FilterListIcon fontSize="small" color="action" />
                </Box>
              ),
            }}
            sx={{ maxWidth: 400 }}
          />
          {searchTerm && (
            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
              Filtering by "{searchTerm}"
            </Typography>
          )}
        </Box>

        <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)} sx={{ mb: 2 }}>
          <Tab label="Current Holdings" />
          <Tab label="Transaction History" />
        </Tabs>

        {/* Current Holdings */}
        {currentTab === 0 && summary && (
          <TableContainer sx={{ maxHeight: 600 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 'bold' }}>Symbol</TableCell>
                  <TableCell align="right" sx={{ bgcolor: 'background.paper', fontWeight: 'bold' }}>Quantity</TableCell>
                  <TableCell align="right" sx={{ bgcolor: 'background.paper', fontWeight: 'bold' }}>Avg Price</TableCell>
                  <TableCell align="right" sx={{ bgcolor: 'background.paper', fontWeight: 'bold' }}>Current Price</TableCell>
                  <TableCell align="right" sx={{ bgcolor: 'background.paper', fontWeight: 'bold' }}>Invested</TableCell>
                  <TableCell 
                    align="right" 
                    onClick={() => handleSort('pct_of_total')}
                    sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' }, bgcolor: 'background.paper', fontWeight: 'bold' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                      % of Total {sortBy === 'pct_of_total' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </Box>
                  </TableCell>
                  <TableCell align="right" sx={{ bgcolor: 'background.paper', fontWeight: 'bold' }}>Current Value</TableCell>
                  <TableCell 
                    align="right" 
                    onClick={() => handleSort('unrealized_pnl')}
                    sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' }, bgcolor: 'background.paper', fontWeight: 'bold' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                      📈 Unrealized P/L {sortBy === 'unrealized_pnl' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </Box>
                  </TableCell>
                  <TableCell 
                    align="right" 
                    onClick={() => handleSort('unrealized_pnl_pct')}
                    sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' }, bgcolor: 'background.paper', fontWeight: 'bold' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                      Return % {sortBy === 'unrealized_pnl_pct' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </Box>
                  </TableCell>
                  <TableCell align="right" sx={{ bgcolor: 'background.paper', fontWeight: 'bold' }}>1D Change %</TableCell>
                  <TableCell 
                    align="right" 
                    onClick={() => handleSort('holding_period_days')}
                    sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' }, bgcolor: 'background.paper', fontWeight: 'bold' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                      Holding Period {sortBy === 'holding_period_days' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </Box>
                  </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {getSortedHoldings().filter(holding =>
                holding.symbol?.toLowerCase().includes(searchTerm.toLowerCase())
              ).map((holding) => (
                  <TableRow key={holding.symbol}>
                    <TableCell>
                      <Typography variant="body1" fontWeight="bold">
                        {holding.symbol.replace('.NS', '').replace('.BO', '')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{holding.quantity}</TableCell>
                    <TableCell align="right">{formatCurrency(holding.avg_price)}</TableCell>
                    <TableCell align="right">
                      <Typography variant="body1" fontWeight="bold" color="primary">
                        {formatCurrency(holding.current_price)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      {formatCurrency(holding.invested_amount)}
                    </TableCell>
                    <TableCell align="right">
                      {totalAmount > 0 ? (
                        (() => {
                          const pct = (holding.invested_amount / totalAmount) * 100;
                          const colorStyle = getAllocationColor(holding.market_cap, pct);
                          return (
                            <Chip
                              label={`${pct.toFixed(1)}%`}
                              size="small"
                              sx={{
                                ...colorStyle,
                                fontWeight: 'bold'
                              }}
                            />
                          );
                        })()
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          -
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">{formatCurrency(holding.current_value)}</TableCell>
                    <TableCell align="right">
                      <Typography
                        color={holding.unrealized_pnl >= 0 ? 'success.main' : 'error.main'}
                        fontWeight="bold"
                      >
                        {formatCurrency(holding.unrealized_pnl)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${holding.unrealized_pnl_pct >= 0 ? '+' : ''}${holding.unrealized_pnl_pct.toFixed(2)}%`}
                        color={holding.unrealized_pnl_pct >= 0 ? 'success' : 'error'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      {holding.day_change_pct !== null && holding.day_change_pct !== undefined ? (
                        <Chip
                          label={`${holding.day_change_pct >= 0 ? '+' : ''}${holding.day_change_pct.toFixed(2)}%`}
                          size="small"
                          sx={{
                            bgcolor: holding.day_change_pct >= 0 ? '#22c55e' : '#ef4444',
                            color: 'white',
                            fontWeight: 'bold'
                          }}
                        />
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          -
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={formatHoldingPeriod(holding.holding_period_days)}
                        size="small"
                        sx={{
                          bgcolor: '#3b82f6',
                          color: 'white',
                          fontWeight: 'bold'
                        }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              {getSortedHoldings().length === 0 && (
                  <TableRow>
                  <TableCell colSpan={11} align="center">
                    <Typography variant="body1" color="text.secondary" sx={{ py: 3 }}>
                      {searchTerm ? `No holdings found for "${searchTerm}"` : 'No holdings yet. Add your first transaction to get started!'}
                    </Typography>
                  </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {/* Transaction History */}
        {currentTab === 1 && (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Symbol</TableCell>
                  <TableCell align="right">Quantity</TableCell>
                  <TableCell align="right">Price</TableCell>
                  <TableCell align="right">Total</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredTransactions.map((transaction) => (
                  <TableRow key={transaction.id}>
                    <TableCell>{formatDate(transaction.transaction_date)}</TableCell>
                    <TableCell>
                      <Chip
                        label={transaction.transaction_type}
                        color={transaction.transaction_type === 'BUY' ? 'success' : 'error'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body1" fontWeight="bold">
                        {transaction.stock_symbol.replace('.NS', '').replace('.BO', '')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{transaction.quantity}</TableCell>
                    <TableCell align="right">{formatCurrency(transaction.price)}</TableCell>
                    <TableCell align="right">
                      {formatCurrency(transaction.quantity * transaction.price)}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 250 }}>
                        {transaction.reason || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleOpenDialog(transaction)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(transaction.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {filteredTransactions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body1" color="text.secondary" sx={{ py: 3 }}>
                      {searchTerm ? `No transactions found for "${searchTerm}"` : 'No transactions yet. Add your first transaction to get started!'}
                    </Typography>
                  </TableCell>
                </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Add/Edit Transaction Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle sx={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
          {editingTransaction ? 'Edit Transaction' : 'Add New Transaction'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Stock Symbol *"
                name="stock_symbol"
                value={formData.stock_symbol}
                onChange={handleInputChange}
                placeholder="e.g., RELIANCE.NS"
                required
                helperText="Stock symbol from your tracking list"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Transaction Type</InputLabel>
                <Select
                  name="transaction_type"
                  value={formData.transaction_type}
                  label="Transaction Type"
                  onChange={handleInputChange}
                >
                  <MenuItem value="BUY">BUY</MenuItem>
                  <MenuItem value="SELL">SELL</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Transaction Date"
                name="transaction_date"
                type="date"
                value={formData.transaction_date}
                onChange={handleInputChange}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Quantity"
                name="quantity"
                type="number"
                value={formData.quantity}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Price per Share"
                name="price"
                type="number"
                value={formData.price}
                onChange={handleInputChange}
                InputProps={{ startAdornment: '₹' }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Reason for Transaction"
                name="reason"
                multiline
                rows={3}
                value={formData.reason}
                onChange={handleInputChange}
                placeholder="Why did you make this transaction? Analysis, strategy, market conditions, etc."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 2.5 }}>
          <Button onClick={handleCloseDialog} sx={{ borderRadius: 2 }}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" sx={{ borderRadius: 2 }}>
            {editingTransaction ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Portfolio;

