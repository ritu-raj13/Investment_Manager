import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  CircularProgress,
  Divider,
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
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

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

  const formatPercent = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
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
        sectorMap[sector] = 0;
      }
      sectorMap[sector] += holding.invested_amount;
    });

    return Object.entries(sectorMap).map(([sector, value]) => ({
      name: sector,
      value: value
    })).sort((a, b) => b.value - a.value);
  };

  const getMarketCapAllocationData = () => {
    if (!data.holdings || data.holdings.length === 0) return [];
    
    const marketCapMap = {};
    data.holdings.forEach(holding => {
      const marketCap = holding.market_cap || 'Unknown';
      if (!marketCapMap[marketCap]) {
        marketCapMap[marketCap] = 0;
      }
      marketCapMap[marketCap] += holding.invested_amount;
    });

    return Object.entries(marketCapMap).map(([marketCap, value]) => ({
      name: marketCap,
      value: value
    })).sort((a, b) => b.value - a.value);
  };

  const COLORS = ['#60a5fa', '#4ade80', '#fbbf24', '#f87171', '#a78bfa', '#ec4899', '#14b8a6', '#f97316'];

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

  const { portfolio_metrics, action_items, action_items_count, stocks_tracked, total_transactions, top_gainers, top_losers } = data;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Analytics Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Portfolio insights and actionable recommendations
        </Typography>
      </Box>

      {/* Action Items Card - Focused on insights, not duplicate metrics */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
        <Card sx={{ 
          borderRadius: 3, 
          bgcolor: 'warning.dark', 
          color: 'white',
          minWidth: 300,
          boxShadow: 3
        }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ color: 'white' }}>
                Action Items
              </Typography>
              <NotificationsActiveIcon sx={{ fontSize: 32 }} />
            </Box>
            <Typography variant="h3" fontWeight="bold" gutterBottom>
              {action_items_count}
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
              {action_items_count > 0 ? 'Stocks require attention' : 'No actions needed'}
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Action Items Section */}
      {action_items_count > 0 && (
        <Paper sx={{ p: 3, mb: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <NotificationsActiveIcon color="warning" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight="bold">
              Stocks Requiring Action
            </Typography>
            <Tooltip title="Stocks currently in or near your defined buy/sell/average zones">
              <IconButton size="small" sx={{ ml: 1 }}>
                <InfoOutlinedIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>

          <Grid container spacing={2}>
            {/* In Buy Zone */}
            {action_items.in_buy_zone.length > 0 && (
              <Grid item xs={12} md={6}>
                <Card sx={{ borderRadius: 2, bgcolor: 'success.dark', color: 'white' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <ShoppingCartIcon sx={{ mr: 1 }} />
                      <Typography variant="h6" fontWeight="bold">
                        In Buy Zone ({action_items.in_buy_zone.length})
                      </Typography>
                    </Box>
                    <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                      {action_items.in_buy_zone.map((stock, idx) => (
                        <Box key={idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.in_buy_zone.length - 1 ? '1px solid rgba(255,255,255,0.2)' : 'none' }}>
                          <Typography variant="body1" fontWeight="bold">
                            {stock.symbol.replace('.NS', '').replace('.BO', '')}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                            {stock.name} • {stock.sector}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                            <Typography variant="caption">
                              Current: ₹{stock.current_price}
                            </Typography>
                            <Typography variant="caption">
                              Zone: ₹{stock.zone}
                            </Typography>
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* In Sell Zone */}
            {action_items.in_sell_zone.length > 0 && (
              <Grid item xs={12} md={6}>
                <Card sx={{ borderRadius: 2, bgcolor: 'error.dark', color: 'white' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <SellIcon sx={{ mr: 1 }} />
                      <Typography variant="h6" fontWeight="bold">
                        In Sell Zone ({action_items.in_sell_zone.length})
                      </Typography>
                    </Box>
                    <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                      {action_items.in_sell_zone.map((stock, idx) => (
                        <Box key={idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.in_sell_zone.length - 1 ? '1px solid rgba(255,255,255,0.2)' : 'none' }}>
                          <Typography variant="body1" fontWeight="bold">
                            {stock.symbol.replace('.NS', '').replace('.BO', '')}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                            {stock.name} • {stock.sector}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                            <Typography variant="caption">
                              Current: ₹{stock.current_price}
                            </Typography>
                            <Typography variant="caption">
                              Zone: ₹{stock.zone}
                            </Typography>
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Near Buy Zone */}
            {action_items.near_buy_zone.length > 0 && (
              <Grid item xs={12} md={6}>
                <Card sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingDownIcon color="success" sx={{ mr: 1 }} />
                      <Typography variant="h6" fontWeight="bold">
                        Near Buy Zone ({action_items.near_buy_zone.length})
                      </Typography>
                    </Box>
                    <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                      {action_items.near_buy_zone.map((stock, idx) => (
                        <Box key={idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.near_buy_zone.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none' }}>
                          <Typography variant="body1" fontWeight="bold">
                            {stock.symbol.replace('.NS', '').replace('.BO', '')}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {stock.name}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                            <Typography variant="caption">
                              ₹{stock.current_price}
                            </Typography>
                            <Chip 
                              label={`${stock.distance_pct.toFixed(1)}% above zone`}
                              size="small"
                              color="success"
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Near Sell Zone */}
            {action_items.near_sell_zone.length > 0 && (
              <Grid item xs={12} md={6}>
                <Card sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingUpIcon color="error" sx={{ mr: 1 }} />
                      <Typography variant="h6" fontWeight="bold">
                        Near Sell Zone ({action_items.near_sell_zone.length})
                      </Typography>
                    </Box>
                    <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                      {action_items.near_sell_zone.map((stock, idx) => (
                        <Box key={idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.near_sell_zone.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none' }}>
                          <Typography variant="body1" fontWeight="bold">
                            {stock.symbol.replace('.NS', '').replace('.BO', '')}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {stock.name}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                            <Typography variant="caption">
                              ₹{stock.current_price}
                            </Typography>
                            <Chip 
                              label={`${stock.distance_pct.toFixed(1)}% below zone`}
                              size="small"
                              color="error"
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* In Average Zone */}
            {action_items.in_average_zone && action_items.in_average_zone.length > 0 && (
              <Grid item xs={12} md={6}>
                <Card sx={{ borderRadius: 2, bgcolor: 'warning.dark', color: 'white' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AddShoppingCartIcon sx={{ mr: 1 }} />
                      <Typography variant="h6" fontWeight="bold">
                        In Average Zone ({action_items.in_average_zone.length})
                      </Typography>
                    </Box>
                    <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                      {action_items.in_average_zone.map((stock, idx) => (
                        <Box key={idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.in_average_zone.length - 1 ? '1px solid rgba(255,255,255,0.2)' : 'none' }}>
                          <Typography variant="body1" fontWeight="bold">
                            {stock.symbol.replace('.NS', '').replace('.BO', '')}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                            {stock.name} • {stock.sector}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                            <Typography variant="caption">
                              Current: ₹{stock.current_price}
                            </Typography>
                            <Typography variant="caption">
                              Zone: ₹{stock.zone}
                            </Typography>
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Near Average Zone */}
            {action_items.near_average_zone && action_items.near_average_zone.length > 0 && (
              <Grid item xs={12} md={6}>
                <Card sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AddShoppingCartIcon color="warning" sx={{ mr: 1 }} />
                      <Typography variant="h6" fontWeight="bold">
                        Near Average Zone ({action_items.near_average_zone.length})
                      </Typography>
                    </Box>
                    <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                      {action_items.near_average_zone.map((stock, idx) => (
                        <Box key={idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.near_average_zone.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none' }}>
                          <Typography variant="body1" fontWeight="bold">
                            {stock.symbol.replace('.NS', '').replace('.BO', '')}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {stock.name}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                            <Typography variant="caption">
                              ₹{stock.current_price}
                            </Typography>
                            <Chip 
                              label={`${stock.distance_pct.toFixed(1)}% ${stock.distance_type} zone`}
                              size="small"
                              color="warning"
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        </Paper>
      )}

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

      {/* Portfolio Charts */}
      {data.holdings && data.holdings.length > 0 && (
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

          {/* Sector Allocation */}
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

          {/* Market Cap Allocation */}
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
      )}

      {/* Quick Stats */}
      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={4}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {stocks_tracked}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Stocks Tracked
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {portfolio_metrics.holdings_count}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Active Holdings
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {total_transactions}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Transactions
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Analytics;

