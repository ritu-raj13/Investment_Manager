import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  LinearProgress,
  Chip,
  Divider,
} from '@mui/material';
import {
  Circle as CircleIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { healthAPI } from '../services/api';

const Health = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [financialHealth, setFinancialHealth] = useState(null); // Phase 3

  useEffect(() => {
    fetchHealthData();
    fetchFinancialHealth(); // Phase 3
  }, []);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const response = await healthAPI.getDashboard();
      setData(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load health data');
      console.error('Health error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchFinancialHealth = async () => {
    try {
      // Fetch financial health metrics (Phase 3)
      const response = await healthAPI.getFinancialHealth();
      setFinancialHealth(response.data);
    } catch (err) {
      console.error('Financial health error:', err);
    }
  };

  const formatCurrency = (value) => {
    return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const getHealthColor = (score) => {
    if (score >= 75) return '#22c55e'; // Green
    if (score >= 50) return '#eab308'; // Yellow
    return '#ef4444'; // Red
  };

  const getHealthLabel = (score) => {
    if (score >= 75) return 'Excellent';
    if (score >= 50) return 'Good';
    return 'Needs Attention';
  };

  const getHealthIcon = (score) => {
    if (score >= 75) return <CheckCircleIcon sx={{ color: '#22c55e', fontSize: 40 }} />;
    if (score >= 50) return <TrendingUpIcon sx={{ color: '#eab308', fontSize: 40 }} />;
    return <WarningIcon sx={{ color: '#ef4444', fontSize: 40 }} />;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!data) {
    return null;
  }

  const {
    overall_health_score,
    concentration_risk,
    diversification,
    allocation_health,
    total_invested,
    holdings_count,
  } = data;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Portfolio Health
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Comprehensive analysis of your portfolio's health and risk metrics
        </Typography>
      </Box>

      {/* Overall Health Score Card */}
      <Paper sx={{ p: 4, mb: 3, borderRadius: 3, textAlign: 'center', bgcolor: 'rgba(96, 165, 250, 0.05)' }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 2 }}>
          {getHealthIcon(overall_health_score)}
        </Box>
        <Typography variant="h3" fontWeight="bold" sx={{ color: getHealthColor(overall_health_score), mb: 1 }}>
          {overall_health_score}/100
        </Typography>
        <Typography variant="h6" gutterBottom>
          {getHealthLabel(overall_health_score)}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Overall Portfolio Health Score
        </Typography>
        
        {/* Health Score Bar */}
        <Box sx={{ mt: 3, maxWidth: 600, mx: 'auto' }}>
          <LinearProgress
            variant="determinate"
            value={overall_health_score}
            sx={{
              height: 12,
              borderRadius: 6,
              bgcolor: 'rgba(255, 255, 255, 0.1)',
              '& .MuiLinearProgress-bar': {
                bgcolor: getHealthColor(overall_health_score),
                borderRadius: 6,
              },
            }}
          />
        </Box>

        {/* Quick Stats */}
        <Grid container spacing={2} sx={{ mt: 3, maxWidth: 600, mx: 'auto' }}>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">
              Total Holdings
            </Typography>
            <Typography variant="h6" fontWeight="bold">
              {holdings_count}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">
              Total Invested
            </Typography>
            <Typography variant="h6" fontWeight="bold">
              {formatCurrency(total_invested)}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Detailed Metrics */}
      <Grid container spacing={3}>
        {/* Concentration Risk */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 3, height: '100%' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Concentration Risk
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Measures portfolio concentration in top holdings
            </Typography>

            {/* Stock Concentration */}
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" fontWeight="medium">
                  Top 3 Stocks
                </Typography>
                <Typography variant="body2" fontWeight="bold" color={concentration_risk.stock_concentration > 60 ? 'error' : 'primary'}>
                  {concentration_risk.stock_concentration}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min(concentration_risk.stock_concentration, 100)}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: concentration_risk.stock_concentration > 60 ? '#ef4444' : '#60a5fa',
                    borderRadius: 4,
                  },
                }}
              />
              {concentration_risk.top_3_stocks && concentration_risk.top_3_stocks.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  {concentration_risk.top_3_stocks.map((stock, idx) => (
                    <Box key={idx} sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {stock.symbol}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {stock.percentage.toFixed(1)}%
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>

            <Divider sx={{ my: 2 }} />

            {/* Sector Concentration */}
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" fontWeight="medium">
                  Top Sector
                </Typography>
                <Typography variant="body2" fontWeight="bold" color={concentration_risk.sector_concentration > 50 ? 'error' : 'primary'}>
                  {concentration_risk.sector_concentration}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min(concentration_risk.sector_concentration, 100)}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: concentration_risk.sector_concentration > 50 ? '#ef4444' : '#4ade80',
                    borderRadius: 4,
                  },
                }}
              />
              {concentration_risk.top_sector && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {concentration_risk.top_sector.name}: {formatCurrency(concentration_risk.top_sector.invested_amount)}
                </Typography>
              )}
            </Box>

            <Divider sx={{ my: 2 }} />

            {/* Market Cap Concentration */}
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" fontWeight="medium">
                  Top Market Cap
                </Typography>
                <Typography variant="body2" fontWeight="bold" color={concentration_risk.market_cap_concentration > 70 ? 'error' : 'primary'}>
                  {concentration_risk.market_cap_concentration}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min(concentration_risk.market_cap_concentration, 100)}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: concentration_risk.market_cap_concentration > 70 ? '#ef4444' : '#fbbf24',
                    borderRadius: 4,
                  },
                }}
              />
              {concentration_risk.top_market_cap && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {concentration_risk.top_market_cap.name}: {formatCurrency(concentration_risk.top_market_cap.invested_amount)}
                </Typography>
              )}
            </Box>

            {/* Risk Assessment */}
            <Box sx={{ mt: 3, p: 2, bgcolor: 'rgba(96, 165, 250, 0.1)', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                Risk Assessment:
              </Typography>
              {concentration_risk.stock_concentration > 60 ? (
                <Typography variant="body2" color="error">
                  ⚠️ High concentration in top stocks - consider diversifying
                </Typography>
              ) : concentration_risk.stock_concentration > 40 ? (
                <Typography variant="body2" color="warning.main">
                  ⚡ Moderate concentration - monitor closely
                </Typography>
              ) : (
                <Typography variant="body2" color="success.main">
                  ✓ Well diversified across stocks
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Diversification Metrics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 3, height: '100%' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Diversification Metrics
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Measures portfolio spread across stocks, sectors, and market caps
            </Typography>

            {/* Diversification Score */}
            <Box sx={{ textAlign: 'center', mb: 3, p: 3, bgcolor: 'rgba(74, 222, 128, 0.1)', borderRadius: 2 }}>
              <Typography variant="h2" fontWeight="bold" color="success.main">
                {diversification.diversification_score}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Diversification Score (0-100)
              </Typography>
            </Box>

            {/* Metrics Grid */}
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Card sx={{ textAlign: 'center', bgcolor: 'rgba(96, 165, 250, 0.1)' }}>
                  <CardContent>
                    <Typography variant="h4" fontWeight="bold" color="primary">
                      {diversification.num_stocks}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Stocks
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={4}>
                <Card sx={{ textAlign: 'center', bgcolor: 'rgba(251, 191, 36, 0.1)' }}>
                  <CardContent>
                    <Typography variant="h4" fontWeight="bold" color="warning.main">
                      {diversification.num_sectors}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Sectors
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={4}>
                <Card sx={{ textAlign: 'center', bgcolor: 'rgba(248, 113, 113, 0.1)' }}>
                  <CardContent>
                    <Typography variant="h4" fontWeight="bold" color="error.main">
                      {diversification.num_market_caps}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Market Caps
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Herfindahl Index */}
            <Box sx={{ mt: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" fontWeight="medium">
                  Herfindahl Index
                </Typography>
                <Chip
                  label={diversification.herfindahl_index}
                  size="small"
                  color={diversification.herfindahl_index < 0.15 ? 'success' : diversification.herfindahl_index < 0.25 ? 'warning' : 'error'}
                />
              </Box>
              <Typography variant="caption" color="text.secondary">
                Lower is better (0 = perfect diversification, 1 = fully concentrated)
              </Typography>
            </Box>

            {/* Recommendations */}
            <Box sx={{ mt: 3, p: 2, bgcolor: 'rgba(74, 222, 128, 0.1)', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                Recommendations:
              </Typography>
              {diversification.num_stocks < 10 && (
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  📈 Consider adding more stocks (target: 10-15)
                </Typography>
              )}
              {diversification.num_sectors < 5 && (
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  🎯 Diversify across more sectors (target: 5-8)
                </Typography>
              )}
              {diversification.num_market_caps < 3 && (
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  💼 Include different market caps (Large/Mid/Small)
                </Typography>
              )}
              {diversification.num_stocks >= 10 && diversification.num_sectors >= 5 && (
                <Typography variant="body2" color="success.main">
                  ✓ Well diversified portfolio!
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Allocation Health */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Allocation Health
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Stock allocation status based on market cap thresholds
            </Typography>

            <Grid container spacing={3}>
              {/* Over-allocated */}
              <Grid item xs={12} sm={4}>
                <Box sx={{ textAlign: 'center', p: 3, bgcolor: 'rgba(248, 113, 113, 0.1)', borderRadius: 2 }}>
                  <CircleIcon sx={{ color: '#ef4444', fontSize: 48, mb: 1 }} />
                  <Typography variant="h3" fontWeight="bold" color="error">
                    {allocation_health.over_allocated}
                  </Typography>
                  <Typography variant="body1" fontWeight="medium" gutterBottom>
                    Over-Allocated
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Above target allocation
                  </Typography>
                </Box>
              </Grid>

              {/* Balanced */}
              <Grid item xs={12} sm={4}>
                <Box sx={{ textAlign: 'center', p: 3, bgcolor: 'rgba(74, 222, 128, 0.1)', borderRadius: 2 }}>
                  <CircleIcon sx={{ color: '#22c55e', fontSize: 48, mb: 1 }} />
                  <Typography variant="h3" fontWeight="bold" color="success.main">
                    {allocation_health.balanced}
                  </Typography>
                  <Typography variant="body1" fontWeight="medium" gutterBottom>
                    Balanced
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    At target allocation
                  </Typography>
                </Box>
              </Grid>

              {/* Under-allocated */}
              <Grid item xs={12} sm={4}>
                <Box sx={{ textAlign: 'center', p: 3, bgcolor: 'rgba(251, 191, 36, 0.1)', borderRadius: 2 }}>
                  <CircleIcon sx={{ color: '#eab308', fontSize: 48, mb: 1 }} />
                  <Typography variant="h3" fontWeight="bold" color="warning.main">
                    {allocation_health.under_allocated}
                  </Typography>
                  <Typography variant="body1" fontWeight="medium" gutterBottom>
                    Under-Allocated
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Below target allocation
                  </Typography>
                </Box>
              </Grid>
            </Grid>

            {/* Allocation Targets Info */}
            <Box sx={{ mt: 3, p: 2, bgcolor: 'rgba(96, 165, 250, 0.05)', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1, fontWeight: 'bold' }}>
                Target Allocations by Market Cap:
              </Typography>
              <Grid container spacing={1}>
                <Grid item xs={12} sm={3}>
                  <Typography variant="caption">
                    🔵 Large Cap: 5% (green: 5-5.5%)
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Typography variant="caption">
                    🟠 Mid Cap: 3% (green: 3-3.5%)
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Typography variant="caption">
                    🟡 Small Cap: 2% (green: 2-2.5%)
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Typography variant="caption">
                    ⚫ Micro Cap: 2% (green: 2-2.5%)
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Phase 3: Enhanced Financial Health Metrics */}
      {financialHealth && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" fontWeight="bold" gutterBottom sx={{ mb: 3 }}>
            Financial Health (Phase 3)
          </Typography>
          
          <Grid container spacing={3}>
            {/* Overall Financial Health Score */}
            <Grid item xs={12}>
              <Paper sx={{ p: 4, borderRadius: 3, textAlign: 'center', bgcolor: 'rgba(96, 165, 250, 0.05)' }}>
                <Typography variant="h2" fontWeight="bold" color="primary.main" sx={{ mb: 1 }}>
                  {financialHealth.financial_health_score}/100
                </Typography>
                <Typography variant="h6" gutterBottom>
                  Overall Financial Health Score
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Comprehensive score based on multiple financial factors
                </Typography>
                
                {/* Score Breakdown */}
                <Grid container spacing={2} sx={{ mt: 3 }}>
                  <Grid item xs={6} sm={3}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Emergency Fund</Typography>
                      <Typography variant="h6" color="success.main">{financialHealth.score_breakdown.emergency_fund_score}/25</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Savings Rate</Typography>
                      <Typography variant="h6" color="primary.main">{financialHealth.score_breakdown.savings_rate_score}/25</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Allocation</Typography>
                      <Typography variant="h6" color="warning.main">{financialHealth.score_breakdown.allocation_score}/25</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Debt Management</Typography>
                      <Typography variant="h6" color="error.main">{financialHealth.score_breakdown.debt_score}/25</Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* Emergency Fund Status */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, borderRadius: 3 }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Emergency Fund
                </Typography>
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <Typography variant="h3" fontWeight="bold" color="success.main">
                    {financialHealth.emergency_fund.months_covered} 
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    months covered
                  </Typography>
                  <Chip 
                    label={`Target: ${financialHealth.emergency_fund.target_months} months`}
                    size="small"
                    sx={{ mt: 2 }}
                    color={financialHealth.emergency_fund.status === 'excellent' ? 'success' : 'warning'}
                  />
                </Box>
                <Divider sx={{ my: 2 }} />
                <Typography variant="caption" color="text.secondary">Current Balance</Typography>
                <Typography variant="h6">{formatCurrency(financialHealth.emergency_fund.current_balance)}</Typography>
              </Paper>
            </Grid>

            {/* Savings Rate */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, borderRadius: 3 }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Savings Rate
                </Typography>
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <Typography variant="h3" fontWeight="bold" color="primary.main">
                    {financialHealth.savings_rate.current_rate}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    of income saved
                  </Typography>
                  <Chip 
                    label={financialHealth.savings_rate.status.replace('_', ' ')}
                    size="small"
                    sx={{ mt: 2, textTransform: 'capitalize' }}
                    color={financialHealth.savings_rate.status === 'excellent' ? 'success' : 'primary'}
                  />
                </Box>
                <Divider sx={{ my: 2 }} />
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Monthly Income</Typography>
                    <Typography variant="body2" fontWeight="medium">{formatCurrency(financialHealth.savings_rate.monthly_income)}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Monthly Expense</Typography>
                    <Typography variant="body2" fontWeight="medium">{formatCurrency(financialHealth.savings_rate.monthly_expense)}</Typography>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* Debt-to-Income Ratio */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, borderRadius: 3 }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Debt-to-Income
                </Typography>
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <Typography variant="h3" fontWeight="bold" color="success.main">
                    {financialHealth.debt_to_income.ratio}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    debt ratio
                  </Typography>
                  <Chip 
                    label={financialHealth.debt_to_income.status.replace('_', ' ')}
                    size="small"
                    sx={{ mt: 2, textTransform: 'capitalize' }}
                    color="success"
                  />
                </Box>
                <Divider sx={{ my: 2 }} />
                <Typography variant="caption" color="text.secondary">
                  Lower is better • &lt;20% excellent • 20-35% good
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default Health;

