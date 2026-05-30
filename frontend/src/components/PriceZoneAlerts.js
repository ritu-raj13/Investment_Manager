import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  IconButton,
  Paper,
  Snackbar,
  Tooltip,
  Typography,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import AddShoppingCartIcon from '@mui/icons-material/AddShoppingCart';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import SellIcon from '@mui/icons-material/Sell';
import { recommendationsAPI, stockAPI } from '../services/api';
import StockEditDialog from './StockEditDialog';

const PriceZoneAlerts = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [editStock, setEditStock] = useState(null);
  const [editOpen, setEditOpen] = useState(false);
  const [editKey, setEditKey] = useState(0);

  useEffect(() => {
    fetchPriceZones();
  }, []);

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const fetchPriceZones = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const response = await recommendationsAPI.getPriceZones();
      setData(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load price zone alerts.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (value == null) return '-';
    return `Rs.${Number(value).toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const zoneCard = (title, icon, list, color) => (
    <Grid item xs={12} md={4}>
      <Paper sx={{ p: 2, borderRadius: 3, height: '100%', border: '1px solid rgba(148,163,184,0.2)' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
          {icon}
          <Typography variant="h6" sx={{ ml: 1 }} fontWeight="bold">
            {title}
          </Typography>
          <Chip size="small" label={list.length} sx={{ ml: 'auto' }} color={color} />
        </Box>
        {list.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No alerts right now.
          </Typography>
        ) : (
          <Box sx={{ maxHeight: 320, overflowY: 'auto', pr: 1 }}>
            {list.map((item) => (
              <Paper
                key={`${title}-${item.id}`}
                sx={{ p: 1.25, mb: 1, borderRadius: 2, background: 'rgba(15,23,42,0.65)' }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="body2" fontWeight="bold" noWrap>
                      {item.symbol.replace('.NS', '').replace('.BO', '')}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {item.name}
                    </Typography>
                  </Box>
                  <Tooltip title="Edit tracking">
                    <IconButton
                      size="small"
                      sx={{ ml: 'auto' }}
                      onClick={() => handleEditStock(item.id)}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Typography variant="caption" color="text.secondary" display="block">
                  LTP: {formatCurrency(item.current_price)} | Zone: {item.zone}
                </Typography>
                {item.distance_pct != null && (
                  <Chip
                    size="small"
                    label={`${item.distance_type === 'above' ? '+' : '-'}${Math.abs(item.distance_pct).toFixed(2)}%`}
                    sx={{ mt: 0.75 }}
                  />
                )}
              </Paper>
            ))}
          </Box>
        )}
      </Paper>
    </Grid>
  );

  const handleEditStock = async (stockId) => {
    try {
      const response = await stockAPI.getById(stockId);
      setEditStock(response.data);
      setEditKey((v) => v + 1);
      setEditOpen(true);
    } catch (err) {
      showSnackbar('Failed to load stock details', 'error');
    }
  };

  const actionItems = data?.action_items || {
    in_buy_zone: [],
    near_buy_zone: [],
    in_sell_zone: [],
    near_sell_zone: [],
    in_average_zone: [],
    near_average_zone: [],
  };

  const buySignals = [...actionItems.in_buy_zone, ...actionItems.near_buy_zone];
  const averageSignals = [...actionItems.in_average_zone, ...actionItems.near_average_zone];
  const sellSignals = [...actionItems.in_sell_zone, ...actionItems.near_sell_zone];

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Price Zone Alerts
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
        Actionable price-zone opportunities only. Use these alerts for entry, averaging, and exit timing.
      </Typography>

      <Grid container spacing={2} sx={{ mb: 2.5 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Buy Opportunities</Typography>
              <Typography variant="h5" fontWeight="bold">{buySignals.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Average Opportunities</Typography>
              <Typography variant="h5" fontWeight="bold">{averageSignals.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Sell Opportunities</Typography>
              <Typography variant="h5" fontWeight="bold">{sellSignals.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        {zoneCard('Buy Alerts', <ShoppingCartIcon color="success" />, buySignals, 'success')}
        {zoneCard('Average Alerts', <AddShoppingCartIcon color="warning" />, averageSignals, 'warning')}
        {zoneCard('Sell Alerts', <SellIcon color="error" />, sellSignals, 'error')}
      </Grid>

      {editStock && (
        <StockEditDialog
          key={editKey}
          open={editOpen}
          onClose={() => setEditOpen(false)}
          stock={editStock}
          onSuccess={() => {
            fetchPriceZones(true);
            showSnackbar('Stock updated successfully', 'success');
          }}
        />
      )}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3500}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
      >
        <Alert severity={snackbar.severity}>{snackbar.message}</Alert>
      </Snackbar>
    </Box>
  );
};

export default PriceZoneAlerts;
