import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
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
  Alert,
  Snackbar,
  Card,
  CardContent,
  CardActions,
  Collapse,
  Autocomplete,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import FilterListIcon from '@mui/icons-material/FilterList';
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore';
import UnfoldLessIcon from '@mui/icons-material/UnfoldLess';
import { stockAPI } from '../services/api';

const StockTracking = () => {
  const [stocks, setStocks] = useState([]);
  const [groups, setGroups] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingStock, setEditingStock] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [expandedGroups, setExpandedGroups] = useState({});
  const [fetchingDetails, setFetchingDetails] = useState(false);
  const [formData, setFormData] = useState({
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

  useEffect(() => {
    fetchStocks();
    fetchGroups();
    fetchSectors();
  }, []);

  useEffect(() => {
    // Expand all groups by default
    const expanded = {};
    groups.forEach(group => {
      expanded[group] = true;
    });
    setExpandedGroups(expanded);
  }, [groups]);

  const fetchStocks = async () => {
    try {
      const response = await stockAPI.getAll();
      setStocks(response.data);
    } catch (error) {
      showSnackbar('Error fetching stocks', 'error');
    }
  };

  const fetchGroups = async () => {
    try {
      const response = await stockAPI.getGroups();
      setGroups(response.data);
    } catch (error) {
      console.error('Error fetching groups:', error);
    }
  };

  const fetchSectors = async () => {
    try {
      const response = await stockAPI.getSectors();
      setSectors(response.data);
    } catch (error) {
      console.error('Error fetching sectors:', error);
    }
  };

  const handleOpenDialog = (stock = null) => {
    if (stock) {
      setEditingStock(stock);
      setFormData({
        symbol: stock.symbol,
        name: stock.name,
        group_name: stock.group_name || '',
        sector: stock.sector || '',
        market_cap: stock.market_cap || '',
        buy_zone_price: stock.buy_zone_price || '',
        sell_zone_price: stock.sell_zone_price || '',
        average_zone_price: stock.average_zone_price || '',
        status: stock.status || 'WATCHING',
        current_price: stock.current_price || '',
        notes: stock.notes || '',
      });
    } else {
      setEditingStock(null);
      setFormData({
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
    }
    setOpenDialog(true);
  };

  const handleSymbolBlur = async () => {
    // Auto-fetch stock details when user enters symbol
    const symbol = formData.symbol.trim().toUpperCase();
    
    // Only fetch if symbol ends with .NS or .BO and name is empty (new stock)
    if (!editingStock && symbol && (symbol.endsWith('.NS') || symbol.endsWith('.BO')) && !formData.name) {
      setFetchingDetails(true);
      try {
        const response = await stockAPI.fetchDetails(symbol);
        const details = response.data;
        
        // Auto-populate fields
        setFormData(prev => ({
          ...prev,
          symbol: symbol,
          name: details.name || prev.name,
          current_price: details.price || prev.current_price,
          day_change_pct: details.day_change_pct !== undefined ? details.day_change_pct : prev.day_change_pct,
          status: details.status || prev.status, // WATCHING or HOLD based on holdings
        }));
        
        if (details.in_holdings) {
          showSnackbar(`Stock found in holdings (${details.quantity} shares) - Status set to HOLD`, 'info');
        } else {
          showSnackbar('Stock details fetched successfully', 'success');
        }
      } catch (error) {
        // Silently fail or show optional warning
        if (error.response?.status === 404) {
          showSnackbar('Could not auto-fetch details. Please enter manually.', 'warning');
        }
      } finally {
        setFetchingDetails(false);
      }
    }
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingStock(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    // Validate required fields
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
      fetchStocks();
      fetchGroups();
      fetchSectors();
      handleCloseDialog();
    } catch (error) {
      showSnackbar(error.response?.data?.error || 'Error saving stock', 'error');
      console.error('Error saving stock:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this stock?')) {
      try {
        await stockAPI.delete(id);
        showSnackbar('Stock deleted successfully', 'success');
        fetchStocks();
        fetchGroups();
      } catch (error) {
        showSnackbar('Error deleting stock', 'error');
      }
    }
  };

  const handleRefreshPrices = async () => {
    try {
      const response = await stockAPI.refreshPrices();
      showSnackbar(response.data.message, 'success');
      fetchStocks();
    } catch (error) {
      showSnackbar('Error refreshing prices', 'error');
    }
  };

  const handleRefreshAlertStocks = async () => {
    try {
      const response = await stockAPI.refreshAlertStocks();
      showSnackbar(response.data.message, 'success');
      fetchStocks();
    } catch (error) {
      showSnackbar(error.response?.data?.error || 'Error refreshing alert stocks', 'error');
    }
  };

  const toggleGroup = (groupName) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupName]: !prev[groupName]
    }));
  };

  const expandAll = () => {
    const expanded = {};
    Object.keys(groupedStocks).forEach(group => {
      expanded[group] = true;
    });
    setExpandedGroups(expanded);
  };

  const collapseAll = () => {
    const collapsed = {};
    Object.keys(groupedStocks).forEach(group => {
      collapsed[group] = false;
    });
    setExpandedGroups(collapsed);
  };

  const showSnackbar = (message, severity) => {
    setSnackbar({ open: true, message, severity });
  };

  const getStatusColor = (status) => {
    switch (status?.toUpperCase()) {
      case 'BUY':
      case 'BUY ZONE':
        return 'success';  // Green
      case 'SELL':
      case 'SELL ZONE':
        return 'error';    // Red
      case 'AVERAGE':
      case 'AVERAGE ZONE':
        return 'warning';  // Yellow/Orange
      case 'WATCHING':
        return 'info';     // Blue (changed from default)
      case 'HOLD':
      case 'HOLD ZONE':
        return 'secondary'; // Purple (changed from default)
      default:
        return 'default';
    }
  };

  const formatStatusDisplay = (status) => {
    // Format status for display (only WATCHING and HOLD are used now)
    if (status === 'HOLD') return 'Holding';
    if (status === 'WATCHING') return 'Watching';
    return status;
  };
  
  const getStatusStyle = (status) => {
    // Simplified styling - only WATCHING and HOLD are used now
    switch (status?.toUpperCase()) {
      case 'WATCHING':
        return { 
          bgcolor: '#64748b', 
          color: '#fff',
          fontWeight: 'bold'
        };
      case 'HOLD':
        return { 
          bgcolor: '#a78bfa', 
          color: '#fff',
          fontWeight: 'bold'
        };
      default:
        return { fontWeight: 'bold' };
    }
  };

  const formatPrice = (price) => {
    if (!price) return '-';
    // If it's a number, format it
    if (typeof price === 'number') {
      return `₹${price.toFixed(2)}`;
    }
    // If it's a string (zone range), just add rupee symbol
    return `₹${price}`;
  };

  const getGroupedStocks = () => {
    let filteredList = stocks;
    
    // Apply search filter
    if (searchTerm.trim()) {
      const search = searchTerm.toLowerCase();
      filteredList = filteredList.filter(stock => 
        stock.symbol?.toLowerCase().includes(search) ||
        stock.name?.toLowerCase().includes(search) ||
        stock.sector?.toLowerCase().includes(search) ||
        stock.status?.toLowerCase().includes(search) ||
        stock.market_cap?.toLowerCase().includes(search)
      );
    }
    
    // Group the filtered stocks
    const grouped = {};
    filteredList.forEach(stock => {
      const group = stock.group_name || 'Ungrouped';
      if (!grouped[group]) {
        grouped[group] = [];
      }
      grouped[group].push(stock);
    });

    // Filter by selected group
    if (selectedGroup !== 'ALL') {
      return { [selectedGroup]: grouped[selectedGroup] || [] };
    }

    return grouped;
  };

  const groupedStocks = getGroupedStocks();
  const stockCount = Object.values(groupedStocks).reduce((acc, stocks) => acc + stocks.length, 0);
  
  // Show search results summary
  const totalStocks = stocks.length;
  const isFiltered = searchTerm || selectedGroup !== 'ALL';

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
            Stock Tracker
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {isFiltered ? (
              <>
                Showing {stockCount} of {totalStocks} stocks
                {searchTerm && ` (search: "${searchTerm}")`}
              </>
            ) : (
              `${stockCount} stocks tracked`
            )}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="warning"
            startIcon={<RefreshIcon />}
            onClick={handleRefreshAlertStocks}
            sx={{ borderRadius: 2 }}
          >
            Refresh Alert Stocks
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefreshPrices}
            sx={{ borderRadius: 2 }}
          >
            Refresh All
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ borderRadius: 2 }}
          >
            Add Stock
          </Button>
        </Box>
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3, borderRadius: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <FilterListIcon color="action" />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search by name, symbol, sector, status, market cap..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <Box sx={{ display: 'flex', alignItems: 'center', mr: 1 }}>
                    <FilterListIcon fontSize="small" color="action" />
                  </Box>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl size="small" fullWidth>
              <InputLabel>Filter by Group</InputLabel>
              <Select
                value={selectedGroup}
                label="Filter by Group"
                onChange={(e) => setSelectedGroup(e.target.value)}
              >
                <MenuItem value="ALL">All Groups</MenuItem>
                {groups.map((group) => (
                  <MenuItem key={group} value={group}>
                    {group}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                size="small"
                variant="outlined"
                startIcon={<UnfoldMoreIcon />}
                onClick={expandAll}
                sx={{ borderRadius: 2, whiteSpace: 'nowrap' }}
              >
                Expand All
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<UnfoldLessIcon />}
                onClick={collapseAll}
                sx={{ borderRadius: 2, whiteSpace: 'nowrap' }}
              >
                Collapse All
              </Button>
            </Box>
          </Grid>
          {(searchTerm || selectedGroup !== 'ALL') && (
            <Grid item>
              <Button
                size="small"
                onClick={() => {
                  setSearchTerm('');
                  setSelectedGroup('ALL');
                }}
              >
                Clear Filters
              </Button>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Grouped Stock Cards */}
      {Object.entries(groupedStocks).map(([groupName, groupStocks]) => (
        <Box key={groupName} sx={{ mb: 3 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              mb: 2,
              cursor: 'pointer',
              '&:hover': { opacity: 0.8 },
            }}
            onClick={() => toggleGroup(groupName)}
          >
            <Typography variant="h6" fontWeight="bold" sx={{ flexGrow: 1 }}>
              {groupName}
            </Typography>
            <Chip label={groupStocks.length} size="small" sx={{ mr: 1 }} />
            <IconButton
              size="small"
              sx={{
                transform: expandedGroups[groupName] ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.3s',
              }}
            >
              <ExpandMoreIcon />
            </IconButton>
          </Box>

          <Collapse in={expandedGroups[groupName]}>
            <Grid container spacing={2}>
              {groupStocks.map((stock) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={stock.id}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      borderRadius: 3,
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 4,
                      },
                    }}
                  >
                    <CardContent sx={{ flexGrow: 1, pb: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Typography variant="h6" component="div" fontWeight="bold">
                          {stock.symbol.replace('.NS', '').replace('.BO', '')}
                        </Typography>
                        <Box>
                          <IconButton
                            size="small"
                            onClick={() => handleOpenDialog(stock)}
                            sx={{ mr: 0.5 }}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDelete(stock.id)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      </Box>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {stock.name}
                      </Typography>

                      {stock.sector && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                          {stock.sector}
                        </Typography>
                      )}

                      <Box sx={{ mb: 2 }}>
                        <Chip
                          label={formatStatusDisplay(stock.status)}
                          size="small"
                          sx={{ 
                            mr: 1, 
                            mb: 1, 
                            ...getStatusStyle(stock.status)
                          }}
                        />
                        {stock.current_price && (
                          <Chip
                            label={formatPrice(stock.current_price)}
                            variant="outlined"
                            size="small"
                            sx={{ mb: 1, mr: 1, fontWeight: 'bold' }}
                          />
                        )}
                        {stock.day_change_pct !== null && stock.day_change_pct !== undefined && (
                          <Chip
                            label={`${stock.day_change_pct >= 0 ? '+' : ''}${stock.day_change_pct.toFixed(2)}%`}
                            size="small"
                            sx={{ 
                              mb: 1, 
                              mr: 1,
                              bgcolor: stock.day_change_pct >= 0 ? '#22c55e' : '#ef4444',
                              color: '#fff',
                              fontWeight: 'bold'
                            }}
                          />
                        )}
                        {stock.market_cap && (
                          <Chip
                            label={stock.market_cap}
                            size="small"
                            variant="outlined"
                            sx={{ mb: 1 }}
                          />
                        )}
                      </Box>

                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                        {stock.buy_zone_price && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Typography variant="caption" color="success.main">
                              Buy Zone:
                            </Typography>
                            <Typography variant="caption" fontWeight="bold">
                              {formatPrice(stock.buy_zone_price)}
                            </Typography>
                          </Box>
                        )}
                        {stock.average_zone_price && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Typography variant="caption" color="warning.main">
                              Average Zone:
                            </Typography>
                            <Typography variant="caption" fontWeight="bold">
                              {formatPrice(stock.average_zone_price)}
                            </Typography>
                          </Box>
                        )}
                        {stock.sell_zone_price && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Typography variant="caption" color="error.main">
                              Sell Zone:
                            </Typography>
                            <Typography variant="caption" fontWeight="bold">
                              {formatPrice(stock.sell_zone_price)}
                            </Typography>
                          </Box>
                        )}
                      </Box>

                      {stock.notes && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                          {stock.notes.length > 80 ? `${stock.notes.substring(0, 80)}...` : stock.notes}
                        </Typography>
                      )}

                      {stock.last_updated && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          Updated: {new Date(stock.last_updated).toLocaleDateString()}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Collapse>
        </Box>
      ))}

      {stockCount === 0 && (
        <Paper sx={{ p: 6, textAlign: 'center', borderRadius: 3 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No stocks found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Add your first stock to get started tracking!
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Stock
          </Button>
        </Paper>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
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
                helperText={fetchingDetails ? "Fetching stock details..." : "Enter symbol with .NS or .BO suffix"}
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
                freeSolo
                options={groups}
                value={formData.group_name}
                onChange={(event, newValue) => {
                  setFormData(prev => ({ ...prev, group_name: newValue || '' }));
                }}
                onInputChange={(event, newInputValue) => {
                  setFormData(prev => ({ ...prev, group_name: newInputValue }));
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
                freeSolo
                options={sectors}
                value={formData.sector}
                onChange={(event, newValue) => {
                  setFormData(prev => ({ ...prev, sector: newValue || '' }));
                }}
                onInputChange={(event, newInputValue) => {
                  setFormData(prev => ({ ...prev, sector: newInputValue }));
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Sector"
                    placeholder="e.g., FMCG, Auto"
                    helperText="Select existing or type new"
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
                helperText={editingStock ? "Auto-updates on Refresh Prices" : "Auto-fetches from symbol"}
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
                      fontWeight: 'bold'
                    }}
                  />
                </Box>
              )}
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={fetchingDetails}>
                <InputLabel>Status</InputLabel>
                <Select
                  name="status"
                  value={formData.status}
                  label="Status"
                  onChange={handleInputChange}
                >
                  <MenuItem value="WATCHING">Watching</MenuItem>
                  <MenuItem value="HOLD">Holding</MenuItem>
                </Select>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, ml: 1.5 }}>
                  {!editingStock && "Auto-set: WATCHING (not in portfolio) or HOLDING (in portfolio)"}
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
          <Button onClick={handleCloseDialog} sx={{ borderRadius: 2 }}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            sx={{ borderRadius: 2, px: 4 }}
          >
            {editingStock ? 'Save' : 'Add Stock'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default StockTracking;
