import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import SavingsIcon from '@mui/icons-material/Savings';
import { dashboardAPI } from '../services/api';

const COLORS = ['#60a5fa', '#a78bfa', '#4ade80', '#fbbf24', '#f87171'];

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [netWorth, setNetWorth] = useState(null);
  const [assetAllocation, setAssetAllocation] = useState(null);
  const [cashFlow, setCashFlow] = useState([]);
  const [summary, setSummary] = useState(null);
  const [unifiedXIRR, setUnifiedXIRR] = useState(null); // Phase 3

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [netWorthRes, allocationRes, cashFlowRes, summaryRes, xirrRes] = await Promise.all([
        dashboardAPI.getNetWorth(),
        dashboardAPI.getAssetAllocation(),
        dashboardAPI.getCashFlow(),
        dashboardAPI.getSummary(),
        dashboardAPI.getUnifiedXIRR(), // Phase 3
      ]);

      setNetWorth(netWorthRes.data);
      setAssetAllocation(allocationRes.data);
      setCashFlow(cashFlowRes.data);
      setSummary(summaryRes.data);
      setUnifiedXIRR(xirrRes.data); // Phase 3
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load dashboard data');
      console.error('Dashboard error:', err);
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

  // Prepare pie chart data for asset allocation
  const allocationData = assetAllocation ? [
    { name: 'Equity', value: assetAllocation.equity },
    { name: 'Debt', value: assetAllocation.debt },
    { name: 'Cash', value: assetAllocation.cash },
    { name: 'Alternative', value: assetAllocation.alternative },
  ].filter(item => item.value > 0) : [];

  // Prepare bar chart data for cash flow (last 6 months)
  const cashFlowData = cashFlow.slice(-6).map(item => ({
    month: item.month,
    income: item.income,
    expense: item.expense,
    savings: item.net,
  }));

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 'bold' }}>
        Financial Dashboard
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <AccountBalanceWalletIcon sx={{ mr: 1, color: 'white' }} />
                <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                  Total Net Worth
                </Typography>
              </Box>
              <Typography variant="h4" color="white" fontWeight="bold">
                ₹{netWorth?.total?.toLocaleString('en-IN') || '0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <ShowChartIcon sx={{ mr: 1, color: 'white' }} />
                <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                  Total Holdings
                </Typography>
              </Box>
              <Typography variant="h4" color="white" fontWeight="bold">
                {summary?.total_holdings || 0}
              </Typography>
              <Typography variant="caption" color="white" sx={{ opacity: 0.8 }}>
                {summary?.stock_holdings || 0} Stocks · {summary?.mf_holdings || 0} MFs
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <TrendingUpIcon sx={{ mr: 1, color: 'white' }} />
                <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                  Stocks Value
                </Typography>
              </Box>
              <Typography variant="h4" color="white" fontWeight="bold">
                ₹{netWorth?.stocks?.toLocaleString('en-IN') || '0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <SavingsIcon sx={{ mr: 1, color: 'white' }} />
                <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                  Savings & Cash
                </Typography>
              </Box>
              <Typography variant="h4" color="white" fontWeight="bold">
                ₹{netWorth?.savings?.toLocaleString('en-IN') || '0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Phase 3: Unified XIRR Card */}
      {unifiedXIRR && unifiedXIRR.overall_xirr && (
        <Card sx={{ mb: 4, background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }}>
          <CardContent>
            <Typography variant="h6" color="white" gutterBottom fontWeight="bold" sx={{ mb: 2 }}>
              📊 Portfolio XIRR (Unified Across All Assets)
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="caption" color="white" sx={{ opacity: 0.9 }}>
                    Overall XIRR
                  </Typography>
                  <Typography variant="h3" color="white" fontWeight="bold">
                    {unifiedXIRR.overall_xirr > 0 ? '+' : ''}{unifiedXIRR.overall_xirr}%
                  </Typography>
                  <Typography variant="caption" color="white" sx={{ opacity: 0.8 }}>
                    Portfolio Return Rate
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={9}>
                <Grid container spacing={2}>
                  {unifiedXIRR.xirr_by_type.stocks && (
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ bgcolor: 'rgba(255,255,255,0.2)', borderRadius: 2, p: 1.5, textAlign: 'center' }}>
                        <Typography variant="caption" color="white">Stocks</Typography>
                        <Typography variant="h6" color="white" fontWeight="bold">
                          {unifiedXIRR.xirr_by_type.stocks > 0 ? '+' : ''}{unifiedXIRR.xirr_by_type.stocks}%
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                  {unifiedXIRR.xirr_by_type.mutual_funds && (
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ bgcolor: 'rgba(255,255,255,0.2)', borderRadius: 2, p: 1.5, textAlign: 'center' }}>
                        <Typography variant="caption" color="white">Mutual Funds</Typography>
                        <Typography variant="h6" color="white" fontWeight="bold">
                          {unifiedXIRR.xirr_by_type.mutual_funds > 0 ? '+' : ''}{unifiedXIRR.xirr_by_type.mutual_funds}%
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                  {unifiedXIRR.xirr_by_type.fixed_deposits && (
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ bgcolor: 'rgba(255,255,255,0.2)', borderRadius: 2, p: 1.5, textAlign: 'center' }}>
                        <Typography variant="caption" color="white">FDs</Typography>
                        <Typography variant="h6" color="white" fontWeight="bold">
                          {unifiedXIRR.xirr_by_type.fixed_deposits > 0 ? '+' : ''}{unifiedXIRR.xirr_by_type.fixed_deposits}%
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                  {unifiedXIRR.xirr_by_type.epf && (
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ bgcolor: 'rgba(255,255,255,0.2)', borderRadius: 2, p: 1.5, textAlign: 'center' }}>
                        <Typography variant="caption" color="white">EPF</Typography>
                        <Typography variant="h6" color="white" fontWeight="bold">
                          {unifiedXIRR.xirr_by_type.epf > 0 ? '+' : ''}{unifiedXIRR.xirr_by_type.epf}%
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                  {unifiedXIRR.xirr_by_type.nps && (
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ bgcolor: 'rgba(255,255,255,0.2)', borderRadius: 2, p: 1.5, textAlign: 'center' }}>
                        <Typography variant="caption" color="white">NPS</Typography>
                        <Typography variant="h6" color="white" fontWeight="bold">
                          {unifiedXIRR.xirr_by_type.nps > 0 ? '+' : ''}{unifiedXIRR.xirr_by_type.nps}%
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                </Grid>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Charts Row */}
      <Grid container spacing={3}>
        {/* Asset Allocation Pie Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Asset Allocation
              </Typography>
              {allocationData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={allocationData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {allocationData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `${value}%`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Box display="flex" justifyContent="center" alignItems="center" height={300}>
                  <Typography color="text.secondary">No asset data available</Typography>
                </Box>
              )}
              {assetAllocation && (
                <Box mt={2}>
                  <Typography variant="caption" color="text.secondary">
                    Total Portfolio Value: ₹{assetAllocation.total_value?.toLocaleString('en-IN')}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Cash Flow Bar Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Income vs Expenses (Last 6 Months)
              </Typography>
              {cashFlowData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={cashFlowData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="month" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #374151' }}
                      formatter={(value) => `₹${value?.toLocaleString('en-IN')}`}
                    />
                    <Legend />
                    <Bar dataKey="income" fill="#4ade80" name="Income" />
                    <Bar dataKey="expense" fill="#f87171" name="Expenses" />
                    <Bar dataKey="savings" fill="#60a5fa" name="Savings" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Box display="flex" justifyContent="center" alignItems="center" height={300}>
                  <Typography color="text.secondary">No cash flow data available</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Net Worth Breakdown */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Net Worth Breakdown
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                {netWorth && Object.entries(netWorth)
                  .filter(([key, value]) => key !== 'total' && value > 0)
                  .map(([key, value]) => (
                    <Grid item xs={6} sm={4} md={3} key={key}>
                      <Box
                        sx={{
                          p: 2,
                          bgcolor: 'background.paper',
                          borderRadius: 2,
                          border: '1px solid',
                          borderColor: 'divider',
                        }}
                      >
                        <Typography variant="caption" color="text.secondary" textTransform="capitalize">
                          {key.replace(/_/g, ' ')}
                        </Typography>
                        <Typography variant="h6" fontWeight="bold">
                          ₹{value.toLocaleString('en-IN')}
                        </Typography>
                      </Box>
                    </Grid>
                  ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;

