import React, { useEffect, useState } from 'react';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { recommendationsAPI } from '../services/api';

const RebalancingRecommendations = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchRebalancing();
  }, []);

  const fetchRebalancing = async () => {
    try {
      setLoading(true);
      const response = await recommendationsAPI.getRebalancing();
      setData(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load rebalancing recommendations.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => `Rs.${Number(value || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;

  const actions = data?.actionable_recommendations || [];
  const topActions = actions.slice(0, 3);

  const severityColor = (severity) => {
    if (severity === 'critical') return 'error';
    if (severity === 'high') return 'warning';
    if (severity === 'low') return 'success';
    return 'info';
  };

  const getActionSignal = (action) => {
    const d = action?.details || {};
    if (action?.action_type === 'UNDER_ALLOCATED_STOCK') {
      if (d.in_buy_zone) return { label: 'In Buy Zone', color: 'success' };
      if (d.near_buy_zone) return { label: 'Near Buy Zone', color: 'info' };
      return { label: 'No Buy Signal', color: 'default' };
    }
    if (action?.action_type === 'OVER_ALLOCATED_STOCK') {
      if (d.in_sell_zone && d.in_profit) return { label: 'Sell Zone + Profit', color: 'error' };
      if (d.in_sell_zone) return { label: 'In Sell Zone', color: 'error' };
      if (d.near_sell_zone) return { label: 'Near Sell Zone', color: 'warning' };
      if (d.in_profit) return { label: 'In Profit', color: 'success' };
      return { label: 'No Sell Signal', color: 'default' };
    }
    return { label: '-', color: 'default' };
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) return <Alert severity="error">{error}</Alert>;

  const summary = data?.summary_metrics || {};

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Rebalancing Recommendations
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
        Prioritized by capital impact first. Focus on the top actions before adding new exposure.
      </Typography>

      <Grid container spacing={2} sx={{ mb: 2.5 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Total Actions</Typography>
              <Typography variant="h5" fontWeight="bold">{summary.total_actions || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Critical</Typography>
              <Typography variant="h5" fontWeight="bold" color="error.main">{summary.critical_actions || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">High Priority</Typography>
              <Typography variant="h5" fontWeight="bold" color="warning.main">{summary.high_actions || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Capital At Risk</Typography>
              <Typography variant="h6" fontWeight="bold">{formatCurrency(summary.capital_at_risk_inr || 0)}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 2.5, mb: 2.5, borderRadius: 3 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 1.5 }}>
          What needs attention now
        </Typography>
        {topActions.length === 0 ? (
          <Alert severity="success">No threshold breaches right now. Portfolio is within configured limits.</Alert>
        ) : (
          <Grid container spacing={2}>
            {topActions.map((action) => (
              <Grid item xs={12} md={4} key={action.id}>
                <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid rgba(148,163,184,0.2)', height: '100%' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Chip size="small" label={`#${action.priority_rank}`} sx={{ mr: 1 }} />
                    <Chip size="small" label={action.severity} color={severityColor(action.severity)} />
                  </Box>
                  <Typography variant="subtitle1" fontWeight="bold">{action.title}</Typography>
                  <Box sx={{ mt: 0.75 }}>
                    <Chip size="small" label={getActionSignal(action).label} color={getActionSignal(action).color} />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.75 }}>{action.why}</Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Impact: <strong>{formatCurrency(action.impact_amount_inr)}</strong>
                    {action.impact_pct != null ? ` (${Number(action.impact_pct).toFixed(2)}%)` : ''}
                  </Typography>
                  <Alert severity={severityColor(action.severity)} sx={{ mt: 1.25 }}>
                    {action.how_to_apply}
                  </Alert>
                </Paper>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography fontWeight="bold">All Actionable Recommendations ({actions.length})</Typography>
        </AccordionSummary>
        <AccordionDetails>
          {actions.length === 0 ? (
            <Typography color="text.secondary">No actionable recommendations available.</Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Priority</TableCell>
                    <TableCell>Recommendation</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Signal</TableCell>
                    <TableCell align="right">Impact (Rs.)</TableCell>
                    <TableCell align="right">Impact %</TableCell>
                    <TableCell>How to apply</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {actions.map((action) => (
                    <TableRow key={action.id} hover>
                      <TableCell>#{action.priority_rank}</TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">{action.title}</Typography>
                        <Typography variant="caption" color="text.secondary">{action.why}</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip size="small" label={action.severity} color={severityColor(action.severity)} />
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={getActionSignal(action).label}
                          color={getActionSignal(action).color}
                        />
                      </TableCell>
                      <TableCell align="right">{formatCurrency(action.impact_amount_inr)}</TableCell>
                      <TableCell align="right">
                        {action.impact_pct != null ? `${Number(action.impact_pct).toFixed(2)}%` : '-'}
                      </TableCell>
                      <TableCell>{action.how_to_apply}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </AccordionDetails>
      </Accordion>

      <Accordion sx={{ mt: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography fontWeight="bold">Supporting Insights</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
                  Stocks to Reduce ({data?.stocks_to_reduce?.length || 0})
                </Typography>
                {(data?.stocks_to_reduce || []).slice(0, 8).map((row) => (
                  <Typography key={row.symbol} variant="body2" color="text.secondary">
                    {row.symbol.replace('.NS', '').replace('.BO', '')}: {formatCurrency(row.reduce_amount)}
                  </Typography>
                ))}
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
                  Stocks to Add ({data?.stocks_to_add?.length || 0})
                </Typography>
                {(data?.stocks_to_add || []).slice(0, 8).map((row) => (
                  <Typography key={row.symbol} variant="body2" color="text.secondary">
                    {row.symbol.replace('.NS', '').replace('.BO', '')}: {formatCurrency(row.add_amount)}
                    {row.in_buy_zone ? ' (Buy zone)' : ''}
                  </Typography>
                ))}
              </Paper>
            </Grid>
          </Grid>

          {(summary.total_actions || 0) > 0 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <WarningAmberIcon sx={{ mr: 1 }} />
                Apply actions in priority order to minimize drift against your configured portfolio limits.
              </Box>
            </Alert>
          )}
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default RebalancingRecommendations;
