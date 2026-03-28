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
  Snackbar,
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
  Edit as EditIcon,
} from '@mui/icons-material';
import { recommendationsAPI, stockAPI } from '../services/api';
import StockEditDialog from './StockEditDialog';

const Recommendations = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editStock, setEditStock] = useState(null);
  const [editDialogMountKey, setEditDialogMountKey] = useState(0);
  const [editSnackbar, setEditSnackbar] = useState({ open: false, message: '', severity: 'error' });

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async (options = {}) => {
    const silent = options.silent === true;
    try {
      if (!silent) setLoading(true);
      const response = await recommendationsAPI.getDashboard();
      setData(response.data);
      setError(null);
    } catch (err) {
      if (!silent) setError('Failed to load recommendations');
      console.error('Recommendations error:', err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const handleEditZoneStock = async (stockId) => {
    try {
      const response = await stockAPI.getById(stockId);
      setEditDialogMountKey((k) => k + 1);
      setEditStock(response.data);
      setEditDialogOpen(true);
    } catch (err) {
      setEditSnackbar({
        open: true,
        message: err.response?.data?.error || 'Failed to load stock for editing',
        severity: 'error',
      });
    }
  };

  const handleCloseEditDialog = () => {
    setEditDialogOpen(false);
    setEditStock(null);
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
  const reduceCount = rebalancing.stocks_to_reduce?.length || 0;
  const addCount = rebalancing.stocks_to_add?.length || 0;
  const concentrationAlertCount = sectorAlerts + marketCapAlerts;
  const parentSectorWarningCount = rebalancing.parent_sector_warnings?.length || 0;
  const hasRebalancingAlerts =
    reduceCount > 0 ||
    addCount > 0 ||
    sectorAlerts > 0 ||
    marketCapAlerts > 0 ||
    parentSectorWarningCount > 0;

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

        {/* Rebalancing Alerts Combined (layout mirrors Price Zone Alerts card) */}
        <Grid item xs={12} md={6}>
          <Card sx={{
            borderRadius: 3,
            bgcolor: hasRebalancingAlerts ? 'warning.dark' : 'success.dark',
            color: 'white',
            boxShadow: 3,
            height: '100%',
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight="bold" sx={{ color: 'white' }}>
                  Rebalancing Alerts
                </Typography>
                <NotificationsActiveIcon sx={{ fontSize: 32 }} />
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <RemoveCircleIcon sx={{ fontSize: 28, mb: 0.5 }} />
                    <Typography variant="h3" fontWeight="bold">
                      {reduceCount}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                      Reduce
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <AddCircleIcon sx={{ fontSize: 28, mb: 0.5 }} />
                    <Typography variant="h3" fontWeight="bold">
                      {addCount}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                      Add
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Tooltip title="Sector and market cap overweight flags (moderate or high concentration)">
                    <Box sx={{ textAlign: 'center', cursor: 'default' }}>
                      <TrendingUpIcon sx={{ fontSize: 28, mb: 0.5 }} />
                      <Typography variant="h3" fontWeight="bold">
                        {concentrationAlertCount}
                      </Typography>
                      <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                        Concentration
                      </Typography>
                    </Box>
                  </Tooltip>
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
                        <Box key={stock.id ?? idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.in_buy_zone.length - 1 ? '1px solid rgba(255,255,255,0.2)' : 'none' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
                            <Typography variant="body1" fontWeight="bold">
                              {stock.symbol.replace('.NS', '').replace('.BO', '')}
                            </Typography>
                            {stock.id != null && (
                              <Tooltip title="Edit tracking">
                                <IconButton size="small" onClick={() => handleEditZoneStock(stock.id)} sx={{ color: 'inherit' }}>
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
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
                        <Box key={stock.id ?? idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.in_sell_zone.length - 1 ? '1px solid rgba(255,255,255,0.2)' : 'none' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
                            <Typography variant="body1" fontWeight="bold">
                              {stock.symbol.replace('.NS', '').replace('.BO', '')}
                            </Typography>
                            {stock.id != null && (
                              <Tooltip title="Edit tracking">
                                <IconButton size="small" onClick={() => handleEditZoneStock(stock.id)} sx={{ color: 'inherit' }}>
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
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
                        <Box key={stock.id ?? idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.near_buy_zone.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
                            <Typography variant="body1" fontWeight="bold">
                              {stock.symbol.replace('.NS', '').replace('.BO', '')}
                            </Typography>
                            {stock.id != null && (
                              <Tooltip title="Edit tracking">
                                <IconButton size="small" onClick={() => handleEditZoneStock(stock.id)}>
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
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
                        <Box key={stock.id ?? idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.near_sell_zone.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
                            <Typography variant="body1" fontWeight="bold">
                              {stock.symbol.replace('.NS', '').replace('.BO', '')}
                            </Typography>
                            {stock.id != null && (
                              <Tooltip title="Edit tracking">
                                <IconButton size="small" onClick={() => handleEditZoneStock(stock.id)}>
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
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
                        <Box key={stock.id ?? idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.in_average_zone.length - 1 ? '1px solid rgba(255,255,255,0.2)' : 'none' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
                            <Typography variant="body1" fontWeight="bold">
                              {stock.symbol.replace('.NS', '').replace('.BO', '')}
                            </Typography>
                            {stock.id != null && (
                              <Tooltip title="Edit tracking">
                                <IconButton size="small" onClick={() => handleEditZoneStock(stock.id)} sx={{ color: 'inherit' }}>
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
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
                        <Box key={stock.id ?? idx} sx={{ mb: 1.5, pb: 1.5, borderBottom: idx < action_items.near_average_zone.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
                            <Typography variant="body1" fontWeight="bold">
                              {stock.symbol.replace('.NS', '').replace('.BO', '')}
                            </Typography>
                            {stock.id != null && (
                              <Tooltip title="Edit tracking">
                                <IconButton size="small" onClick={() => handleEditZoneStock(stock.id)}>
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
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

        {/* Sector Rebalancing (Stock Count Based) */}
        {rebalancing.sector_rebalancing && rebalancing.sector_rebalancing.length > 0 && (
          <Accordion sx={{ mb: 2, borderRadius: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: 'rgba(96, 165, 250, 0.1)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <InfoOutlinedIcon sx={{ color: '#60a5fa', mr: 1 }} />
                <Typography fontWeight="bold">
                  Sector Rebalancing (Stock Count Based)
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Alert severity="info" sx={{ mb: 2 }}>
                Strategy: Maximum {rebalancing.sector_rebalancing[0]?.max_stocks_allowed || 2} stocks per sector to maintain diversification
              </Alert>
              <Grid container spacing={2}>
                {rebalancing.sector_rebalancing.map((sector, idx) => (
                  <Grid item xs={12} md={6} key={idx}>
                    <Card sx={{ 
                      bgcolor: sector.status === 'overweight' ? 'rgba(248, 113, 113, 0.05)' :
                                sector.status === 'moderate_overweight' ? 'rgba(251, 191, 36, 0.05)' :
                                sector.status === 'underweight' ? 'rgba(147, 197, 253, 0.05)' :
                                'rgba(74, 222, 128, 0.05)',
                      borderLeft: `4px solid ${
                        sector.status === 'overweight' ? '#ef4444' :
                        sector.status === 'moderate_overweight' ? '#eab308' :
                        sector.status === 'underweight' ? '#3b82f6' :
                        '#22c55e'
                      }`
                    }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="h6" fontWeight="bold">
                            {sector.sector}
                          </Typography>
                          <Box>
                            <Chip 
                              label={`${sector.num_stocks}/${sector.max_stocks_allowed || 2} stocks`}
                              size="small"
                              color={
                                sector.status === 'overweight' ? 'error' :
                                sector.status === 'moderate_overweight' ? 'warning' :
                                'success'
                              }
                              sx={{ mr: 1 }}
                            />
                            <Chip 
                              label={`${sector.percentage.toFixed(2)}%`}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {formatCurrency(sector.current_value || 0)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                          Stocks: {sector.stocks.join(', ')}
                        </Typography>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="body2" fontWeight={sector.status === 'overweight' ? 'bold' : 'normal'}>
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

        {/* Market Cap Rebalancing - Enhanced with Multiple Limits */}
        {rebalancing.market_cap_rebalancing && rebalancing.market_cap_rebalancing.length > 0 && (
          <Accordion sx={{ borderRadius: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: 'rgba(167, 139, 250, 0.1)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <InfoOutlinedIcon sx={{ color: '#a78bfa', mr: 1 }} />
                <Typography fontWeight="bold">
                  Market Cap Rebalancing (Multi-Limit Analysis)
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Alert severity="info" sx={{ mb: 2 }}>
                <strong>Three-Tier Limit System:</strong><br/>
                1️⃣ <strong>Per-Stock %:</strong> Max % per individual stock<br/>
                2️⃣ <strong>Stock Count:</strong> Max number of stocks in category<br/>
                3️⃣ <strong>Portfolio %:</strong> Max total % of portfolio in category
              </Alert>
              
              {/* Total Portfolio Stock Count Warning */}
              {rebalancing.total_stocks > rebalancing.max_total_stocks && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <strong>⚠️ Total Stocks Limit Exceeded:</strong> {rebalancing.total_stocks}/{rebalancing.max_total_stocks} stocks - Consider reducing overall holdings
                </Alert>
              )}
              
              <Grid container spacing={2}>
                {rebalancing.market_cap_rebalancing.map((mc, idx) => (
                  <Grid item xs={12} key={idx}>
                    <Card sx={{ 
                      bgcolor: mc.status === 'overweight' ? 'rgba(248, 113, 113, 0.05)' :
                                mc.status === 'moderate_overweight' ? 'rgba(251, 191, 36, 0.05)' :
                                mc.status === 'underweight' ? 'rgba(147, 197, 253, 0.05)' :
                                'rgba(74, 222, 128, 0.05)',
                      borderLeft: `4px solid ${
                        mc.status === 'overweight' ? '#ef4444' :
                        mc.status === 'moderate_overweight' ? '#eab308' :
                        mc.status === 'underweight' ? '#3b82f6' :
                        '#22c55e'
                      }`
                    }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Typography variant="h6" fontWeight="bold">
                            {mc.market_cap}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                            <Chip 
                              label={`${mc.num_stocks}/${mc.stock_count_limit || 'N/A'} stocks`}
                              size="small"
                              color={mc.status === 'overweight' ? 'error' : 'default'}
                              variant="outlined"
                            />
                            <Chip 
                              label={`${mc.percentage.toFixed(1)}%/${mc.portfolio_pct_limit || 'N/A'}% portfolio`}
                              size="small"
                              color={mc.status === 'overweight' ? 'error' : mc.status === 'moderate_overweight' ? 'warning' : 'success'}
                            />
                            <Chip 
                              label={`Per-stock: ${mc.per_stock_limit || 'N/A'}%`}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                        
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {formatCurrency(mc.current_value || 0)}
                        </Typography>
                        
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                          Stocks: {mc.stocks.join(', ')}
                        </Typography>
                        
                        <Divider sx={{ my: 1.5 }} />
                        
                        <Typography 
                          variant="body2" 
                          fontWeight={mc.status === 'overweight' ? 'bold' : 'normal'}
                          color={mc.status === 'overweight' ? 'error.main' : 'text.primary'}
                        >
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

        {/* Parent Sector Analysis (with 2-stock limit) */}
        {rebalancing.parent_sector_analysis && rebalancing.parent_sector_analysis.length > 0 && (
          <Accordion sx={{ mb: 2, borderRadius: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: 'rgba(236, 72, 153, 0.1)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <InfoOutlinedIcon sx={{ color: '#ec4899', mr: 1 }} />
                <Typography fontWeight="bold">
                  Parent Sector Analysis (Max 2 Stocks/Sector)
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Alert severity="info" sx={{ mb: 2 }}>
                Strategy: Maximum 2 stocks per parent sector to avoid overconcentration
              </Alert>
              <Grid container spacing={2}>
                {rebalancing.parent_sector_analysis.map((ps, idx) => (
                  <Grid item xs={12} md={6} key={idx}>
                    <Card sx={{ 
                      bgcolor: ps.status === 'overconcentrated' ? 'rgba(248, 113, 113, 0.05)' :
                                ps.status === 'at_limit' ? 'rgba(251, 191, 36, 0.05)' :
                                'rgba(74, 222, 128, 0.05)',
                      borderLeft: `4px solid ${
                        ps.status === 'overconcentrated' ? '#ef4444' :
                        ps.status === 'at_limit' ? '#eab308' :
                        '#22c55e'
                      }`
                    }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="h6" fontWeight="bold">
                            {ps.parent_sector}
                          </Typography>
                          <Box>
                            <Chip 
                              label={`${ps.num_stocks}/${ps.stock_limit} stocks`}
                              size="small"
                              color={
                                ps.status === 'overconcentrated' ? 'error' :
                                ps.status === 'at_limit' ? 'warning' :
                                'success'
                              }
                              sx={{ mr: 1 }}
                            />
                            <Chip 
                              label={`${ps.percentage.toFixed(2)}%`}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {formatCurrency(ps.current_value || 0)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                          Stocks: {ps.stocks.join(', ')}
                        </Typography>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="body2" fontWeight={ps.status === 'overconcentrated' ? 'bold' : 'normal'}>
                          {ps.recommendation}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Parent Sector Warnings */}
        {rebalancing.parent_sector_warnings && rebalancing.parent_sector_warnings.length > 0 && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
              ⚠️ Parent Sector Limit Exceeded
            </Typography>
            {rebalancing.parent_sector_warnings.map((warning, idx) => (
              <Typography key={idx} variant="body2" sx={{ mt: 1 }}>
                <strong>{warning.parent_sector}:</strong> {warning.stock_count} stocks ({warning.stocks.join(', ')}) - {warning.recommendation}
              </Typography>
            ))}
          </Alert>
        )}

        {/* No Rebalancing Needed */}
        {(!rebalancing.stocks_to_reduce || rebalancing.stocks_to_reduce.length === 0) &&
         (!rebalancing.stocks_to_add || rebalancing.stocks_to_add.length === 0) && (
          <Alert severity="success" sx={{ mt: 2 }}>
            ✓ Portfolio is well-balanced! No rebalancing needed at this time.
          </Alert>
        )}
      </Paper>

      <StockEditDialog
        key={editDialogMountKey}
        open={editDialogOpen}
        onClose={handleCloseEditDialog}
        stock={editStock}
        onSuccess={() => fetchRecommendations({ silent: true })}
      />

      <Snackbar
        open={editSnackbar.open}
        autoHideDuration={4000}
        onClose={() => setEditSnackbar((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={editSnackbar.severity} sx={{ width: '100%' }} onClose={() => setEditSnackbar((s) => ({ ...s, open: false }))}>
          {editSnackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Recommendations;

