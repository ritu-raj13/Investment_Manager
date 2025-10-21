import React, { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Container,
  InputAdornment,
  IconButton
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  ShowChart as ShowChartIcon
} from '@mui/icons-material';
import { authAPI } from '../services/api';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authAPI.login(username, password);
      onLogin();
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Invalid credentials. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={24}
          sx={{
            p: 4,
            borderRadius: 2,
            background: '#1e1e1e',
          }}
        >
          {/* Logo/Title */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 3 }}>
            <ShowChartIcon sx={{ fontSize: 40, mr: 1, color: '#90caf9' }} />
            <Typography variant="h4" component="h1" fontWeight="bold">
              Investment Manager
            </Typography>
          </Box>

          <Typography
            variant="body2"
            color="text.secondary"
            align="center"
            gutterBottom
            sx={{ mb: 4 }}
          >
            Portfolio tracking and analytics for Indian equities
          </Typography>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              margin="normal"
              required
              autoFocus
              disabled={loading}
              autoComplete="username"
            />

            <TextField
              fullWidth
              type={showPassword ? 'text' : 'password'}
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              required
              disabled={loading}
              autoComplete="current-password"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      disabled={loading}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Button
              fullWidth
              variant="contained"
              type="submit"
              size="large"
              disabled={loading}
              sx={{
                mt: 3,
                mb: 2,
                height: 48,
                fontSize: '1rem',
                textTransform: 'none',
                fontWeight: 'bold'
              }}
            >
              {loading ? <CircularProgress size={24} /> : 'Sign In'}
            </Button>
          </form>

          {/* Footer */}
          <Typography
            variant="caption"
            color="text.secondary"
            align="center"
            display="block"
            sx={{ mt: 3 }}
          >
            Single-user access • Secure & Private
          </Typography>
        </Paper>

        {/* Info Box */}
        <Paper
          sx={{
            mt: 2,
            p: 2,
            background: 'rgba(30, 30, 30, 0.5)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <Typography variant="caption" color="text.secondary" display="block" align="center">
            💡 First time? Use the credentials you set during deployment
          </Typography>
        </Paper>
      </Container>
    </Box>
  );
}

export default Login;

