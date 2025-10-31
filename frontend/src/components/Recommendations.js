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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  NotificationsActive as NotificationsActiveIcon,
  InfoOutlined as InfoOutlinedIcon,
  ShoppingCart as ShoppingCartIcon,
  Sell as SellIcon,
  AddShoppingCart as AddShoppingCartIcon,
  ExpandMore as ExpandMoreIcon,
  RemoveCircle as RemoveCircleIcon,
  AddCircle as AddCircleIcon,
} from '@mui/icons-material';
import { recommendationsAPI } from '../services/api';

const Recommendations = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const response = await recommendationsAPI.getDashboard();
      setData(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load recommendations');
      console.error('Recommendations error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
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

  const { rebalancing, action_items, action_items_count } = data;

  // Calculate alert counts
  const sellAlertCount = (action_items.in_sell_zone?.length || 0) + (action_items.near_sell_zone?.length || 0);
  const avgAlertCount = (action_items.in_average_zone?.length || 0) + (action_items.near_average_zone?.length || 0);
  const buyAlertCount = (action_items.in_buy_zone?.length || 0) + (action_items.near_buy_zone?.length || 0);
  
  // Calculate rebalancing alert counts
  const sectorAlerts = rebalancing.sector_rebalancing?.filter(s => s.status === 'overweight' || s.status === 'moderate_overweight').length || 0;
  const marketCapAlerts = rebalancing.market_cap_rebalancing?.filter(mc => mc.status === 'overweight' || mc.status === 'moderate_overweight').length || 0;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Recommendations
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Actionable insights for portfolio management and rebalancing
        </Typography>
      </Box>

      {/* Combined Alert Cards at Top */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {/* Price Zone Alerts Combined */}
        <Grid item xs={12} md={6}>
          <Card sx={{ 
            borderRadius: 3, 
            bgcolor: action_items_count > 0 ? 'warning.dark' : 'success.dark',
            color: 'white',
            boxShadow: 3,
            height: '100%'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight="bold" sx={{ color: 'white' }}>
                  Price Zone Alerts
                </Typography>
                <NotificationsActiveIcon sx={{ fontSize: 32 }} />
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <SellIcon sx={{ fontSize: 28, mb: 0.5 }} />
                    <Typography variant="h3" fontWeight="bold">
                      {sellAlertCount}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                      Sell
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <AddShoppingCartIcon sx={{ fontSize: 28, mb: 0.5 }} />
                    <Typography variant="h3" fontWeight="bold">
                      {avgAlertCount}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                      Average
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <ShoppingCartIcon sx={{ fontSize: 28, mb: 0.5 }} />
                    <Typography variant="h3" fontWeight="bold">
                      {buyAlertCount}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                      Buy
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Rebalancing Alerts Combined */}
        <Grid item xs={12} md={6}>
          <Card sx={{ 
            borderRadius: 3, 
            bgcolor: (sectorAlerts > 0 || marketCapAlerts > 0) ? 'rgba(251, 191, 36, 0.9)' : 'rgba(34, 197, 94, 0.9)', 
            color: 'white',
            boxShadow: 3,
            height: '100%'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight="bold" sx={{ color: 'white' }}>
                  Rebalancing Alerts
                </Typography>
                <InfoOutlinedIcon sx={{ fontSize: 32 }} />
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }} display="block">
                      Sector
                    </Typography>
                    <Typography variant="h3" fontWeight="bold">
                      {sectorAlerts}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                      over-allocated
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }} display="block">
                      Market Cap
                    </Typography>
                    <Typography variant="h3" fontWeight="bold">
                      {marketCapAlerts}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                      over-allocated
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Price Zone Alert Details */}
      {action_items_count > 0 && (
        <Paper sx={{ p: 3, mb: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <NotificationsActiveIcon color="warning" sx={{ mr: 1, fontSize: 28 }} />
            <Typography variant="h5" fontWeight="bold">
              Price Zone Alert Details
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

      {/* Rebalancing Details */}
      <Paper sx={{ p: 3, mb: 3, borderRadius: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TrendingUpIcon color="primary" sx={{ mr: 1, fontSize: 28 }} />
          <Typography variant="h5" fontWeight="bold">
            Rebalancing Details
          </Typography>
          <Tooltip title="Detailed rebalancing suggestions based on allocation thresholds">
            <IconButton size="small" sx={{ ml: 1 }}>
              <InfoOutlinedIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Stocks to Reduce */}
        {rebalancing.stocks_to_reduce && rebalancing.stocks_to_reduce.length > 0 && (
          <Accordion sx={{ mb: 2, borderRadius: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: 'rgba(248, 113, 113, 0.1)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                <RemoveCircleIcon sx={{ color: '#ef4444', mr: 1 }} />
                <Typography fontWeight="bold">
                  Stocks to Reduce ({rebalancing.stocks_to_reduce.length})
                </Typography>
                <Chip
                  label="Over-Allocated"
                  size="small"
                  sx={{ ml: 'auto', mr: 2, bgcolor: '#ef4444', color: 'white' }}
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Symbol</strong></TableCell>
                      <TableCell><strong>Market Cap</strong></TableCell>
                      <TableCell align="right"><strong>Current %</strong></TableCell>
                      <TableCell align="right"><strong>Target %</strong></TableCell>
                      <TableCell align="right"><strong>Reduce By</strong></TableCell>
                      <TableCell><strong>Reason</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {rebalancing.stocks_to_reduce.map((stock, idx) => (
                      <TableRow key={idx}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {stock.symbol.replace('.NS', '').replace('.BO', '')}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {stock.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={stock.market_cap} size="small" />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" color="error">
                            {stock.current_pct}%
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {stock.target_pct}%
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="bold" color="error">
                            {formatCurrency(stock.reduce_amount)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">
                            {stock.reason}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Stocks to Add */}
        {rebalancing.stocks_to_add && rebalancing.stocks_to_add.length > 0 && (
          <Accordion sx={{ mb: 2, borderRadius: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: 'rgba(251, 191, 36, 0.1)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                <AddCircleIcon sx={{ color: '#eab308', mr: 1 }} />
                <Typography fontWeight="bold">
                  Stocks to Add ({rebalancing.stocks_to_add.length})
                </Typography>
                <Chip
                  label="Under-Allocated"
                  size="small"
                  sx={{ ml: 'auto', mr: 2, bgcolor: '#eab308', color: 'white' }}
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Symbol</strong></TableCell>
                      <TableCell><strong>Market Cap</strong></TableCell>
                      <TableCell align="right"><strong>Current %</strong></TableCell>
                      <TableCell align="right"><strong>Target %</strong></TableCell>
                      <TableCell align="right"><strong>Add Amount</strong></TableCell>
                      <TableCell><strong>Reason</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {rebalancing.stocks_to_add.map((stock, idx) => (
                      <TableRow key={idx} sx={{ bgcolor: stock.in_buy_zone ? 'rgba(74, 222, 128, 0.05)' : 'transparent' }}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Box>
                              <Typography variant="body2" fontWeight="bold">
                                {stock.symbol.replace('.NS', '').replace('.BO', '')}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {stock.name}
                              </Typography>
                            </Box>
                            {stock.in_buy_zone && (
                              <Chip
                                label="Buy Zone"
                                size="small"
                                color="success"
                                sx={{ ml: 1 }}
                              />
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip label={stock.market_cap} size="small" />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" color="warning.main">
                            {stock.current_pct}%
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {stock.target_pct}%
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="bold" color="success.main">
                            {formatCurrency(stock.add_amount)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">
                            {stock.reason}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Sector Rebalancing */}
        {rebalancing.sector_rebalancing && rebalancing.sector_rebalancing.length > 0 && (
          <Accordion sx={{ mb: 2, borderRadius: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: 'rgba(96, 165, 250, 0.1)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <InfoOutlinedIcon sx={{ color: '#60a5fa', mr: 1 }} />
                <Typography fontWeight="bold">
                  Sector Rebalancing Insights
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {rebalancing.sector_rebalancing.map((sector, idx) => (
                  <Grid item xs={12} md={6} key={idx}>
                    <Card sx={{ 
                      bgcolor: sector.status === 'overweight' ? 'rgba(248, 113, 113, 0.05)' :
                                sector.status === 'underweight' ? 'rgba(251, 191, 36, 0.05)' :
                                'rgba(74, 222, 128, 0.05)',
                      borderLeft: `4px solid ${
                        sector.status === 'overweight' ? '#ef4444' :
                        sector.status === 'underweight' ? '#eab308' :
                        '#22c55e'
                      }`
                    }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="h6" fontWeight="bold">
                            {sector.sector}
                          </Typography>
                          <Chip 
                            label={`${sector.percentage}%`}
                            size="small"
                            color={
                              sector.status === 'overweight' ? 'error' :
                              sector.status === 'underweight' ? 'warning' :
                              'success'
                            }
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {formatCurrency(sector.invested_amount)} • {sector.num_stocks} {sector.num_stocks === 1 ? 'stock' : 'stocks'}
                        </Typography>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="body2">
                          {sector.recommendation}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Market Cap Rebalancing */}
        {rebalancing.market_cap_rebalancing && rebalancing.market_cap_rebalancing.length > 0 && (
          <Accordion sx={{ borderRadius: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: 'rgba(167, 139, 250, 0.1)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <InfoOutlinedIcon sx={{ color: '#a78bfa', mr: 1 }} />
                <Typography fontWeight="bold">
                  Market Cap Rebalancing Insights
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {rebalancing.market_cap_rebalancing.map((mc, idx) => (
                  <Grid item xs={12} md={6} key={idx}>
                    <Card sx={{ 
                      bgcolor: mc.status === 'overweight' ? 'rgba(248, 113, 113, 0.05)' :
                                mc.status === 'underweight' ? 'rgba(251, 191, 36, 0.05)' :
                                'rgba(74, 222, 128, 0.05)',
                      borderLeft: `4px solid ${
                        mc.status === 'overweight' ? '#ef4444' :
                        mc.status === 'underweight' ? '#eab308' :
                        '#22c55e'
                      }`
                    }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="h6" fontWeight="bold">
                            {mc.market_cap}
                          </Typography>
                          <Chip 
                            label={`${mc.percentage}%`}
                            size="small"
                            color={
                              mc.status === 'overweight' ? 'error' :
                              mc.status === 'underweight' ? 'warning' :
                              'success'
                            }
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {formatCurrency(mc.invested_amount)} • {mc.num_stocks} {mc.num_stocks === 1 ? 'stock' : 'stocks'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                          Target Range: {mc.target_range}
                        </Typography>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="body2">
                          {mc.recommendation}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </AccordionDetails>
          </Accordion>
        )}

        {/* No Rebalancing Needed */}
        {(!rebalancing.stocks_to_reduce || rebalancing.stocks_to_reduce.length === 0) &&
         (!rebalancing.stocks_to_add || rebalancing.stocks_to_add.length === 0) && (
          <Alert severity="success" sx={{ mt: 2 }}>
            ✓ Portfolio is well-balanced! No rebalancing needed at this time.
          </Alert>
        )}
      </Paper>
    </Box>
  );
};

export default Recommendations;

