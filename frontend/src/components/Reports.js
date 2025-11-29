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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import DownloadIcon from '@mui/icons-material/Download';
import AssessmentIcon from '@mui/icons-material/Assessment';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import ReceiptIcon from '@mui/icons-material/Receipt';
import { dashboardAPI, incomeAPI, expensesAPI } from '../services/api';

const COLORS = ['#60a5fa', '#a78bfa', '#4ade80', '#fbbf24', '#f87171', '#fb923c', '#ec4899', '#8b5cf6'];

function Reports() {
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  // Data state
  const [netWorthTrend, setNetWorthTrend] = useState([]);
  const [allocationTrend, setAllocationTrend] = useState([]);
  const [cashFlowData, setCashFlowData] = useState([]);
  const [taxSummary, setTaxSummary] = useState(null);
  const [yearlyData, setYearlyData] = useState(null);

  useEffect(() => {
    fetchData();
  }, [currentTab, selectedYear]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (currentTab === 0) {
        // Net Worth Trend - fetch historical data
        const netWorthRes = await dashboardAPI.getNetWorth();
        // Mock historical data for demonstration (backend would provide this)
        const mockHistoricalData = generateMockHistoricalData();
        setNetWorthTrend(mockHistoricalData);
      } else if (currentTab === 1) {
        // Asset Allocation Evolution
        const allocationRes = await dashboardAPI.getAssetAllocation();
        const mockAllocationTrend = generateMockAllocationTrend();
        setAllocationTrend(mockAllocationTrend);
      } else if (currentTab === 2) {
        // Cash Flow Analysis
        const cashFlowRes = await dashboardAPI.getCashFlow();
        setCashFlowData(cashFlowRes.data);
      } else if (currentTab === 3) {
        // Tax Summary - calculate from various sources
        const mockTaxData = generateMockTaxData();
        setTaxSummary(mockTaxData);
      } else if (currentTab === 4) {
        // Yearly Summary
        const mockYearlyData = generateMockYearlyData(selectedYear);
        setYearlyData(mockYearlyData);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load data');
      console.error('Data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Mock data generators (replace with actual API calls when backend is ready)
  const generateMockHistoricalData = () => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months.map((month, index) => ({
      month,
      netWorth: 1000000 + (index * 50000) + (Math.random() * 100000),
      invested: 800000 + (index * 40000),
      gains: 200000 + (index * 10000) + (Math.random() * 50000),
    }));
  };

  const generateMockAllocationTrend = () => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months.map((month, index) => ({
      month,
      equity: 500000 + (index * 25000),
      debt: 300000 + (index * 15000),
      cash: 150000 + (index * 7000),
      alternative: 50000 + (index * 3000),
    }));
  };

  const generateMockTaxData = () => {
    return {
      stocks: {
        stcg: 25000,
        ltcg: 75000,
        dividends: 12000,
      },
      mutualFunds: {
        stcg: 15000,
        ltcg: 45000,
        dividends: 8000,
      },
      fixedIncome: {
        fdInterest: 35000,
        epfInterest: 18000,
      },
      other: {
        rentalIncome: 120000,
        businessIncome: 250000,
      },
      totalTaxable: 603000,
      estimatedTax: 120600, // Assuming 20% average tax rate
    };
  };

  const generateMockYearlyData = (year) => {
    return {
      year,
      income: {
        salary: 1200000,
        investment: 150000,
        freelance: 80000,
        other: 45000,
        total: 1475000,
      },
      expenses: {
        essential: 480000,
        lifestyle: 240000,
        investments: 400000,
        total: 1120000,
      },
      savings: 355000,
      savingsRate: 24.07,
      netWorthStart: 2500000,
      netWorthEnd: 2855000,
      growth: 355000,
      growthPercent: 14.2,
    };
  };

  const handleExportPDF = () => {
    alert('PDF export functionality will be implemented with a PDF library like jsPDF or html2pdf');
  };

  const handleExportExcel = () => {
    alert('Excel export functionality will be implemented with a library like xlsx or exceljs');
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Render Net Worth Trend Tab
  const renderNetWorthTrend = () => {
    const latestData = netWorthTrend[netWorthTrend.length - 1] || {};
    const firstData = netWorthTrend[0] || {};
    const growth = latestData.netWorth - firstData.netWorth;
    const growthPercent = firstData.netWorth > 0 
      ? ((growth / firstData.netWorth) * 100).toFixed(2)
      : 0;

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
                    Current Net Worth
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  ₹{latestData.netWorth?.toLocaleString('en-IN') || '0'}
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
                  ₹{latestData.invested?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Gains
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  ₹{latestData.gains?.toLocaleString('en-IN') || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  YTD Growth
                </Typography>
                <Typography 
                  variant="h5" 
                  fontWeight="bold"
                  color={growth >= 0 ? 'success.main' : 'error.main'}
                >
                  {growth >= 0 ? '+' : ''}{growthPercent}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Net Worth Trend Chart */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Net Worth Trend (Last 12 Months)
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={netWorthTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="netWorth" 
                  stroke="#60a5fa" 
                  strokeWidth={3}
                  name="Net Worth"
                  dot={{ r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="invested" 
                  stroke="#a78bfa" 
                  strokeWidth={2}
                  name="Total Invested"
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Box>
    );
  };

  // Render Asset Allocation Evolution Tab
  const renderAllocationEvolution = () => {
    return (
      <Box>
        {/* Allocation Evolution Chart */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Asset Allocation Evolution (Last 12 Months)
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={allocationTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="equity" 
                  stackId="1"
                  stroke="#60a5fa" 
                  fill="#60a5fa"
                  name="Equity"
                />
                <Area 
                  type="monotone" 
                  dataKey="debt" 
                  stackId="1"
                  stroke="#4ade80" 
                  fill="#4ade80"
                  name="Debt"
                />
                <Area 
                  type="monotone" 
                  dataKey="cash" 
                  stackId="1"
                  stroke="#fbbf24" 
                  fill="#fbbf24"
                  name="Cash"
                />
                <Area 
                  type="monotone" 
                  dataKey="alternative" 
                  stackId="1"
                  stroke="#a78bfa" 
                  fill="#a78bfa"
                  name="Alternative"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Allocation Breakdown Table */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current Allocation Breakdown
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Asset Class</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell align="right">Percentage</TableCell>
                    <TableCell align="right">YTD Change</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {allocationTrend.length > 0 && (() => {
                    const latest = allocationTrend[allocationTrend.length - 1];
                    const first = allocationTrend[0];
                    const total = latest.equity + latest.debt + latest.cash + latest.alternative;
                    
                    return [
                      { name: 'Equity', current: latest.equity, start: first.equity },
                      { name: 'Debt', current: latest.debt, start: first.debt },
                      { name: 'Cash', current: latest.cash, start: first.cash },
                      { name: 'Alternative', current: latest.alternative, start: first.alternative },
                    ].map((item) => {
                      const change = ((item.current - item.start) / item.start * 100).toFixed(2);
                      return (
                        <TableRow key={item.name}>
                          <TableCell>{item.name}</TableCell>
                          <TableCell align="right">
                            <Typography fontWeight="bold">
                              ₹{item.current.toLocaleString('en-IN')}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            {((item.current / total) * 100).toFixed(1)}%
                          </TableCell>
                          <TableCell align="right">
                            <Typography color={change >= 0 ? 'success.main' : 'error.main'}>
                              {change >= 0 ? '+' : ''}{change}%
                            </Typography>
                          </TableCell>
                        </TableRow>
                      );
                    });
                  })()}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Box>
    );
  };

  // Render Cash Flow Tab
  const renderCashFlow = () => {
    const totalIncome = cashFlowData.reduce((sum, item) => sum + (item.income || 0), 0);
    const totalExpense = cashFlowData.reduce((sum, item) => sum + (item.expense || 0), 0);
    const netSavings = totalIncome - totalExpense;
    const savingsRate = totalIncome > 0 ? ((netSavings / totalIncome) * 100).toFixed(2) : 0;

    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Income
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  ₹{totalIncome.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Expenses
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="error.main">
                  ₹{totalExpense.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Net Savings
                </Typography>
                <Typography 
                  variant="h5" 
                  fontWeight="bold"
                  color={netSavings >= 0 ? 'success.main' : 'error.main'}
                >
                  ₹{netSavings.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Savings Rate
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="primary.main">
                  {savingsRate}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Cash Flow Chart */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Income vs Expenses Trend
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={cashFlowData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                <Legend />
                <Bar dataKey="income" fill="#4ade80" name="Income" />
                <Bar dataKey="expense" fill="#f87171" name="Expense" />
                <Bar dataKey="net" fill="#60a5fa" name="Net Savings" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Box>
    );
  };

  // Render Tax Summary Tab
  const renderTaxSummary = () => {
    if (!taxSummary) return null;

    return (
      <Box>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={6}>
            <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <ReceiptIcon sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    Total Taxable Income
                  </Typography>
                </Box>
                <Typography variant="h4" color="white" fontWeight="bold">
                  ₹{taxSummary.totalTaxable.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={6}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Estimated Tax Liability
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="error.main">
                  ₹{taxSummary.estimatedTax.toLocaleString('en-IN')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  (Approximate - consult tax advisor)
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Tax Breakdown - Stocks */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Stock Investment Tax
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell>Tax Rate</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Short Term Capital Gains (STCG)</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{taxSummary.stocks.stcg.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label="15%" size="small" color="warning" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Long Term Capital Gains (LTCG)</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{taxSummary.stocks.ltcg.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label="10% (above ₹1L)" size="small" color="success" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Dividends</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{taxSummary.stocks.dividends.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label="As per slab" size="small" color="primary" />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* Tax Breakdown - Mutual Funds */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Mutual Funds Tax
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell>Tax Rate</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Short Term Capital Gains (STCG)</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{taxSummary.mutualFunds.stcg.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label="15%" size="small" color="warning" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Long Term Capital Gains (LTCG)</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{taxSummary.mutualFunds.ltcg.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label="10% (above ₹1L)" size="small" color="success" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Dividends</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{taxSummary.mutualFunds.dividends.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label="As per slab" size="small" color="primary" />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* Tax Breakdown - Fixed Income & Other */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Other Taxable Income
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell>Tax Rate</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Fixed Deposit Interest</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{taxSummary.fixedIncome.fdInterest.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label="As per slab" size="small" color="primary" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>EPF Interest (if taxable)</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{taxSummary.fixedIncome.epfInterest.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label="As per slab" size="small" color="primary" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Rental Income</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{taxSummary.other.rentalIncome.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label="As per slab" size="small" color="primary" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Business Income</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{taxSummary.other.businessIncome.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label="As per slab" size="small" color="primary" />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            <strong>Note:</strong> This is an estimated tax summary based on your transactions. 
            Please consult with a qualified tax advisor or Chartered Accountant for accurate tax planning and filing.
            Tax rates and rules may vary based on your specific situation and current tax laws.
          </Typography>
        </Alert>
      </Box>
    );
  };

  // Render Yearly Summary Tab
  const renderYearlySummary = () => {
    if (!yearlyData) return null;

    return (
      <Box>
        {/* Year Selector */}
        <Box sx={{ mb: 4 }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Select Year</InputLabel>
            <Select
              value={selectedYear}
              label="Select Year"
              onChange={(e) => setSelectedYear(e.target.value)}
            >
              <MenuItem value={2025}>2025</MenuItem>
              <MenuItem value={2024}>2024</MenuItem>
              <MenuItem value={2023}>2023</MenuItem>
              <MenuItem value={2022}>2022</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Income
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  ₹{yearlyData.income.total.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Expenses
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="error.main">
                  ₹{yearlyData.expenses.total.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Savings
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="primary.main">
                  ₹{yearlyData.savings.toLocaleString('en-IN')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Savings Rate
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="primary.main">
                  {yearlyData.savingsRate}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Income Breakdown */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Income Breakdown - {selectedYear}
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell align="right">Percentage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Salary</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{yearlyData.income.salary.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {((yearlyData.income.salary / yearlyData.income.total) * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Investment Income</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{yearlyData.income.investment.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {((yearlyData.income.investment / yearlyData.income.total) * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Freelance</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{yearlyData.income.freelance.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {((yearlyData.income.freelance / yearlyData.income.total) * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Other</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{yearlyData.income.other.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {((yearlyData.income.other / yearlyData.income.total) * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* Expense Breakdown */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Expense Breakdown - {selectedYear}
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell align="right">Percentage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Essential (Rent, Food, Bills)</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{yearlyData.expenses.essential.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {((yearlyData.expenses.essential / yearlyData.expenses.total) * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Lifestyle (Entertainment, Travel)</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{yearlyData.expenses.lifestyle.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {((yearlyData.expenses.lifestyle / yearlyData.expenses.total) * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Investments</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        ₹{yearlyData.expenses.investments.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {((yearlyData.expenses.investments / yearlyData.expenses.total) * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* Net Worth Growth */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Net Worth Growth - {selectedYear}
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Start of Year
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  ₹{yearlyData.netWorthStart.toLocaleString('en-IN')}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  End of Year
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="primary.main">
                  ₹{yearlyData.netWorthEnd.toLocaleString('en-IN')}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Absolute Growth
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  +₹{yearlyData.growth.toLocaleString('en-IN')}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Growth %
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  +{yearlyData.growthPercent}%
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Box>
    );
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Reports & Analytics
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExportPDF}
            sx={{ mr: 2 }}
          >
            Export PDF
          </Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={handleExportExcel}
          >
            Export Excel
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs 
          value={currentTab} 
          onChange={(e, val) => setCurrentTab(val)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Net Worth Trend" />
          <Tab label="Allocation Evolution" />
          <Tab label="Cash Flow" />
          <Tab label="Tax Summary" />
          <Tab label="Yearly Summary" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {currentTab === 0 && renderNetWorthTrend()}
      {currentTab === 1 && renderAllocationEvolution()}
      {currentTab === 2 && renderCashFlow()}
      {currentTab === 3 && renderTaxSummary()}
      {currentTab === 4 && renderYearlySummary()}
    </Box>
  );
}

export default Reports;

