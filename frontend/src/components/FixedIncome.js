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
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import SavingsIcon from '@mui/icons-material/Savings';
import WarningIcon from '@mui/icons-material/Warning';
import { fixedDepositsAPI, epfAPI, npsAPI } from '../services/api';

function FixedIncome() {
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // FD state
  const [fdList, setFdList] = useState([]);
  const [upcomingMaturity, setUpcomingMaturity] = useState([]);
  
  // EPF state
  const [epfAccounts, setEpfAccounts] = useState([]);
  const [epfContributions, setEpfContributions] = useState([]);
  const [epfSummary, setEpfSummary] = useState(null);
  
  // NPS state
  const [npsAccounts, setNpsAccounts] = useState([]);
  const [npsContributions, setNpsContributions] = useState([]);
  const [npsSummary, setNpsSummary] = useState(null);

  // Dialog states
  const [openFdDialog, setOpenFdDialog] = useState(false);
  const [openEpfAccountDialog, setOpenEpfAccountDialog] = useState(false);
  const [openEpfContributionDialog, setOpenEpfContributionDialog] = useState(false);
  const [openNpsAccountDialog, setOpenNpsAccountDialog] = useState(false);
  const [openNpsContributionDialog, setOpenNpsContributionDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  // Form states
  const [fdForm, setFdForm] = useState({
    bank_name: '',
    account_number: '',
    principal: '',
    interest_rate: '',
    start_date: new Date().toISOString().split('T')[0],
    maturity_date: '',
    maturity_amount: '',
    frequency: 'quarterly',
  });

  const [epfAccountForm, setEpfAccountForm] = useState({
    account_number: '',
    employer_name: '',
    uan: '',
  });

  const [epfContributionForm, setEpfContributionForm] = useState({
    account_id: '',
    month: new Date().toISOString().slice(0, 7),
    employee_contribution: '',
    employer_contribution: '',
    interest_earned: '',
  });

  const [npsAccountForm, setNpsAccountForm] = useState({
    pran: '',
    account_type: 'Tier 1',
    sector: 'private',
  });

  const [npsContributionForm, setNpsContributionForm] = useState({
    account_id: '',
    date: new Date().toISOString().split('T')[0],
    amount: '',
    nav: '',
    units: '',
  });

  useEffect(() => {
    fetchData();
  }, [currentTab]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (currentTab === 0) {
        // Fetch FD data
        const [fdRes, upcomingRes] = await Promise.all([
          fixedDepositsAPI.getAll(),
          fixedDepositsAPI.getUpcomingMaturity(),
        ]);
        setFdList(fdRes.data);
        setUpcomingMaturity(upcomingRes.data);
      } else if (currentTab === 1) {
        // Fetch EPF data
        const [accountsRes, contributionsRes, summaryRes] = await Promise.all([
          epfAPI.getAccounts(),
          epfAPI.getContributions(),
          epfAPI.getSummary(),
        ]);
        setEpfAccounts(accountsRes.data);
        setEpfContributions(contributionsRes.data);
        setEpfSummary(summaryRes.data);
      } else if (currentTab === 2) {
        // Fetch NPS data
        const [accountsRes, contributionsRes, summaryRes] = await Promise.all([
          npsAPI.getAccounts(),
          npsAPI.getContributions(),
          npsAPI.getSummary(),
        ]);
        setNpsAccounts(accountsRes.data);
        setNpsContributions(contributionsRes.data);
        setNpsSummary(summaryRes.data);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load data');
      console.error('Data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // FD handlers
  const handleOpenFdDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setFdForm({
        bank_name: item.bank_name,
        account_number: item.account_number || '',
        principal: item.principal,
        interest_rate: item.interest_rate,
        start_date: item.start_date,
        maturity_date: item.maturity_date,
        maturity_amount: item.maturity_amount || '',
        frequency: item.frequency || 'quarterly',
      });
    } else {
      setEditingItem(null);
      setFdForm({
        bank_name: '',
        account_number: '',
        principal: '',
        interest_rate: '',
        start_date: new Date().toISOString().split('T')[0],
        maturity_date: '',
        maturity_amount: '',
        frequency: 'quarterly',
      });
    }
    setOpenFdDialog(true);
  };

  const handleSaveFd = async () => {
    try {
      if (editingItem) {
        await fixedDepositsAPI.update(editingItem.id, fdForm);
      } else {
        await fixedDepositsAPI.create(fdForm);
      }
      setOpenFdDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save FD');
    }
  };

  const handleDeleteFd = async (id) => {
    if (window.confirm('Are you sure you want to delete this FD?')) {
      try {
        await fixedDepositsAPI.delete(id);
        fetchData();
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to delete FD');
      }
    }
  };

  // EPF Account handlers
  const handleOpenEpfAccountDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setEpfAccountForm({
        account_number: item.account_number,
        employer_name: item.employer_name,
        uan: item.uan || '',
      });
    } else {
      setEditingItem(null);
      setEpfAccountForm({
        account_number: '',
        employer_name: '',
        uan: '',
      });
    }
    setOpenEpfAccountDialog(true);
  };

  const handleSaveEpfAccount = async () => {
    try {
      if (editingItem) {
        await epfAPI.updateAccount(editingItem.id, epfAccountForm);
      } else {
        await epfAPI.createAccount(epfAccountForm);
      }
      setOpenEpfAccountDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save EPF account');
    }
  };

  // EPF Contribution handlers
  const handleOpenEpfContributionDialog = () => {
    setEpfContributionForm({
      account_id: epfAccounts[0]?.id || '',
      month: new Date().toISOString().slice(0, 7),
      employee_contribution: '',
      employer_contribution: '',
      interest_earned: '',
    });
    setOpenEpfContributionDialog(true);
  };

  const handleSaveEpfContribution = async () => {
    try {
      await epfAPI.addContribution(epfContributionForm);
      setOpenEpfContributionDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save EPF contribution');
    }
  };

  // NPS Account handlers
  const handleOpenNpsAccountDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setNpsAccountForm({
        pran: item.pran,
        account_type: item.account_type,
        sector: item.sector || 'private',
      });
    } else {
      setEditingItem(null);
      setNpsAccountForm({
        pran: '',
        account_type: 'Tier 1',
        sector: 'private',
      });
    }
    setOpenNpsAccountDialog(true);
  };

  const handleSaveNpsAccount = async () => {
    try {
      await npsAPI.createAccount(npsAccountForm);
      setOpenNpsAccountDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save NPS account');
    }
  };

  // NPS Contribution handlers
  const handleOpenNpsContributionDialog = () => {
    setNpsContributionForm({
      account_id: npsAccounts[0]?.id || '',
      date: new Date().toISOString().split('T')[0],
      amount: '',
      nav: '',
      units: '',
    });
    setOpenNpsContributionDialog(true);
  };

  const handleSaveNpsContribution = async () => {
    try {
      await npsAPI.addContribution(npsContributionForm);
      setOpenNpsContributionDialog(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save NPS contribution');
    }
  };

  // Calculate maturity amount based on principal, rate, and tenure
  const calculateMaturityAmount = () => {
    const { principal, interest_rate, start_date, maturity_date, frequency } = fdForm;
    if (principal && interest_rate && start_date && maturity_date) {
      const p = parseFloat(principal);
      const r = parseFloat(interest_rate) / 100;
      const startDate = new Date(start_date);
      const endDate = new Date(maturity_date);
      const years = (endDate - startDate) / (1000 * 60 * 60 * 24 * 365);
      
      // Compound interest calculation
      const n = frequency === 'monthly' ? 12 : frequency === 'quarterly' ? 4 : 2; // Default semi-annual
      const maturity = p * Math.pow((1 + r / n), n * years);
      
      setFdForm({ ...fdForm, maturity_amount: maturity.toFixed(2) });
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Render FD Tab
  const renderFdTab = () => {
    const totalPrincipal = fdList.reduce((sum, fd) => sum + (parseFloat(fd.principal) || 0), 0);
    const totalMaturity = fdList.reduce((sum, fd) => sum + (parseFloat(fd.maturity_amount) || 0), 0);
    const totalGain = totalMaturity - totalPrincipal;

    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <AccountBalanceIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Total FDs
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  {fdList.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Principal
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  ₹{totalPrincipal.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Maturity Value
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  ₹{totalMaturity.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Interest
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="primary.main">
                  ₹{totalGain.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Upcoming Maturity Alert */}
        {upcomingMaturity.length > 0 && (
          <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 3 }}>
            <Typography variant="body2" fontWeight="bold">
              {upcomingMaturity.length} FD(s) maturing in next 90 days
            </Typography>
            {upcomingMaturity.map(fd => (
              <Typography key={fd.id} variant="caption" display="block">
                {fd.bank_name} - ₹{parseFloat(fd.principal).toLocaleString('en-IN')} 
                (Matures: {new Date(fd.maturity_date).toLocaleDateString()})
              </Typography>
            ))}
          </Alert>
        )}

        {/* FD Table */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Fixed Deposits</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenFdDialog()}
              >
                Add FD
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Bank</TableCell>
                    <TableCell>Account No.</TableCell>
                    <TableCell align="right">Principal</TableCell>
                    <TableCell align="right">Rate</TableCell>
                    <TableCell>Start Date</TableCell>
                    <TableCell>Maturity Date</TableCell>
                    <TableCell align="right">Maturity Amount</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {fdList.map((fd) => {
                    const daysToMaturity = Math.ceil((new Date(fd.maturity_date) - new Date()) / (1000 * 60 * 60 * 24));
                    const isMatured = daysToMaturity < 0;
                    const isNearMaturity = daysToMaturity > 0 && daysToMaturity <= 90;

                    return (
                      <TableRow key={fd.id}>
                        <TableCell>{fd.bank_name}</TableCell>
                        <TableCell>{fd.account_number || '-'}</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold">
                            ₹{parseFloat(fd.principal).toLocaleString('en-IN')}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">{fd.interest_rate}%</TableCell>
                        <TableCell>{new Date(fd.start_date).toLocaleDateString()}</TableCell>
                        <TableCell>{new Date(fd.maturity_date).toLocaleDateString()}</TableCell>
                        <TableCell align="right">
                          <Typography color="success.main" fontWeight="bold">
                            ₹{parseFloat(fd.maturity_amount).toLocaleString('en-IN')}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {isMatured ? (
                            <Chip label="Matured" color="error" size="small" />
                          ) : isNearMaturity ? (
                            <Chip label={`${daysToMaturity}d`} color="warning" size="small" />
                          ) : (
                            <Chip label="Active" color="success" size="small" />
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => handleOpenFdDialog(fd)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteFd(fd.id)}
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

            {fdList.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No fixed deposits yet. Click "Add FD" to get started.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };

  // Render EPF Tab
  const renderEpfTab = () => {
    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <SavingsIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Total Balance
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  ₹{epfSummary?.total_balance?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Employee Contribution
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  ₹{epfSummary?.total_employee?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Employer Contribution
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  ₹{epfSummary?.total_employer?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Interest Earned
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  ₹{epfSummary?.total_interest?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* EPF Accounts */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">EPF Accounts</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenEpfAccountDialog()}
              >
                Add Account
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Account Number</TableCell>
                    <TableCell>Employer</TableCell>
                    <TableCell>UAN</TableCell>
                    <TableCell align="right">Balance</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {epfAccounts.map((account) => (
                    <TableRow key={account.id}>
                      <TableCell>{account.account_number}</TableCell>
                      <TableCell>{account.employer_name}</TableCell>
                      <TableCell>{account.uan || '-'}</TableCell>
                      <TableCell align="right">
                        <Typography fontWeight="bold">
                          ₹{account.balance?.toLocaleString('en-IN') || '0'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenEpfAccountDialog(account)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {epfAccounts.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No EPF accounts yet. Click "Add Account" to get started.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* EPF Contributions */}
        {epfAccounts.length > 0 && (
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Monthly Contributions</Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={handleOpenEpfContributionDialog}
                >
                  Add Contribution
                </Button>
              </Box>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Month</TableCell>
                      <TableCell>Account</TableCell>
                      <TableCell align="right">Employee</TableCell>
                      <TableCell align="right">Employer</TableCell>
                      <TableCell align="right">Interest</TableCell>
                      <TableCell align="right">Total</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {epfContributions.map((contribution) => {
                      const account = epfAccounts.find(a => a.id === contribution.account_id);
                      const total = (contribution.employee_contribution || 0) + 
                                   (contribution.employer_contribution || 0) + 
                                   (contribution.interest_earned || 0);
                      return (
                        <TableRow key={contribution.id}>
                          <TableCell>{contribution.month}</TableCell>
                          <TableCell>{account?.account_number || '-'}</TableCell>
                          <TableCell align="right">
                            ₹{contribution.employee_contribution?.toLocaleString('en-IN') || '0'}
                          </TableCell>
                          <TableCell align="right">
                            ₹{contribution.employer_contribution?.toLocaleString('en-IN') || '0'}
                          </TableCell>
                          <TableCell align="right">
                            ₹{contribution.interest_earned?.toLocaleString('en-IN') || '0'}
                          </TableCell>
                          <TableCell align="right">
                            <Typography fontWeight="bold">
                              ₹{total.toLocaleString('en-IN')}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>

              {epfContributions.length === 0 && (
                <Box textAlign="center" py={4}>
                  <Typography color="text.secondary">
                    No contributions yet. Click "Add Contribution" to get started.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        )}
      </Box>
    );
  };

  // Render NPS Tab
  const renderNpsTab = () => {
    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <TrendingUpIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Total NPS Value
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  ₹{npsSummary?.total_value?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Invested
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  ₹{npsSummary?.total_invested?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Units
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {npsSummary?.total_units?.toFixed(3) || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* NPS Accounts */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">NPS Accounts</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenNpsAccountDialog()}
              >
                Add Account
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>PRAN</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Sector</TableCell>
                    <TableCell align="right">Balance</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {npsAccounts.map((account) => (
                    <TableRow key={account.id}>
                      <TableCell>{account.pran}</TableCell>
                      <TableCell>
                        <Chip
                          label={account.account_type}
                          size="small"
                          color={account.account_type === 'Tier 1' ? 'primary' : 'secondary'}
                        />
                      </TableCell>
                      <TableCell>{account.sector}</TableCell>
                      <TableCell align="right">
                        <Typography fontWeight="bold">
                          ₹{account.balance?.toLocaleString('en-IN') || '0'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {npsAccounts.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="text.secondary">
                  No NPS accounts yet. Click "Add Account" to get started.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* NPS Contributions */}
        {npsAccounts.length > 0 && (
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Contributions</Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={handleOpenNpsContributionDialog}
                >
                  Add Contribution
                </Button>
              </Box>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>PRAN</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell align="right">NAV</TableCell>
                      <TableCell align="right">Units</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {npsContributions.map((contribution) => {
                      const account = npsAccounts.find(a => a.id === contribution.account_id);
                      return (
                        <TableRow key={contribution.id}>
                          <TableCell>{new Date(contribution.date).toLocaleDateString()}</TableCell>
                          <TableCell>{account?.pran || '-'}</TableCell>
                          <TableCell align="right">
                            <Typography fontWeight="bold">
                              ₹{contribution.amount?.toLocaleString('en-IN') || '0'}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">₹{contribution.nav || '-'}</TableCell>
                          <TableCell align="right">{contribution.units?.toFixed(3) || '0'}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>

              {npsContributions.length === 0 && (
                <Box textAlign="center" py={4}>
                  <Typography color="text.secondary">
                    No contributions yet. Click "Add Contribution" to get started.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        )}
      </Box>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 'bold' }}>
        Fixed Income
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, val) => setCurrentTab(val)}>
          <Tab label="Fixed Deposits" />
          <Tab label="EPF" />
          <Tab label="NPS" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {currentTab === 0 && renderFdTab()}
      {currentTab === 1 && renderEpfTab()}
      {currentTab === 2 && renderNpsTab()}

      {/* FD Dialog */}
      <Dialog open={openFdDialog} onClose={() => setOpenFdDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingItem ? 'Edit Fixed Deposit' : 'Add Fixed Deposit'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Bank Name"
                value={fdForm.bank_name}
                onChange={(e) => setFdForm({ ...fdForm, bank_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Account Number (Optional)"
                value={fdForm.account_number}
                onChange={(e) => setFdForm({ ...fdForm, account_number: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Principal Amount"
                type="number"
                value={fdForm.principal}
                onChange={(e) => setFdForm({ ...fdForm, principal: e.target.value })}
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Interest Rate"
                type="number"
                value={fdForm.interest_rate}
                onChange={(e) => setFdForm({ ...fdForm, interest_rate: e.target.value })}
                required
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
                value={fdForm.start_date}
                onChange={(e) => setFdForm({ ...fdForm, start_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Maturity Date"
                type="date"
                value={fdForm.maturity_date}
                onChange={(e) => setFdForm({ ...fdForm, maturity_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Interest Frequency"
                value={fdForm.frequency}
                onChange={(e) => setFdForm({ ...fdForm, frequency: e.target.value })}
                select
              >
                <MenuItem value="monthly">Monthly</MenuItem>
                <MenuItem value="quarterly">Quarterly</MenuItem>
                <MenuItem value="semi-annual">Semi-Annual</MenuItem>
                <MenuItem value="annual">Annual</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Maturity Amount"
                type="number"
                value={fdForm.maturity_amount}
                onChange={(e) => setFdForm({ ...fdForm, maturity_amount: e.target.value })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
                helperText="Auto-calculated if empty"
              />
            </Grid>
            <Grid item xs={12}>
              <Button onClick={calculateMaturityAmount} variant="outlined" fullWidth>
                Calculate Maturity Amount
              </Button>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenFdDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveFd} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* EPF Account Dialog */}
      <Dialog open={openEpfAccountDialog} onClose={() => setOpenEpfAccountDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingItem ? 'Edit EPF Account' : 'Add EPF Account'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Account Number"
                value={epfAccountForm.account_number}
                onChange={(e) => setEpfAccountForm({ ...epfAccountForm, account_number: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Employer Name"
                value={epfAccountForm.employer_name}
                onChange={(e) => setEpfAccountForm({ ...epfAccountForm, employer_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="UAN (Optional)"
                value={epfAccountForm.uan}
                onChange={(e) => setEpfAccountForm({ ...epfAccountForm, uan: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEpfAccountDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveEpfAccount} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* EPF Contribution Dialog */}
      <Dialog open={openEpfContributionDialog} onClose={() => setOpenEpfContributionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add EPF Contribution</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Account"
                value={epfContributionForm.account_id}
                onChange={(e) => setEpfContributionForm({ ...epfContributionForm, account_id: e.target.value })}
                select
                required
              >
                {epfAccounts.map((account) => (
                  <MenuItem key={account.id} value={account.id}>
                    {account.account_number} - {account.employer_name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Month"
                type="month"
                value={epfContributionForm.month}
                onChange={(e) => setEpfContributionForm({ ...epfContributionForm, month: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Employee Contribution"
                type="number"
                value={epfContributionForm.employee_contribution}
                onChange={(e) => setEpfContributionForm({ ...epfContributionForm, employee_contribution: e.target.value })}
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Employer Contribution"
                type="number"
                value={epfContributionForm.employer_contribution}
                onChange={(e) => setEpfContributionForm({ ...epfContributionForm, employer_contribution: e.target.value })}
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Interest Earned (Optional)"
                type="number"
                value={epfContributionForm.interest_earned}
                onChange={(e) => setEpfContributionForm({ ...epfContributionForm, interest_earned: e.target.value })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEpfContributionDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveEpfContribution} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* NPS Account Dialog */}
      <Dialog open={openNpsAccountDialog} onClose={() => setOpenNpsAccountDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add NPS Account</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="PRAN"
                value={npsAccountForm.pran}
                onChange={(e) => setNpsAccountForm({ ...npsAccountForm, pran: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Account Type"
                value={npsAccountForm.account_type}
                onChange={(e) => setNpsAccountForm({ ...npsAccountForm, account_type: e.target.value })}
                select
                required
              >
                <MenuItem value="Tier 1">Tier 1</MenuItem>
                <MenuItem value="Tier 2">Tier 2</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Sector"
                value={npsAccountForm.sector}
                onChange={(e) => setNpsAccountForm({ ...npsAccountForm, sector: e.target.value })}
                select
              >
                <MenuItem value="government">Government</MenuItem>
                <MenuItem value="private">Private</MenuItem>
                <MenuItem value="unorganized">Unorganized</MenuItem>
              </TextField>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenNpsAccountDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveNpsAccount} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* NPS Contribution Dialog */}
      <Dialog open={openNpsContributionDialog} onClose={() => setOpenNpsContributionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add NPS Contribution</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Account"
                value={npsContributionForm.account_id}
                onChange={(e) => setNpsContributionForm({ ...npsContributionForm, account_id: e.target.value })}
                select
                required
              >
                {npsAccounts.map((account) => (
                  <MenuItem key={account.id} value={account.id}>
                    {account.pran} - {account.account_type}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Date"
                type="date"
                value={npsContributionForm.date}
                onChange={(e) => setNpsContributionForm({ ...npsContributionForm, date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={npsContributionForm.amount}
                onChange={(e) => setNpsContributionForm({ ...npsContributionForm, amount: e.target.value })}
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="NAV (Optional)"
                type="number"
                value={npsContributionForm.nav}
                onChange={(e) => setNpsContributionForm({ ...npsContributionForm, nav: e.target.value })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Units (Optional)"
                type="number"
                value={npsContributionForm.units}
                onChange={(e) => setNpsContributionForm({ ...npsContributionForm, units: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenNpsContributionDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveNpsContribution} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default FixedIncome;

