import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  CircularProgress,
  TextField,
  InputAdornment,
  Divider,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import UploadIcon from '@mui/icons-material/Upload';
import BackupIcon from '@mui/icons-material/Backup';
import RestoreIcon from '@mui/icons-material/Restore';
import StorageIcon from '@mui/icons-material/Storage';
import DescriptionIcon from '@mui/icons-material/Description';
import SettingsIcon from '@mui/icons-material/Settings';
import SaveIcon from '@mui/icons-material/Save';
import { dataAPI, portfolioAPI } from '../services/api';

const Settings = () => {
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [loading, setLoading] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null, file: null });
  const [config, setConfig] = useState({
    total_amount: 0,
    max_large_cap_pct: 50,
    max_mid_cap_pct: 30,
    max_small_cap_pct: 25,
    max_micro_cap_pct: 15,
    max_sector_pct: 20,
  });
  const [configLoading, setConfigLoading] = useState(false);

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Load configuration on mount
  useEffect(() => {
    loadConfiguration();
  }, []);

  const loadConfiguration = async () => {
    try {
      setConfigLoading(true);
      const response = await portfolioAPI.getSettings();
      setConfig({
        total_amount: response.data.total_amount || 0,
        max_large_cap_pct: response.data.max_large_cap_pct || 50,
        max_mid_cap_pct: response.data.max_mid_cap_pct || 30,
        max_small_cap_pct: response.data.max_small_cap_pct || 25,
        max_micro_cap_pct: response.data.max_micro_cap_pct || 15,
        max_sector_pct: response.data.max_sector_pct || 20,
      });
    } catch (error) {
      showSnackbar('Failed to load configuration', 'error');
    } finally {
      setConfigLoading(false);
    }
  };

  const handleConfigChange = (field, value) => {
    setConfig((prev) => ({ ...prev, [field]: parseFloat(value) || 0 }));
  };

  const handleSaveConfiguration = async () => {
    try {
      setConfigLoading(true);
      await portfolioAPI.updateSettings(config);
      showSnackbar('Configuration saved successfully!', 'success');
      // Reload to reflect changes
      setTimeout(() => window.location.reload(), 1500);
    } catch (error) {
      showSnackbar('Failed to save configuration', 'error');
    } finally {
      setConfigLoading(false);
    }
  };

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  // Export functions
  const handleExportStocks = async () => {
    try {
      setLoading(true);
      const response = await dataAPI.exportStocks();
      const filename = `stocks_export_${new Date().toISOString().split('T')[0]}.csv`;
      downloadBlob(response.data, filename);
      showSnackbar('Stocks exported successfully!', 'success');
    } catch (error) {
      showSnackbar(error.response?.data?.error || 'Failed to export stocks', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleExportTransactions = async () => {
    try {
      setLoading(true);
      const response = await dataAPI.exportTransactions();
      const filename = `transactions_export_${new Date().toISOString().split('T')[0]}.csv`;
      downloadBlob(response.data, filename);
      showSnackbar('Transactions exported successfully!', 'success');
    } catch (error) {
      showSnackbar(error.response?.data?.error || 'Failed to export transactions', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleBackupDatabase = async () => {
    try {
      setLoading(true);
      const response = await dataAPI.backupDatabase();
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
      const filename = `investment_manager_backup_${timestamp}.db`;
      downloadBlob(response.data, filename);
      showSnackbar('Database backup created successfully!', 'success');
    } catch (error) {
      showSnackbar(error.response?.data?.error || 'Failed to backup database', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Import functions
  const handleFileSelect = (event, action) => {
    const file = event.target.files[0];
    if (file) {
      setConfirmDialog({
        open: true,
        action,
        file,
      });
    }
    // Reset input
    event.target.value = null;
  };

  const handleConfirmImport = async () => {
    const { action, file } = confirmDialog;
    setConfirmDialog({ open: false, action: null, file: null });

    try {
      setLoading(true);
      let response;

      switch (action) {
        case 'importStocks':
          response = await dataAPI.importStocks(file);
          showSnackbar(response.data.message, 'success');
          break;
        case 'importTransactions':
          response = await dataAPI.importTransactions(file);
          showSnackbar(response.data.message, 'success');
          break;
        case 'restoreDatabase':
          response = await dataAPI.restoreDatabase(file);
          showSnackbar(`${response.data.message} Reloading...`, 'warning');
          // Reload after 2 seconds
          setTimeout(() => {
            window.location.reload();
          }, 2000);
          break;
        default:
          break;
      }
    } catch (error) {
      showSnackbar(error.response?.data?.error || 'Operation failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Configure portfolio thresholds and manage your data
        </Typography>
      </Box>

      {/* Configuration Section */}
      <Paper sx={{ p: 3, mb: 4, borderRadius: 3, bgcolor: 'primary.dark' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <SettingsIcon sx={{ mr: 1, fontSize: 28 }} />
          <Typography variant="h5" fontWeight="bold">
            Portfolio Configuration
          </Typography>
        </Box>

        {configLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={3}>
            {/* Total Portfolio Amount */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Total Portfolio Target Amount"
                type="number"
                value={config.total_amount}
                onChange={(e) => handleConfigChange('total_amount', e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
                helperText="Target total portfolio amount for percentage calculations"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Maximum Allocation % by Market Cap
                </Typography>
              </Divider>
            </Grid>

            {/* Market Cap Allocations */}
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Large Cap Max %"
                type="number"
                value={config.max_large_cap_pct}
                onChange={(e) => handleConfigChange('max_large_cap_pct', e.target.value)}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 1 }}
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Mid Cap Max %"
                type="number"
                value={config.max_mid_cap_pct}
                onChange={(e) => handleConfigChange('max_mid_cap_pct', e.target.value)}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 1 }}
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Small Cap Max %"
                type="number"
                value={config.max_small_cap_pct}
                onChange={(e) => handleConfigChange('max_small_cap_pct', e.target.value)}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 1 }}
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Micro Cap Max %"
                type="number"
                value={config.max_micro_cap_pct}
                onChange={(e) => handleConfigChange('max_micro_cap_pct', e.target.value)}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 1 }}
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Sector Allocation
                </Typography>
              </Divider>
            </Grid>

            {/* Sector Allocation */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Maximum % per Sector"
                type="number"
                value={config.max_sector_pct}
                onChange={(e) => handleConfigChange('max_sector_pct', e.target.value)}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 1 }}
                helperText="Maximum allocation allowed for any single sector"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            {/* Save Button */}
            <Grid item xs={12}>
              <Button
                variant="contained"
                color="success"
                size="large"
                startIcon={<SaveIcon />}
                onClick={handleSaveConfiguration}
                disabled={configLoading}
                sx={{ mt: 2 }}
              >
                Save Configuration
              </Button>
            </Grid>
          </Grid>
        )}
      </Paper>

      {/* Data Management Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight="bold" gutterBottom>
          Data Management
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Import, export, backup, and restore your investment data
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Export Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <DownloadIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" fontWeight="bold">
                Export Data
              </Typography>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Card variant="outlined" sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <DescriptionIcon sx={{ mr: 1, fontSize: 20 }} />
                      <Typography variant="subtitle1" fontWeight="bold">
                        Export Stocks
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Download all tracked stocks as CSV file
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<DownloadIcon />}
                      onClick={handleExportStocks}
                      disabled={loading}
                    >
                      Export Stocks CSV
                    </Button>
                  </CardActions>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Card variant="outlined" sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <DescriptionIcon sx={{ mr: 1, fontSize: 20 }} />
                      <Typography variant="subtitle1" fontWeight="bold">
                        Export Transactions
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Download all portfolio transactions as CSV file
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<DownloadIcon />}
                      onClick={handleExportTransactions}
                      disabled={loading}
                    >
                      Export Transactions CSV
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Import Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <UploadIcon sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="h6" fontWeight="bold">
                Import Data
              </Typography>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Card variant="outlined" sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <DescriptionIcon sx={{ mr: 1, fontSize: 20 }} />
                      <Typography variant="subtitle1" fontWeight="bold">
                        Import Stocks
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Upload CSV file to import stocks (skips duplicates)
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      fullWidth
                      variant="outlined"
                      component="label"
                      startIcon={<UploadIcon />}
                      disabled={loading}
                    >
                      Choose Stocks CSV
                      <input
                        type="file"
                        hidden
                        accept=".csv"
                        onChange={(e) => handleFileSelect(e, 'importStocks')}
                      />
                    </Button>
                  </CardActions>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Card variant="outlined" sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <DescriptionIcon sx={{ mr: 1, fontSize: 20 }} />
                      <Typography variant="subtitle1" fontWeight="bold">
                        Import Transactions
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Upload CSV file to import portfolio transactions
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      fullWidth
                      variant="outlined"
                      component="label"
                      startIcon={<UploadIcon />}
                      disabled={loading}
                    >
                      Choose Transactions CSV
                      <input
                        type="file"
                        hidden
                        accept=".csv"
                        onChange={(e) => handleFileSelect(e, 'importTransactions')}
                      />
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Backup Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 3, bgcolor: 'success.dark' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <BackupIcon sx={{ mr: 1 }} />
              <Typography variant="h6" fontWeight="bold">
                Backup Database
              </Typography>
            </Box>

            <Card variant="outlined" sx={{ borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <StorageIcon sx={{ mr: 1, fontSize: 20 }} />
                  <Typography variant="subtitle1" fontWeight="bold">
                    Complete Backup
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Download complete database backup (.db file)
                  <br />
                  <strong>Includes:</strong> All stocks, transactions, and settings
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  fullWidth
                  variant="contained"
                  color="success"
                  startIcon={<BackupIcon />}
                  onClick={handleBackupDatabase}
                  disabled={loading}
                >
                  Backup Database
                </Button>
              </CardActions>
            </Card>
          </Paper>
        </Grid>

        {/* Restore Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 3, bgcolor: 'error.dark' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <RestoreIcon sx={{ mr: 1 }} />
              <Typography variant="h6" fontWeight="bold">
                Restore Database
              </Typography>
            </Box>

            <Card variant="outlined" sx={{ borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <StorageIcon sx={{ mr: 1, fontSize: 20 }} />
                  <Typography variant="subtitle1" fontWeight="bold">
                    Complete Restore
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Upload database backup file to restore
                </Typography>
                <Typography variant="caption" color="warning.main" sx={{ fontWeight: 'bold' }}>
                  ⚠️ This will replace ALL current data!
                  <br />
                  A backup of current data will be created automatically.
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  fullWidth
                  variant="contained"
                  color="error"
                  component="label"
                  startIcon={<RestoreIcon />}
                  disabled={loading}
                >
                  Choose Database File
                  <input
                    type="file"
                    hidden
                    accept=".db"
                    onChange={(e) => handleFileSelect(e, 'restoreDatabase')}
                  />
                </Button>
              </CardActions>
            </Card>
          </Paper>
        </Grid>
      </Grid>

      {/* Loading Overlay */}
      {loading && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'rgba(0,0,0,0.5)',
            zIndex: 9999,
          }}
        >
          <CircularProgress />
        </Box>
      )}

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ open: false, action: null, file: null })}>
        <DialogTitle>Confirm Action</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {confirmDialog.action === 'restoreDatabase'
              ? 'Are you sure you want to restore the database? This will replace ALL your current data. A backup of current data will be created automatically.'
              : confirmDialog.action === 'importStocks'
              ? 'Import stocks from CSV? Duplicate symbols will be skipped.'
              : 'Import transactions from CSV? This will add new transactions to your portfolio.'}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, action: null, file: null })}>Cancel</Button>
          <Button onClick={handleConfirmImport} variant="contained" color={confirmDialog.action === 'restoreDatabase' ? 'error' : 'primary'}>
            Confirm
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar open={snackbar.open} autoHideDuration={6000} onClose={handleCloseSnackbar}>
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;

