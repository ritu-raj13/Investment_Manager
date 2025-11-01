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
  Chip,
  InputAdornment,
} from '@mui/material';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip
} from 'recharts';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import MoneyOffIcon from '@mui/icons-material/MoneyOff';
import DiamondIcon from '@mui/icons-material/Diamond';
import { savingsAPI, lendingAPI, otherInvestmentsAPI } from '../services/api';

const COLORS = ['#60a5fa', '#a78bfa', '#4ade80', '#fbbf24', '#f87171', '#fb923c', '#ec4899', '#8b5cf6'];

function Accounts() {
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Savings state
  const [savingsAccounts, setSavingsAccounts] = useState([]);
  const [savingsTransactions, setSavingsTransactions] = useState([]);
  const [savingsSummary, setSavingsSummary] = useState(null);
  
  // Lending state
  const [lendingList, setLendingList] = useState([]);
  const [lendingSummary, setLendingSummary] = useState(null);
  
  // Other Investments state
  const [otherInvestments, setOtherInvestments] = useState([]);

  // Dialog states
  const [openSavingsAccountDialog, setOpenSavingsAccountDialog] = useState(false);
  const [openSavingsTransactionDialog, setOpenSavingsTransactionDialog] = useState(false);
  const [openLendingDialog, setOpenLendingDialog] = useState(false);
  const [openOtherInvestmentDialog, setOpenOtherInvestmentDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  // Form states
  const [savingsAccountForm, setSavingsAccountForm] = useState({
    account_name: '',
    bank_name: '',
    account_number: '',
    account_type: 'savings',
    current_balance: '',
  });

  const [savingsTransactionForm, setSavingsTransactionForm] = useState({
    account_id: '',
    date: new Date().toISOString().split('T')[0],
    type: 'CREDIT',
    amount: '',
    description: '',
  });

  const [lendingForm, setLendingForm] = useState({
    borrower_name: '',
    amount_lent: '',
    interest_rate: '',
    start_date: new Date().toISOString().split('T')[0],
    due_date: '',
    amount_returned: '',
    status: 'active',
    notes: '',
  });

  const [otherInvestmentForm, setOtherInvestmentForm] = useState({
    name: '',
    type: 'gold',
    quantity: '',
    purchase_price: '',
    purchase_date: new Date().toISOString().split('T')[0],
    current_value: '',
    notes: '',
  });

  useEffect(() => {
    fetchData();
  }, [currentTab]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (currentTab === 0) {
        // Fetch Savings data
        const [accountsRes, transactionsRes, summaryRes] = await Promise.all([
          savingsAPI.getAccounts(),
          savingsAPI.getTransactions(),
          savingsAPI.getSummary(),
        ]);
        setSavingsAccounts(accountsRes.data);
        setSavingsTransactions(transactionsRes.data);
        setSavingsSummary(summaryRes.data);
      } else if (currentTab === 1) {
        // Fetch Lending data
        const [lendingRes, summaryRes] = await Promise.all([
          lendingAPI.getAll(),
          lendingAPI.getSummary(),
        ]);
        setLendingList(lendingRes.data);
        setLendingSummary(summaryRes.data);
      } else if (currentTab === 2) {
        // Fetch Other Investments
        const investmentsRes = await otherInvestmentsAPI.getAll();
        setOtherInvestments(investmentsRes.data);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load data');
      console.error('Data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Savings Account handlers
  const handleOpenSavingsAccountDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setSavingsAccountForm({
        account_name: item.account_name,
        bank_name: item.bank_name,
        account_number: item.account_number || '',
        account_type: item.account_type,
        current_balance: item.current_balance,
      });
    } else {
      setEditingItem(null);
      setSavingsAccountForm({
        account_name: '',
        bank_name: '',
        account_number: '',
        account_type: 'savings',
        current_balance: '',
      });
    }
    setOpenSavingsAccountDialog(true);
  };

  const handleSaveSavingsAccount = async () => {
    try {
      if (editingItem) {
        await savingsAPI.updateAccount(editingItem.id, savingsAccountForm);
      } else {
        await savingsAPI.createAccount(savingsAccountForm);
      }
      setOpenSavingsAccountDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save account');
    }
  };

  // Savings Transaction handlers
  const handleOpenSavingsTransactionDialog = () => {
    setSavingsTransactionForm({
      account_id: savingsAccounts[0]?.id || '',
      date: new Date().toISOString().split('T')[0],
      type: 'CREDIT',
      amount: '',
      description: '',
    });
    setOpenSavingsTransactionDialog(true);
  };

  const handleSaveSavingsTransaction = async () => {
    try {
      await savingsAPI.addTransaction(savingsTransactionForm);
      setOpenSavingsTransactionDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save transaction');
    }
  };

  // Lending handlers
  const handleOpenLendingDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setLendingForm({
        borrower_name: item.borrower_name,
        amount_lent: item.amount_lent,
        interest_rate: item.interest_rate || '',
        start_date: item.start_date,
        due_date: item.due_date || '',
        amount_returned: item.amount_returned || '',
        status: item.status,
        notes: item.notes || '',
      });
    } else {
      setEditingItem(null);
      setLendingForm({
        borrower_name: '',
        amount_lent: '',
        interest_rate: '',
        start_date: new Date().toISOString().split('T')[0],
        due_date: '',
        amount_returned: '',
        status: 'active',
        notes: '',
      });
    }
    setOpenLendingDialog(true);
  };

  const handleSaveLending = async () => {
    try {
      if (editingItem) {
        await lendingAPI.update(editingItem.id, lendingForm);
      } else {
        await lendingAPI.create(lendingForm);
      }
      setOpenLendingDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save lending record');
    }
  };

  const handleDeleteLending = async (id) => {
    if (window.confirm('Are you sure you want to delete this lending record?')) {
      try {
        await lendingAPI.delete(id);
        fetchData();
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to delete lending record');
      }
    }
  };

  // Other Investment handlers
  const handleOpenOtherInvestmentDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setOtherInvestmentForm({
        name: item.name,
        type: item.type,
        quantity: item.quantity || '',
        purchase_price: item.purchase_price,
        purchase_date: item.purchase_date,
        current_value: item.current_value || '',
        notes: item.notes || '',
      });
    } else {
      setEditingItem(null);
      setOtherInvestmentForm({
        name: '',
        type: 'gold',
        quantity: '',
        purchase_price: '',
        purchase_date: new Date().toISOString().split('T')[0],
        current_value: '',
        notes: '',
      });
    }
    setOpenOtherInvestmentDialog(true);
  };

  const handleSaveOtherInvestment = async () => {
    try {
      if (editingItem) {
        await otherInvestmentsAPI.update(editingItem.id, otherInvestmentForm);
      } else {
        await otherInvestmentsAPI.create(otherInvestmentForm);
      }
      setOpenOtherInvestmentDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save investment');
    }
  };

  const handleDeleteOtherInvestment = async (id) => {
    if (window.confirm('Are you sure you want to delete this investment?')) {
      try {
        await otherInvestmentsAPI.delete(id);
        fetchData();
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to delete investment');
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

  // Render Savings Tab
  const renderSavingsTab = () => {
    const accountTypeData = savingsAccounts.reduce((acc, account) => {
      const type = account.account_type || 'savings';
      if (!acc[type]) acc[type] = 0;
      acc[type] += parseFloat(account.current_balance) || 0;
      return acc;
    }, {});

    const chartData = Object.entries(accountTypeData).map(([name, value]) => ({ name, value }));

    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <AccountBalanceWalletIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Total Balance
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  ₹{savingsSummary?.total_balance?.toLocaleString('en-IN') || '0'}
                </Typography>
                <Typography variant="caption" color="white" sx={{ opacity: 0.8 }}>
                  {savingsAccounts.length} account(s)
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Account Type Distribution */}
        {chartData.length > 0 && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Account Type Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ₹${value.toLocaleString('en-IN')}`}
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
          </Grid>
        )}

        {/* Accounts Table */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Savings Accounts</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenSavingsAccountDialog()}
              >
                Add Account
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Account Name</TableCell>
                    <TableCell>Bank</TableCell>
                    <TableCell>Account Number</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Balance</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {savingsAccounts.map((account) => (
                    <TableRow key={account.id}>
                      <TableCell>{account.account_name}</TableCell>
                      <TableCell>{account.bank_name}</TableCell>
                      <TableCell>{account.account_number || '-'}</TableCell>
                      <TableCell>
                        <Chip label={account.account_type} size="small" color="primary" />
                      </TableCell>
                      <TableCell align="right">
                        <Typography fontWeight="bold">
                          ₹{parseFloat(account.current_balance).toLocaleString('en-IN')}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenSavingsAccountDialog(account)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {savingsAccounts.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No accounts yet. Click "Add Account" to get started.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Transactions */}
        {savingsAccounts.length > 0 && (
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Recent Transactions</Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={handleOpenSavingsTransactionDialog}
                >
                  Add Transaction
                </Button>
              </Box>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Account</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell>Description</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {savingsTransactions.slice(-10).reverse().map((transaction) => {
                      const account = savingsAccounts.find(a => a.id === transaction.account_id);
                      return (
                        <TableRow key={transaction.id}>
                          <TableCell>{new Date(transaction.date).toLocaleDateString()}</TableCell>
                          <TableCell>{account?.account_name || '-'}</TableCell>
                          <TableCell>
                            <Chip
                              label={transaction.type}
                              size="small"
                              color={transaction.type === 'CREDIT' ? 'success' : 'error'}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography
                              color={transaction.type === 'CREDIT' ? 'success.main' : 'error.main'}
                              fontWeight="bold"
                            >
                              {transaction.type === 'CREDIT' ? '+' : '-'}
                              ₹{parseFloat(transaction.amount).toLocaleString('en-IN')}
                            </Typography>
                          </TableCell>
                          <TableCell>{transaction.description || '-'}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>

              {savingsTransactions.length === 0 && (
                <Box textAlign="center" py={4}>
                  <Typography color="text.secondary">
                    No transactions yet. Click "Add Transaction" to get started.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        )}
      </Box>
    );
  };

  // Render Lending Tab
  const renderLendingTab = () => {
    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <MoneyOffIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Total Lent
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  ₹{lendingSummary?.total_lent?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Active Loans
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {lendingSummary?.active_count || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Amount Recovered
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  ₹{lendingSummary?.total_recovered?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Outstanding
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="warning.main">
                  ₹{lendingSummary?.outstanding?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Lending Table */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Loans Given</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenLendingDialog()}
              >
                Add Loan
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Borrower</TableCell>
                    <TableCell align="right">Amount Lent</TableCell>
                    <TableCell align="right">Interest Rate</TableCell>
                    <TableCell>Start Date</TableCell>
                    <TableCell>Due Date</TableCell>
                    <TableCell align="right">Returned</TableCell>
                    <TableCell align="right">Outstanding</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {lendingList.map((loan) => {
                    const outstanding = parseFloat(loan.amount_lent) - (parseFloat(loan.amount_returned) || 0);
                    return (
                      <TableRow key={loan.id}>
                        <TableCell>
                          <Typography fontWeight="bold">{loan.borrower_name}</Typography>
                          {loan.notes && (
                            <Typography variant="caption" color="text.secondary">
                              {loan.notes}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell align="right">
                          ₹{parseFloat(loan.amount_lent).toLocaleString('en-IN')}
                        </TableCell>
                        <TableCell align="right">
                          {loan.interest_rate ? `${loan.interest_rate}%` : '-'}
                        </TableCell>
                        <TableCell>{new Date(loan.start_date).toLocaleDateString()}</TableCell>
                        <TableCell>
                          {loan.due_date ? new Date(loan.due_date).toLocaleDateString() : '-'}
                        </TableCell>
                        <TableCell align="right">
                          <Typography color="success.main">
                            ₹{(parseFloat(loan.amount_returned) || 0).toLocaleString('en-IN')}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography color="warning.main" fontWeight="bold">
                            ₹{outstanding.toLocaleString('en-IN')}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={loan.status}
                            size="small"
                            color={loan.status === 'active' ? 'warning' : 'success'}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => handleOpenLendingDialog(loan)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteLending(loan.id)}
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

            {lendingList.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No lending records yet. Click "Add Loan" to get started.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };

  // Render Other Investments Tab
  const renderOtherInvestmentsTab = () => {
    const typeData = otherInvestments.reduce((acc, inv) => {
      const type = inv.type || 'other';
      if (!acc[type]) acc[type] = 0;
      acc[type] += parseFloat(inv.current_value || inv.purchase_price) || 0;
      return acc;
    }, {});

    const chartData = Object.entries(typeData).map(([name, value]) => ({ name, value }));

    const totalInvested = otherInvestments.reduce((sum, inv) => sum + (parseFloat(inv.purchase_price) || 0), 0);
    const totalValue = otherInvestments.reduce((sum, inv) => sum + (parseFloat(inv.current_value || inv.purchase_price) || 0), 0);
    const totalGain = totalValue - totalInvested;

    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Investments
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {otherInvestments.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Invested
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  ₹{totalInvested.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Current Value
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="primary.main">
                  ₹{totalValue.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Gain/Loss
                </Typography>
                <Typography 
                  variant="h5" 
                  fontWeight="bold"
                  color={totalGain >= 0 ? 'success.main' : 'error.main'}
                >
                  {totalGain >= 0 ? '+' : ''}₹{totalGain.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Type Distribution */}
        {chartData.length > 0 && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Investment Type Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ₹${value.toLocaleString('en-IN')}`}
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
          </Grid>
        )}

        {/* Investments Table */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Other Investments</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenOtherInvestmentDialog()}
              >
                Add Investment
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Quantity</TableCell>
                    <TableCell align="right">Purchase Price</TableCell>
                    <TableCell>Purchase Date</TableCell>
                    <TableCell align="right">Current Value</TableCell>
                    <TableCell align="right">Gain/Loss</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {otherInvestments.map((investment) => {
                    const purchasePrice = parseFloat(investment.purchase_price) || 0;
                    const currentValue = parseFloat(investment.current_value || investment.purchase_price) || 0;
                    const gain = currentValue - purchasePrice;

                    return (
                      <TableRow key={investment.id}>
                        <TableCell>
                          <Typography fontWeight="bold">{investment.name}</Typography>
                          {investment.notes && (
                            <Typography variant="caption" color="text.secondary">
                              {investment.notes}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Chip label={investment.type} size="small" color="primary" />
                        </TableCell>
                        <TableCell>{investment.quantity || '-'}</TableCell>
                        <TableCell align="right">
                          ₹{purchasePrice.toLocaleString('en-IN')}
                        </TableCell>
                        <TableCell>{new Date(investment.purchase_date).toLocaleDateString()}</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold">
                            ₹{currentValue.toLocaleString('en-IN')}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography 
                            color={gain >= 0 ? 'success.main' : 'error.main'}
                            fontWeight="bold"
                          >
                            {gain >= 0 ? '+' : ''}₹{gain.toLocaleString('en-IN')}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => handleOpenOtherInvestmentDialog(investment)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteOtherInvestment(investment.id)}
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

            {otherInvestments.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No investments yet. Click "Add Investment" to get started.
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
        Accounts & Other Investments
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, val) => setCurrentTab(val)}>
          <Tab label="Savings Accounts" />
          <Tab label="Lending" />
          <Tab label="Other Investments" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {currentTab === 0 && renderSavingsTab()}
      {currentTab === 1 && renderLendingTab()}
      {currentTab === 2 && renderOtherInvestmentsTab()}

      {/* Savings Account Dialog */}
      <Dialog open={openSavingsAccountDialog} onClose={() => setOpenSavingsAccountDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Account' : 'Add Savings Account'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Account Name"
                value={savingsAccountForm.account_name}
                onChange={(e) => setSavingsAccountForm({ ...savingsAccountForm, account_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Bank Name"
                value={savingsAccountForm.bank_name}
                onChange={(e) => setSavingsAccountForm({ ...savingsAccountForm, bank_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Account Number (Optional)"
                value={savingsAccountForm.account_number}
                onChange={(e) => setSavingsAccountForm({ ...savingsAccountForm, account_number: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Account Type"
                value={savingsAccountForm.account_type}
                onChange={(e) => setSavingsAccountForm({ ...savingsAccountForm, account_type: e.target.value })}
                select
                required
              >
                <MenuItem value="savings">Savings</MenuItem>
                <MenuItem value="current">Current</MenuItem>
                <MenuItem value="salary">Salary</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Current Balance"
                type="number"
                value={savingsAccountForm.current_balance}
                onChange={(e) => setSavingsAccountForm({ ...savingsAccountForm, current_balance: e.target.value })}
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenSavingsAccountDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveSavingsAccount} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Savings Transaction Dialog */}
      <Dialog open={openSavingsTransactionDialog} onClose={() => setOpenSavingsTransactionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Transaction</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Account"
                value={savingsTransactionForm.account_id}
                onChange={(e) => setSavingsTransactionForm({ ...savingsTransactionForm, account_id: e.target.value })}
                select
                required
              >
                {savingsAccounts.map((account) => (
                  <MenuItem key={account.id} value={account.id}>
                    {account.account_name} - {account.bank_name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Date"
                type="date"
                value={savingsTransactionForm.date}
                onChange={(e) => setSavingsTransactionForm({ ...savingsTransactionForm, date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Type"
                value={savingsTransactionForm.type}
                onChange={(e) => setSavingsTransactionForm({ ...savingsTransactionForm, type: e.target.value })}
                select
                required
              >
                <MenuItem value="CREDIT">Credit (+)</MenuItem>
                <MenuItem value="DEBIT">Debit (-)</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={savingsTransactionForm.amount}
                onChange={(e) => setSavingsTransactionForm({ ...savingsTransactionForm, amount: e.target.value })}
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description (Optional)"
                multiline
                rows={2}
                value={savingsTransactionForm.description}
                onChange={(e) => setSavingsTransactionForm({ ...savingsTransactionForm, description: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenSavingsTransactionDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveSavingsTransaction} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Lending Dialog */}
      <Dialog open={openLendingDialog} onClose={() => setOpenLendingDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Loan' : 'Add Loan'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Borrower Name"
                value={lendingForm.borrower_name}
                onChange={(e) => setLendingForm({ ...lendingForm, borrower_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Amount Lent"
                type="number"
                value={lendingForm.amount_lent}
                onChange={(e) => setLendingForm({ ...lendingForm, amount_lent: e.target.value })}
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Interest Rate (Optional)"
                type="number"
                value={lendingForm.interest_rate}
                onChange={(e) => setLendingForm({ ...lendingForm, interest_rate: e.target.value })}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                value={lendingForm.start_date}
                onChange={(e) => setLendingForm({ ...lendingForm, start_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Due Date (Optional)"
                type="date"
                value={lendingForm.due_date}
                onChange={(e) => setLendingForm({ ...lendingForm, due_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Amount Returned"
                type="number"
                value={lendingForm.amount_returned}
                onChange={(e) => setLendingForm({ ...lendingForm, amount_returned: e.target.value })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Status"
                value={lendingForm.status}
                onChange={(e) => setLendingForm({ ...lendingForm, status: e.target.value })}
                select
                required
              >
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="repaid">Repaid</MenuItem>
                <MenuItem value="defaulted">Defaulted</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes (Optional)"
                multiline
                rows={2}
                value={lendingForm.notes}
                onChange={(e) => setLendingForm({ ...lendingForm, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenLendingDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveLending} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Other Investment Dialog */}
      <Dialog open={openOtherInvestmentDialog} onClose={() => setOpenOtherInvestmentDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Investment' : 'Add Investment'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Investment Name"
                value={otherInvestmentForm.name}
                onChange={(e) => setOtherInvestmentForm({ ...otherInvestmentForm, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Type"
                value={otherInvestmentForm.type}
                onChange={(e) => setOtherInvestmentForm({ ...otherInvestmentForm, type: e.target.value })}
                select
                required
              >
                <MenuItem value="gold">Gold</MenuItem>
                <MenuItem value="silver">Silver</MenuItem>
                <MenuItem value="bonds">Bonds</MenuItem>
                <MenuItem value="real_estate">Real Estate</MenuItem>
                <MenuItem value="crypto">Cryptocurrency</MenuItem>
                <MenuItem value="art">Art/Collectibles</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Quantity (Optional)"
                value={otherInvestmentForm.quantity}
                onChange={(e) => setOtherInvestmentForm({ ...otherInvestmentForm, quantity: e.target.value })}
                placeholder="e.g., 10 grams, 2 units"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Purchase Price"
                type="number"
                value={otherInvestmentForm.purchase_price}
                onChange={(e) => setOtherInvestmentForm({ ...otherInvestmentForm, purchase_price: e.target.value })}
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Purchase Date"
                type="date"
                value={otherInvestmentForm.purchase_date}
                onChange={(e) => setOtherInvestmentForm({ ...otherInvestmentForm, purchase_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Current Value (Optional)"
                type="number"
                value={otherInvestmentForm.current_value}
                onChange={(e) => setOtherInvestmentForm({ ...otherInvestmentForm, current_value: e.target.value })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
                helperText="Leave empty to use purchase price"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes (Optional)"
                multiline
                rows={2}
                value={otherInvestmentForm.notes}
                onChange={(e) => setOtherInvestmentForm({ ...otherInvestmentForm, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenOtherInvestmentDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveOtherInvestment} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Accounts;

