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
  Tabs,
  Tab,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import UploadIcon from '@mui/icons-material/Upload';
import BackupIcon from '@mui/icons-material/Backup';
import RestoreIcon from '@mui/icons-material/Restore';
import StorageIcon from '@mui/icons-material/Storage';
import DescriptionIcon from '@mui/icons-material/Description';
import SettingsIcon from '@mui/icons-material/Settings';
import SaveIcon from '@mui/icons-material/Save';
import RefreshIcon from '@mui/icons-material/Refresh';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import SecurityIcon from '@mui/icons-material/Security';
import { dataAPI, portfolioAPI, globalSettingsAPI } from '../services/api';

const Settings = () => {
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [loading, setLoading] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null, file: null });
  const [currentTab, setCurrentTab] = useState(0);
  
  // Stock Portfolio Settings
  const [config, setConfig] = useState({
    projected_portfolio_amount: 0,
    target_date: '',
    // Per-stock limits
    max_large_cap_pct: 5.0,
    max_mid_cap_pct: 3.0,
    max_small_cap_pct: 2.5,
    max_micro_cap_pct: 2.0,
    // Stock count limits per market cap
    max_large_cap_stocks: 15,
    max_mid_cap_stocks: 8,
    max_small_cap_stocks: 7,
    max_micro_cap_stocks: 3,
    // Portfolio % limits per market cap
    max_large_cap_portfolio_pct: 50,
    max_mid_cap_portfolio_pct: 30,
    max_small_cap_portfolio_pct: 25,
    max_micro_cap_portfolio_pct: 10,
    // Overall limits
    max_stocks_per_sector: 2,
    max_total_stocks: 30,
    // Screener MC cutoffs (Rs. Cr) — fetch from Screener on Stock Portfolio tab
    mc_threshold_rank_100: '',
    mc_threshold_rank_250: '',
    mc_threshold_rank_500: '',
    mc_thresholds_updated_at: '',
  });
  const [configLoading, setConfigLoading] = useState(false);
  const [mcThresholdsLoading, setMcThresholdsLoading] = useState(false);
  
  // Global Settings (Phase 3)
  const [globalSettings, setGlobalSettings] = useState({
    max_equity_allocation_pct: 70.0,
    max_debt_allocation_pct: 30.0,
    min_emergency_fund_months: 6,
    monthly_income_target: 0.0,
    monthly_expense_target: 0.0,
    currency: 'INR',
  });
  const [globalSettingsLoading, setGlobalSettingsLoading] = useState(false);

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Load configuration on mount
  useEffect(() => {
    loadConfiguration();
    loadGlobalSettings();
  }, []);

  const loadConfiguration = async () => {
    try {
      setConfigLoading(true);
      const response = await portfolioAPI.getSettings();
      setConfig({
        projected_portfolio_amount: response.data.projected_portfolio_amount || 0,
        target_date: response.data.target_date || '',
        // Per-stock limits
        max_large_cap_pct: response.data.max_large_cap_pct || 5.0,
        max_mid_cap_pct: response.data.max_mid_cap_pct || 3.0,
        max_small_cap_pct: response.data.max_small_cap_pct || 2.5,
        max_micro_cap_pct: response.data.max_micro_cap_pct || 2.0,
        // Stock count limits per market cap
        max_large_cap_stocks: response.data.max_large_cap_stocks || 15,
        max_mid_cap_stocks: response.data.max_mid_cap_stocks || 8,
        max_small_cap_stocks: response.data.max_small_cap_stocks || 7,
        max_micro_cap_stocks: response.data.max_micro_cap_stocks || 3,
        // Portfolio % limits per market cap
        max_large_cap_portfolio_pct: response.data.max_large_cap_portfolio_pct || 50,
        max_mid_cap_portfolio_pct: response.data.max_mid_cap_portfolio_pct || 30,
        max_small_cap_portfolio_pct: response.data.max_small_cap_portfolio_pct || 25,
        max_micro_cap_portfolio_pct: response.data.max_micro_cap_portfolio_pct || 10,
        // Overall limits
        max_stocks_per_sector: response.data.max_stocks_per_sector || 2,
        max_total_stocks: response.data.max_total_stocks || 30,
        mc_threshold_rank_100:
          response.data.mc_threshold_rank_100 != null ? response.data.mc_threshold_rank_100 : '',
        mc_threshold_rank_250:
          response.data.mc_threshold_rank_250 != null ? response.data.mc_threshold_rank_250 : '',
        mc_threshold_rank_500:
          response.data.mc_threshold_rank_500 != null ? response.data.mc_threshold_rank_500 : '',
        mc_thresholds_updated_at: response.data.mc_thresholds_updated_at || '',
      });
    } catch (error) {
      showSnackbar('Failed to load configuration', 'error');
    } finally {
      setConfigLoading(false);
    }
  };

  const loadGlobalSettings = async () => {
    try {
      setGlobalSettingsLoading(true);
      const response = await globalSettingsAPI.get();
      setGlobalSettings({
        max_equity_allocation_pct: response.data.max_equity_allocation_pct || 70.0,
        max_debt_allocation_pct: response.data.max_debt_allocation_pct || 30.0,
        min_emergency_fund_months: response.data.min_emergency_fund_months || 6,
        monthly_income_target: response.data.monthly_income_target || 0.0,
        monthly_expense_target: response.data.monthly_expense_target || 0.0,
        currency: response.data.currency || 'INR',
      });
    } catch (error) {
      showSnackbar('Failed to load global settings', 'error');
    } finally {
      setGlobalSettingsLoading(false);
    }
  };

  const handleConfigChange = (field, value) => {
    setConfig((prev) => ({ ...prev, [field]: parseFloat(value) || 0 }));
  };

  const handleGlobalSettingsChange = (field, value) => {
    setGlobalSettings((prev) => ({ ...prev, [field]: value }));
  };

  const handleFetchMcThresholds = async () => {
    try {
      setMcThresholdsLoading(true);
      const response = await portfolioAPI.refreshMcThresholds();
      showSnackbar(response.data?.message || 'Market cap thresholds updated from Screener', 'success');
      await loadConfiguration();
    } catch (error) {
      showSnackbar(error.response?.data?.error || 'Failed to fetch market cap thresholds', 'error');
    } finally {
      setMcThresholdsLoading(false);
    }
  };

  const handleSaveConfiguration = async () => {
    try {
      setConfigLoading(true);
      const numOrNull = (v) => {
        if (v === '' || v == null) return null;
        const n = parseFloat(v);
        return Number.isFinite(n) ? n : null;
      };
      const payload = {
        ...config,
        mc_threshold_rank_100: numOrNull(config.mc_threshold_rank_100),
        mc_threshold_rank_250: numOrNull(config.mc_threshold_rank_250),
        mc_threshold_rank_500: numOrNull(config.mc_threshold_rank_500),
      };
      await portfolioAPI.updateSettings(payload);
      showSnackbar('Configuration saved successfully!', 'success');
      // Reload to reflect changes
      setTimeout(() => window.location.reload(), 1500);
    } catch (error) {
      showSnackbar('Failed to save configuration', 'error');
    } finally {
      setConfigLoading(false);
    }
  };

  const handleSaveGlobalSettings = async () => {
    try {
      setGlobalSettingsLoading(true);
      await globalSettingsAPI.update(globalSettings);
      showSnackbar('Global settings saved successfully!', 'success');
    } catch (error) {
      showSnackbar('Failed to save global settings', 'error');
    } finally {
      setGlobalSettingsLoading(false);
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
          Configure portfolio thresholds, global settings, and manage your data
        </Typography>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3, borderRadius: 3 }}>
        <Tabs 
          value={currentTab} 
          onChange={(e, newValue) => setCurrentTab(newValue)}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Global Settings" icon={<AccountBalanceIcon />} iconPosition="start" />
          <Tab label="Stock Portfolio" icon={<SettingsIcon />} iconPosition="start" />
          <Tab label="Data Management" icon={<StorageIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Tab 0: Global Settings (Phase 3) */}
      {currentTab === 0 && (
        <Paper sx={{ p: 3, mb: 4, borderRadius: 3, bgcolor: 'rgba(96, 165, 250, 0.05)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <AccountBalanceIcon sx={{ mr: 1, fontSize: 28, color: 'primary.main' }} />
            <Typography variant="h5" fontWeight="bold">
              Global Settings
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Configure portfolio-wide targets, emergency fund, and financial goals
          </Typography>

          {globalSettingsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={3}>
              {/* Asset Allocation Targets */}
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Asset Allocation Targets (Across All Investments)
                  </Typography>
                </Divider>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Maximum Equity Allocation"
                  type="number"
                  value={globalSettings.max_equity_allocation_pct}
                  onChange={(e) => handleGlobalSettingsChange('max_equity_allocation_pct', parseFloat(e.target.value) || 0)}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">%</InputAdornment>,
                  }}
                  inputProps={{ min: 0, max: 100, step: 1 }}
                  helperText="Target % of total net worth in equity (stocks + equity MF)"
                  sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Maximum Debt Allocation"
                  type="number"
                  value={globalSettings.max_debt_allocation_pct}
                  onChange={(e) => handleGlobalSettingsChange('max_debt_allocation_pct', parseFloat(e.target.value) || 0)}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">%</InputAdornment>,
                  }}
                  inputProps={{ min: 0, max: 100, step: 1 }}
                  helperText="Target % of total net worth in debt (FD + debt MF + bonds)"
                  sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
                />
              </Grid>

              {/* Emergency Fund */}
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Emergency Fund Settings
                  </Typography>
                </Divider>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Emergency Fund Target (Months)"
                  type="number"
                  value={globalSettings.min_emergency_fund_months}
                  onChange={(e) => handleGlobalSettingsChange('min_emergency_fund_months', parseInt(e.target.value) || 0)}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">Months</InputAdornment>,
                    startAdornment: <InputAdornment position="start"><SecurityIcon /></InputAdornment>,
                  }}
                  inputProps={{ min: 1, max: 24, step: 1 }}
                  helperText="Recommended: 6-12 months of expenses"
                  sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
                />
              </Grid>

              {/* Budget Targets */}
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Monthly Budget Targets
                  </Typography>
                </Divider>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Monthly Income Target"
                  type="number"
                  value={globalSettings.monthly_income_target}
                  onChange={(e) => handleGlobalSettingsChange('monthly_income_target', parseFloat(e.target.value) || 0)}
                  InputProps={{
                    startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                  }}
                  helperText="Target monthly income (used for savings rate)"
                  sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Monthly Expense Target"
                  type="number"
                  value={globalSettings.monthly_expense_target}
                  onChange={(e) => handleGlobalSettingsChange('monthly_expense_target', parseFloat(e.target.value) || 0)}
                  InputProps={{
                    startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                  }}
                  helperText="Target monthly expenses (used for emergency fund)"
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
                  onClick={handleSaveGlobalSettings}
                  disabled={globalSettingsLoading}
                  sx={{ mt: 2 }}
                >
                  Save Global Settings
                </Button>
              </Grid>
            </Grid>
          )}
        </Paper>
      )}

      {/* Tab 1: Stock Portfolio Configuration */}
      {currentTab === 1 && (
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
            {/* Projected Portfolio Amount */}
            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                label="Projected Portfolio Amount"
                type="number"
                value={config.projected_portfolio_amount}
                onChange={(e) => handleConfigChange('projected_portfolio_amount', e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
                helperText="Target portfolio amount for percentage calculations (not current invested)"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            {/* Target Date */}
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Target Date"
                type="date"
                value={config.target_date}
                onChange={(e) => setConfig(prev => ({ ...prev, target_date: e.target.value }))}
                InputLabelProps={{
                  shrink: true,
                }}
                helperText="Target date for projected amount"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12}>
              <Alert severity="info" sx={{ bgcolor: 'rgba(255,255,255,0.08)' }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  Market cap tier cutoffs (Rs. Cr)
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Use <strong>Fetch MC Thresholds</strong> below to load the 100th, 250th, and 500th company market caps
                  from Screener (sorted by market cap). Large / Mid / Small / Micro are assigned by comparing each
                  stock&apos;s market cap to these values. You can edit the numbers manually if needed.
                </Typography>
                {config.mc_thresholds_updated_at && (
                  <Typography variant="caption" display="block" sx={{ opacity: 0.9 }}>
                    Last updated from Screener: {new Date(config.mc_thresholds_updated_at).toLocaleString()}
                  </Typography>
                )}
              </Alert>
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="outlined"
                color="secondary"
                startIcon={<RefreshIcon />}
                onClick={handleFetchMcThresholds}
                disabled={mcThresholdsLoading || configLoading}
                sx={{ borderRadius: 2 }}
              >
                {mcThresholdsLoading ? 'Fetching…' : 'Fetch MC Thresholds'}
              </Button>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="100th stock MC (Cr)"
                type="number"
                value={config.mc_threshold_rank_100}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, mc_threshold_rank_100: e.target.value }))
                }
                inputProps={{ min: 0, step: 0.01 }}
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="250th stock MC (Cr)"
                type="number"
                value={config.mc_threshold_rank_250}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, mc_threshold_rank_250: e.target.value }))
                }
                inputProps={{ min: 0, step: 0.01 }}
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="500th stock MC (Cr)"
                type="number"
                value={config.mc_threshold_rank_500}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, mc_threshold_rank_500: e.target.value }))
                }
                inputProps={{ min: 0, step: 0.01 }}
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
                label="Large Cap Max % (Display: 5.5%)"
                type="number"
                value={config.max_large_cap_pct}
                onChange={(e) => handleConfigChange('max_large_cap_pct', e.target.value)}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 0.5 }}
                helperText="Actual max: 5%, with 0.5% leverage shown as 5.5%"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Mid Cap Max % (Display: 3.5%)"
                type="number"
                value={config.max_mid_cap_pct}
                onChange={(e) => handleConfigChange('max_mid_cap_pct', e.target.value)}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 0.5 }}
                helperText="Actual max: 3%, with 0.5% leverage shown as 3.5%"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Small Cap Max % (Display: 3%)"
                type="number"
                value={config.max_small_cap_pct}
                onChange={(e) => handleConfigChange('max_small_cap_pct', e.target.value)}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 0.5 }}
                helperText="Actual max: 2.5%, with 0.5% leverage shown as 3%"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Micro Cap Max % (Display: 2.5%)"
                type="number"
                value={config.max_micro_cap_pct}
                onChange={(e) => handleConfigChange('max_micro_cap_pct', e.target.value)}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 0.5 }}
                helperText="Actual max: 2%, with 0.5% leverage shown as 2.5%"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Stock Count Limits per Market Cap
                </Typography>
              </Divider>
            </Grid>

            {/* Stock Count Limits */}
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Max Large Cap Stocks"
                type="number"
                value={config.max_large_cap_stocks}
                onChange={(e) => setConfig(prev => ({ ...prev, max_large_cap_stocks: parseInt(e.target.value) || 15 }))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">stocks</InputAdornment>,
                }}
                inputProps={{ min: 1, max: 50, step: 1 }}
                helperText="Max number of Large Cap stocks"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Max Mid Cap Stocks"
                type="number"
                value={config.max_mid_cap_stocks}
                onChange={(e) => setConfig(prev => ({ ...prev, max_mid_cap_stocks: parseInt(e.target.value) || 8 }))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">stocks</InputAdornment>,
                }}
                inputProps={{ min: 1, max: 50, step: 1 }}
                helperText="Max number of Mid Cap stocks"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Max Small Cap Stocks"
                type="number"
                value={config.max_small_cap_stocks}
                onChange={(e) => setConfig(prev => ({ ...prev, max_small_cap_stocks: parseInt(e.target.value) || 7 }))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">stocks</InputAdornment>,
                }}
                inputProps={{ min: 1, max: 50, step: 1 }}
                helperText="Max number of Small Cap stocks"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Max Micro Cap Stocks"
                type="number"
                value={config.max_micro_cap_stocks}
                onChange={(e) => setConfig(prev => ({ ...prev, max_micro_cap_stocks: parseInt(e.target.value) || 3 }))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">stocks</InputAdornment>,
                }}
                inputProps={{ min: 1, max: 50, step: 1 }}
                helperText="Max number of Micro Cap stocks"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Portfolio % Limits per Market Cap
                </Typography>
              </Divider>
            </Grid>

            {/* Portfolio % Limits */}
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Max Large Cap Portfolio %"
                type="number"
                value={config.max_large_cap_portfolio_pct}
                onChange={(e) => setConfig(prev => ({ ...prev, max_large_cap_portfolio_pct: parseFloat(e.target.value) || 50 }))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 1 }}
                helperText="Max total % of portfolio in Large Cap"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Max Mid Cap Portfolio %"
                type="number"
                value={config.max_mid_cap_portfolio_pct}
                onChange={(e) => setConfig(prev => ({ ...prev, max_mid_cap_portfolio_pct: parseFloat(e.target.value) || 30 }))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 1 }}
                helperText="Max total % of portfolio in Mid Cap"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Max Small Cap Portfolio %"
                type="number"
                value={config.max_small_cap_portfolio_pct}
                onChange={(e) => setConfig(prev => ({ ...prev, max_small_cap_portfolio_pct: parseFloat(e.target.value) || 25 }))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 1 }}
                helperText="Max total % of portfolio in Small Cap"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Max Micro Cap Portfolio %"
                type="number"
                value={config.max_micro_cap_portfolio_pct}
                onChange={(e) => setConfig(prev => ({ ...prev, max_micro_cap_portfolio_pct: parseFloat(e.target.value) || 10 }))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                inputProps={{ min: 0, max: 100, step: 1 }}
                helperText="Max total % of portfolio in Micro Cap"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Overall Portfolio Limits
                </Typography>
              </Divider>
            </Grid>

            {/* Overall Limits */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Max Stocks per Parent Sector"
                type="number"
                value={config.max_stocks_per_sector}
                onChange={(e) => setConfig(prev => ({ ...prev, max_stocks_per_sector: parseInt(e.target.value) || 2 }))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">stocks</InputAdornment>,
                }}
                inputProps={{ min: 1, max: 10, step: 1 }}
                helperText="Maximum number of stocks allowed in any single parent sector (e.g., Auto, IT, Pharma)"
                sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Max Total Stocks in Portfolio"
                type="number"
                value={config.max_total_stocks}
                onChange={(e) => setConfig(prev => ({ ...prev, max_total_stocks: parseInt(e.target.value) || 30 }))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">stocks</InputAdornment>,
                }}
                inputProps={{ min: 1, max: 100, step: 1 }}
                helperText="Maximum total number of stocks in entire portfolio"
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
      )}

      {/* Tab 2: Data Management */}
      {currentTab === 2 && (
      <Box>
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
      </Box>
      )}

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

