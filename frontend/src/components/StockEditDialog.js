import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Typography,
  Alert,
  Snackbar,
  Autocomplete,
} from '@mui/material';
import { stockAPI, sectorAPI } from '../services/api';

const emptyForm = () => ({
  symbol: '',
  name: '',
  group_name: '',
  sector: '',
  market_cap: '',
  current_price: '',
  day_change_pct: null,
  buy_zone_price: '',
  sell_zone_price: '',
  average_zone_price: '',
  status: 'WATCHING',
  notes: '',
});

const stockToForm = (stock) => ({
  symbol: stock.symbol,
  name: stock.name,
  group_name: stock.group_name || '',
  sector: stock.sector || '',
  market_cap: stock.market_cap || '',
  buy_zone_price: stock.buy_zone_price || '',
  sell_zone_price: stock.sell_zone_price || '',
  average_zone_price: stock.average_zone_price || '',
  status: stock.status || 'WATCHING',
  current_price: stock.current_price ?? '',
  day_change_pct: stock.day_change_pct ?? null,
  notes: stock.notes || '',
});

/**
 * Shared add/edit stock dialog (same fields as Stock Tracking).
 * @param {boolean} open
 * @param {function} onClose
 * @param {object|null} stock — null = add mode; object with id = edit mode
 * @param {function} onSuccess — called after successful save (before dialog closes)
 */
const StockEditDialog = ({ open, onClose, stock, onSuccess }) => {
  const [groups, setGroups] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [sectorMappings, setSectorMappings] = useState({});
  const [formData, setFormData] = useState(emptyForm);
  const [fetchingDetails, setFetchingDetails] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  const showSnackbar = useCallback((message, severity) => {
    setSnackbar({ open: true, message, severity });
  }, []);

  const fetchGroups = useCallback(async () => {
    try {
      const response = await stockAPI.getGroups();
      setGroups(response.data);
    } catch (error) {
      console.error('Error fetching groups:', error);
    }
  }, []);

  const fetchSectors = useCallback(async () => {
    try {
      const response = await stockAPI.getSectors();
      setSectors(response.data);
    } catch (error) {
      console.error('Error fetching sectors:', error);
    }
  }, []);

  const fetchParentSectors = useCallback(async () => {
    try {
      const mappingsRes = await sectorAPI.getParentMappings();
      const mappings = {};
      mappingsRes.data.forEach((m) => {
        mappings[m.sector_name] = m.parent_sector;
      });
      setSectorMappings(mappings);
    } catch (error) {
      console.error('Error fetching parent sectors:', error);
    }
  }, []);

  useEffect(() => {
    fetchGroups();
    fetchSectors();
    fetchParentSectors();
  }, [fetchGroups, fetchSectors, fetchParentSectors]);

  // Remount freeSolo Autocompletes when switching stocks — MUI can keep stale input text otherwise.
  const stockIdentityKey = stock?.id != null ? `id-${stock.id}` : 'add';

  useEffect(() => {
    if (!open) return;
    if (stock) {
      setFormData(stockToForm(stock));
    } else {
      setFormData(emptyForm());
    }
  }, [open, stock]);

  const editingStock = stock && stock.id != null ? stock : null;

  const handleSymbolBlur = async () => {
    const symbol = formData.symbol.trim().toUpperCase();

    const needsFetch =
      !editingStock &&
      symbol &&
      (symbol.endsWith('.NS') || symbol.endsWith('.BO')) &&
      (!formData.name || !formData.sector || !formData.market_cap);

    if (needsFetch) {
      setFetchingDetails(true);
      try {
        const response = await stockAPI.fetchDetails(symbol);
        const details = response.data;

        setFormData((prev) => ({
          ...prev,
          symbol,
          name: details.name || prev.name,
          current_price: details.price || prev.current_price,
          day_change_pct: details.day_change_pct !== undefined ? details.day_change_pct : prev.day_change_pct,
          status: details.status || prev.status,
          sector: details.sector || prev.sector,
          market_cap: details.market_cap || prev.market_cap,
        }));

        if (details.in_holdings) {
          showSnackbar(`Stock found in holdings (${details.quantity} shares) - Status set to HOLD`, 'info');
        } else {
          showSnackbar('Stock details fetched successfully', 'success');
        }
      } catch (error) {
        if (error.response?.status === 404) {
          showSnackbar('Could not auto-fetch details. Please enter manually.', 'warning');
        }
      } finally {
        setFetchingDetails(false);
      }
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    if (!formData.symbol || !formData.name) {
      showSnackbar('Stock symbol and name are required', 'error');
      return;
    }

    try {
      if (editingStock) {
        await stockAPI.update(editingStock.id, formData);
        showSnackbar('Stock updated successfully', 'success');
      } else {
        await stockAPI.create(formData);
        showSnackbar('Stock added successfully', 'success');
      }
      if (onSuccess) onSuccess();
      onClose();
    } catch (error) {
      showSnackbar(error.response?.data?.error || 'Error saving stock', 'error');
      console.error('Error saving stock:', error);
    }
  };

  const handleDialogClose = () => {
    onClose();
  };

  return (
    <>
      <Dialog open={open} onClose={handleDialogClose} maxWidth="md" fullWidth>
        <DialogTitle sx={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
          {editingStock ? 'Edit Stock' : 'Add New Stock'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Stock Symbol *"
                name="symbol"
                value={formData.symbol}
                onChange={handleInputChange}
                onBlur={handleSymbolBlur}
                disabled={!!editingStock || fetchingDetails}
                placeholder="e.g., RELIANCE.NS"
                helperText={fetchingDetails ? 'Fetching stock details...' : 'Enter symbol with .NS or .BO suffix'}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Company Name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Auto-fetched from symbol"
                helperText="Leave blank to auto-fetch"
                disabled={fetchingDetails}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <Autocomplete
                key={`group-ac-${stockIdentityKey}`}
                freeSolo
                options={groups}
                value={formData.group_name}
                onChange={(event, newValue) => {
                  setFormData((prev) => ({ ...prev, group_name: newValue || '' }));
                }}
                onInputChange={(event, newInputValue) => {
                  setFormData((prev) => ({ ...prev, group_name: newInputValue }));
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Group/Category"
                    placeholder="e.g., Bull Run"
                    helperText="Select existing or type new"
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Market Cap</InputLabel>
                <Select
                  name="market_cap"
                  value={formData.market_cap}
                  label="Market Cap"
                  onChange={handleInputChange}
                >
                  <MenuItem value="">None</MenuItem>
                  <MenuItem value="Large">Large</MenuItem>
                  <MenuItem value="Mid">Mid</MenuItem>
                  <MenuItem value="Small">Small</MenuItem>
                  <MenuItem value="Micro">Micro</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Autocomplete
                key={`sector-ac-${stockIdentityKey}`}
                freeSolo
                options={sectors}
                value={formData.sector}
                onChange={(event, newValue) => {
                  setFormData((prev) => ({ ...prev, sector: newValue || '' }));
                }}
                onInputChange={(event, newInputValue) => {
                  setFormData((prev) => ({ ...prev, sector: newInputValue }));
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Sector"
                    placeholder="e.g., FMCG, Auto"
                    helperText={
                      formData.sector && sectorMappings[formData.sector]
                        ? `Parent: ${sectorMappings[formData.sector]}`
                        : 'Select existing or type new'
                    }
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Current Price (Optional)"
                name="current_price"
                type="number"
                value={formData.current_price}
                onChange={handleInputChange}
                placeholder="Auto-fetched from Screener.in"
                helperText={editingStock ? 'Auto-updates on Refresh Prices' : 'Auto-fetches from symbol'}
                disabled={fetchingDetails}
              />
              {formData.day_change_pct !== null && formData.day_change_pct !== undefined && (
                <Box sx={{ mt: 1 }}>
                  <Chip
                    label={`1D Change: ${formData.day_change_pct >= 0 ? '+' : ''}${formData.day_change_pct.toFixed(2)}%`}
                    size="small"
                    sx={{
                      bgcolor: formData.day_change_pct >= 0 ? '#22c55e' : '#ef4444',
                      color: 'white',
                      fontWeight: 'bold',
                    }}
                  />
                </Box>
              )}
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={fetchingDetails}>
                <InputLabel>Status</InputLabel>
                <Select name="status" value={formData.status} label="Status" onChange={handleInputChange}>
                  <MenuItem value="WATCHING">Watching</MenuItem>
                  <MenuItem value="HOLD">Holding</MenuItem>
                </Select>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, ml: 1.5 }}>
                  {!editingStock && 'Auto-set: WATCHING (not in portfolio) or HOLDING (in portfolio)'}
                </Typography>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Buy Zone"
                name="buy_zone_price"
                value={formData.buy_zone_price}
                onChange={handleInputChange}
                placeholder="250-300 or 275"
                helperText="Range or exact price"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Average Zone"
                name="average_zone_price"
                value={formData.average_zone_price}
                onChange={handleInputChange}
                placeholder="150-180 or 165"
                helperText="Range or exact price"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Sell Zone"
                name="sell_zone_price"
                value={formData.sell_zone_price}
                onChange={handleInputChange}
                placeholder="700-800 or 750"
                helperText="Range or exact price"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                placeholder="Add your analysis, chart patterns, reasons..."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 2.5 }}>
          <Button onClick={handleDialogClose} sx={{ borderRadius: 2 }}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} variant="contained" sx={{ borderRadius: 2, px: 4 }}>
            {editingStock ? 'Save' : 'Add Stock'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default StockEditDialog;
