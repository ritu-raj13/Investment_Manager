import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import SellIcon from '@mui/icons-material/Sell';
import AddShoppingCartIcon from '@mui/icons-material/AddShoppingCart';
import { analyticsAPI } from '../services/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const Analytics = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getDashboard();
      setData(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load analytics data');
      console.error('Analytics error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // Prepare chart data
  const getPortfolioComparisonData = () => {
    return [
      {
        name: 'Invested',
        value: portfolio_metrics.total_invested,
        fill: '#60a5fa'
      },
      {
        name: 'Current Value',
        value: portfolio_metrics.total_current_value,
        fill: portfolio_metrics.total_gain_loss >= 0 ? '#4ade80' : '#f87171'
      }
    ];
  };

  const getSectorAllocationData = () => {
    if (!data.holdings || data.holdings.length === 0) return [];
    
    const sectorMap = {};
    data.holdings.forEach(holding => {
      // Get sector from stocks (we need to add it to the holdings response or use a workaround)
      const sector = holding.sector || 'Other';
      if (!sectorMap[sector]) {
        sectorMap[sector] = {
          value: 0,
          stocks: []
        };
      }
      sectorMap[sector].value += holding.invested_amount;
      sectorMap[sector].stocks.push({
        symbol: holding.symbol.replace('.NS', '').replace('.BO', ''),
        name: holding.name,
        amount: holding.invested_amount
      });
    });

    return Object.entries(sectorMap).map(([sector, data]) => ({
      name: sector,
      value: data.value,
      count: data.stocks.length,
      stocks: data.stocks.sort((a, b) => b.amount - a.amount)
    })).sort((a, b) => b.value - a.value);
  };

  const getMarketCapAllocationData = () => {
    if (!data.holdings || data.holdings.length === 0) return [];
    
    const marketCapMap = {};
    data.holdings.forEach(holding => {
      const marketCap = holding.market_cap || 'Unknown';
      if (!marketCapMap[marketCap]) {
        marketCapMap[marketCap] = {
          value: 0,
          stocks: []
        };
      }
      marketCapMap[marketCap].value += holding.invested_amount;
      marketCapMap[marketCap].stocks.push({
        symbol: holding.symbol.replace('.NS', '').replace('.BO', ''),
        name: holding.name,
        amount: holding.invested_amount
      });
    });

    return Object.entries(marketCapMap).map(([marketCap, data]) => ({
      name: marketCap,
      value: data.value,
      count: data.stocks.length,
      stocks: data.stocks.sort((a, b) => b.amount - a.amount)
    })).sort((a, b) => b.value - a.value);
  };

  const COLORS = ['#60a5fa', '#4ade80', '#fbbf24', '#f87171', '#a78bfa', '#ec4899', '#14b8a6', '#f97316'];

  // Custom tooltip for allocation charts (investment value)
  const CustomAllocationTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      return (
        <Box
          sx={{
            backgroundColor: '#1e293b',
            border: '2px solid #475569',
            borderRadius: '8px',
            padding: '12px 16px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            minWidth: '180px'
          }}
        >
          <Typography variant="body1" fontWeight="bold" sx={{ color: '#ffffff', mb: 0.5 }}>
            {data.name}
          </Typography>
          <Typography variant="body2" sx={{ color: '#94a3b8' }}>
            {formatCurrency(data.value)}
          </Typography>
        </Box>
      );
    }
    return null;
  };

  // Get stock count data by sector
  const getStockCountBySectorData = () => {
    if (!data.holdings || data.holdings.length === 0) return [];
    
    const sectorMap = {};
    data.holdings.forEach(holding => {
      const sector = holding.sector || 'Other';
      if (!sectorMap[sector]) {
        sectorMap[sector] = 0;
      }
      sectorMap[sector] += 1;
    });

    return Object.entries(sectorMap)
      .map(([sector, count]) => ({
        name: sector,
        count: count,
        fill: COLORS[Object.keys(sectorMap).indexOf(sector) % COLORS.length]
      }))
      .sort((a, b) => b.count - a.count);
  };

  // Get stock count data by market cap
  const getStockCountByMarketCapData = () => {
    if (!data.holdings || data.holdings.length === 0) return [];
    
    const marketCapMap = {};
    data.holdings.forEach(holding => {
      const marketCap = holding.market_cap || 'Unknown';
      if (!marketCapMap[marketCap]) {
        marketCapMap[marketCap] = 0;
      }
      marketCapMap[marketCap] += 1;
    });

    return Object.entries(marketCapMap)
      .map(([marketCap, count]) => ({
        name: marketCap,
        count: count,
        fill: COLORS[Object.keys(marketCapMap).indexOf(marketCap) % COLORS.length]
      }))
      .sort((a, b) => b.count - a.count);
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

  const { portfolio_metrics, stocks_tracked, total_transactions, top_gainers, top_losers } = data;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Analytics Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Portfolio performance visualization and insights
        </Typography>
      </Box>

      {/* Top Gainers and Losers */}
      {((top_gainers && top_gainers.length > 0) || (top_losers && top_losers.length > 0)) && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {/* Top Gainers */}
          {top_gainers && top_gainers.length > 0 && (
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, borderRadius: 3, bgcolor: 'rgba(74, 222, 128, 0.05)', border: '1px solid rgba(74, 222, 128, 0.2)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TrendingUpIcon sx={{ color: '#22c55e', mr: 1, fontSize: 28 }} />
                  <Typography variant="h6" fontWeight="bold" color="success.main">
                    Top 5 Gainers
                  </Typography>
                </Box>
                {top_gainers.map((stock, idx) => (
                  <Card key={idx} sx={{ mb: 1.5, bgcolor: 'rgba(74, 222, 128, 0.08)', borderRadius: 2 }}>
                    <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="body1" fontWeight="bold">
                            {stock.symbol.replace('.NS', '').replace('.BO', '')}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {stock.name}
                          </Typography>
                        </Box>
                        <Box sx={{ textAlign: 'right' }}>
                          <Chip
                            label={`+${stock.gain_loss_pct.toFixed(2)}%`}
                            size="small"
                            sx={{
                              bgcolor: '#22c55e',
                              color: 'white',
                              fontWeight: 'bold',
                              fontSize: '0.875rem'
                            }}
                          />
                          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                            {formatCurrency(stock.gain_loss)}
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Paper>
            </Grid>
          )}

          {/* Top Losers */}
          {top_losers && top_losers.length > 0 && (
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, borderRadius: 3, bgcolor: 'rgba(248, 113, 113, 0.05)', border: '1px solid rgba(248, 113, 113, 0.2)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TrendingDownIcon sx={{ color: '#ef4444', mr: 1, fontSize: 28 }} />
                  <Typography variant="h6" fontWeight="bold" color="error.main">
                    Top 5 Losers
                  </Typography>
                </Box>
                {top_losers.map((stock, idx) => (
                  <Card key={idx} sx={{ mb: 1.5, bgcolor: 'rgba(248, 113, 113, 0.08)', borderRadius: 2 }}>
                    <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="body1" fontWeight="bold">
                            {stock.symbol.replace('.NS', '').replace('.BO', '')}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {stock.name}
                          </Typography>
                        </Box>
                        <Box sx={{ textAlign: 'right' }}>
                          <Chip
                            label={`${stock.gain_loss_pct.toFixed(2)}%`}
                            size="small"
                            sx={{
                              bgcolor: '#ef4444',
                              color: 'white',
                              fontWeight: 'bold',
                              fontSize: '0.875rem'
                            }}
                          />
                          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                            {formatCurrency(stock.gain_loss)}
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Paper>
            </Grid>
          )}
        </Grid>
      )}

      {/* Portfolio Charts Row 1: Investment Allocation */}
      {data.holdings && data.holdings.length > 0 && (
        <>
          <Grid container spacing={3} sx={{ mt: 3, mb: 3 }}>
            {/* Portfolio Value Comparison */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, borderRadius: 3, height: '100%' }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Portfolio Value
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={getPortfolioComparisonData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis dataKey="name" stroke="#888" />
                    <YAxis stroke="#888" />
                    <RechartsTooltip 
                      contentStyle={{ 
                        backgroundColor: '#1e293b', 
                        border: '1px solid #475569',
                        borderRadius: '8px',
                        color: '#ffffff',
                        padding: '12px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
                      }}
                      labelStyle={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '4px' }}
                      itemStyle={{ color: '#e2e8f0' }}
                      formatter={(value) => formatCurrency(value)}
                    />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {getPortfolioComparisonData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <Box sx={{ mt: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Invested vs Current Value
                  </Typography>
                </Box>
              </Paper>
            </Grid>

            {/* Sector Allocation (Investment) */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, borderRadius: 3, height: '100%' }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Sector Allocation
                </Typography>
                {getSectorAllocationData().length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={getSectorAllocationData()}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {getSectorAllocationData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <RechartsTooltip content={<CustomAllocationTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                    <Box sx={{ mt: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Investment by Sector
                      </Typography>
                    </Box>
                  </>
                ) : (
                  <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Add sector info to stocks for allocation view
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Grid>

            {/* Market Cap Allocation (Investment) */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, borderRadius: 3, height: '100%' }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Market Cap Allocation
                </Typography>
                {getMarketCapAllocationData().length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={getMarketCapAllocationData()}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {getMarketCapAllocationData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <RechartsTooltip content={<CustomAllocationTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                    <Box sx={{ mt: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Investment by Market Cap
                      </Typography>
                    </Box>
                  </>
                ) : (
                  <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Add market cap to stocks for allocation view
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Grid>
          </Grid>

          {/* Portfolio Charts Row 2: Stock Count Distribution */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            {/* Number of Stocks by Sector */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, borderRadius: 3, height: '100%' }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Number of Stocks by Sector
                </Typography>
                {getStockCountBySectorData().length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={getStockCountBySectorData()}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                        <XAxis 
                          dataKey="name" 
                          stroke="#888"
                          angle={-45}
                          textAnchor="end"
                          height={80}
                          interval={0}
                        />
                        <YAxis stroke="#888" allowDecimals={false} />
                        <RechartsTooltip 
                          contentStyle={{ 
                            backgroundColor: '#1e293b', 
                            border: '1px solid #475569',
                            borderRadius: '8px',
                            color: '#ffffff',
                            padding: '12px',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
                          }}
                          labelStyle={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '4px' }}
                          itemStyle={{ color: '#e2e8f0' }}
                          formatter={(value) => `${value} ${value === 1 ? 'stock' : 'stocks'}`}
                        />
                        <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                          {getStockCountBySectorData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <Box sx={{ mt: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Stock distribution across sectors
                      </Typography>
                    </Box>
                  </>
                ) : (
                  <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Add sector info to stocks for distribution view
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Grid>

            {/* Number of Stocks by Market Cap */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, borderRadius: 3, height: '100%' }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Number of Stocks by Market Cap
                </Typography>
                {getStockCountByMarketCapData().length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={getStockCountByMarketCapData()}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                        <XAxis 
                          dataKey="name" 
                          stroke="#888"
                          angle={-45}
                          textAnchor="end"
                          height={80}
                          interval={0}
                        />
                        <YAxis stroke="#888" allowDecimals={false} />
                        <RechartsTooltip 
                          contentStyle={{ 
                            backgroundColor: '#1e293b', 
                            border: '1px solid #475569',
                            borderRadius: '8px',
                            color: '#ffffff',
                            padding: '12px',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
                          }}
                          labelStyle={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '4px' }}
                          itemStyle={{ color: '#e2e8f0' }}
                          formatter={(value) => `${value} ${value === 1 ? 'stock' : 'stocks'}`}
                        />
                        <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                          {getStockCountByMarketCapData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <Box sx={{ mt: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Stock distribution by market capitalization
                      </Typography>
                    </Box>
                  </>
                ) : (
                  <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Add market cap to stocks for distribution view
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  );
};

export default Analytics;

