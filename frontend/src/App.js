import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { 
  Box, 
  AppBar, 
  Toolbar, 
  Typography, 
  Tabs, 
  Tab, 
  Container, 
  Fab, 
  Zoom,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import DashboardIcon from '@mui/icons-material/Dashboard';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import AccountBoxIcon from '@mui/icons-material/AccountBox';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import AssessmentIcon from '@mui/icons-material/Assessment';
import FavoriteIcon from '@mui/icons-material/Favorite';
import RecommendIcon from '@mui/icons-material/Recommend';
import SettingsIcon from '@mui/icons-material/Settings';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import LogoutIcon from '@mui/icons-material/Logout';
import BarChartIcon from '@mui/icons-material/BarChart';
import TimelineIcon from '@mui/icons-material/Timeline';
import StockTracking from './components/StockTracking';
import Portfolio from './components/Portfolio';
import Analytics from './components/Analytics';
import Health from './components/Health';
import Recommendations from './components/Recommendations';
import Settings from './components/Settings';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import IncomeExpenses from './components/IncomeExpenses';
import MutualFunds from './components/MutualFunds';
import FixedIncome from './components/FixedIncome';
import Accounts from './components/Accounts';
import Reports from './components/Reports';
import Equity from './components/Equity';
import { authAPI } from './services/api';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#60a5fa',
    },
    secondary: {
      main: '#a78bfa',
    },
    success: {
      main: '#4ade80',
    },
    error: {
      main: '#f87171',
    },
    warning: {
      main: '#fbbf24',
    },
    background: {
      default: '#0f172a',
      paper: '#1e293b',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#1e293b',
          borderRadius: 12,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

function App() {
  const [currentTab, setCurrentTab] = useState(0);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [username, setUsername] = useState('');

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  // Check authentication status on mount
  useEffect(() => {
    const checkAuthentication = async () => {
      try {
        const response = await authAPI.checkAuth();
        setIsAuthenticated(true);
        setUsername(response.data.username);
      } catch (error) {
        setIsAuthenticated(false);
      } finally {
        setIsCheckingAuth(false);
      }
    };

    checkAuthentication();
  }, []);

  // Handle successful login
  const handleLogin = () => {
    setIsAuthenticated(true);
    setIsCheckingAuth(false);
  };

  // Handle logout
  const handleLogout = async () => {
    try {
      await authAPI.logout();
      setIsAuthenticated(false);
      setUsername('');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // Show/hide back to top button based on scroll position
  useEffect(() => {
    const handleScroll = () => {
      if (window.pageYOffset > 300) {
        setShowBackToTop(true);
      } else {
        setShowBackToTop(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  // Show loading spinner while checking authentication
  if (isCheckingAuth) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            bgcolor: 'background.default',
          }}
        >
          <CircularProgress size={60} />
        </Box>
      </ThemeProvider>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Login onLogin={handleLogin} />
      </ThemeProvider>
    );
  }

  // Show main app if authenticated
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: 'background.default', pb: 4 }}>
        <AppBar 
          position="sticky" 
          elevation={4}
          sx={{ 
            top: 0,
            zIndex: (theme) => theme.zIndex.drawer + 1,
            backdropFilter: 'blur(10px)',
            bgcolor: 'rgba(30, 41, 59, 0.95)'
          }}
        >
          <Toolbar>
            <DashboardIcon sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Personal Finance Manager
            </Typography>
            {username && (
              <Typography variant="body2" sx={{ mr: 2, opacity: 0.8 }}>
                {username}
              </Typography>
            )}
            <Tooltip title="Logout">
              <IconButton color="inherit" onClick={handleLogout}>
                <LogoutIcon />
              </IconButton>
            </Tooltip>
          </Toolbar>
          <Tabs 
            value={currentTab} 
            onChange={handleTabChange} 
            textColor="inherit"
            indicatorColor="secondary"
            sx={{ bgcolor: 'primary.dark' }}
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab 
              icon={<DashboardIcon />} 
              label="Dashboard" 
              iconPosition="start"
            />
            <Tab 
              icon={<ShowChartIcon />} 
              label="Stocks" 
              iconPosition="start"
            />
            <Tab 
              icon={<TrendingUpIcon />} 
              label="Mutual Funds" 
              iconPosition="start"
            />
            <Tab 
              icon={<AccountBalanceIcon />} 
              label="Fixed Income" 
              iconPosition="start"
            />
            <Tab 
              icon={<AccountBoxIcon />} 
              label="Accounts" 
              iconPosition="start"
            />
            <Tab 
              icon={<MonetizationOnIcon />} 
              label="Income & Expenses" 
              iconPosition="start"
            />
            <Tab 
              icon={<AssessmentIcon />} 
              label="Reports"
              iconPosition="start"
            />
            <Tab 
              icon={<FavoriteIcon />} 
              label="Health"
              iconPosition="start"
            />
            <Tab 
              icon={<SettingsIcon />} 
              label="Settings"
              iconPosition="start"
            />
          </Tabs>
        </AppBar>
        
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          {currentTab === 0 && <Dashboard />}
          {currentTab === 1 && <Equity />}
          {currentTab === 2 && <MutualFunds />}
          {currentTab === 3 && <FixedIncome />}
          {currentTab === 4 && <Accounts />}
          {currentTab === 5 && <IncomeExpenses />}
          {currentTab === 6 && <Reports />}
          {currentTab === 7 && <Health />}
          {currentTab === 8 && <Settings />}
        </Container>

        {/* Back to Top Button */}
        <Zoom in={showBackToTop}>
          <Fab
            onClick={scrollToTop}
            color="primary"
            size="medium"
            aria-label="scroll back to top"
            sx={{
              position: 'fixed',
              bottom: 32,
              right: 32,
              zIndex: (theme) => theme.zIndex.speedDial,
              boxShadow: 4,
              '&:hover': {
                transform: 'scale(1.1)',
                boxShadow: 6,
              },
              transition: 'all 0.3s ease-in-out',
            }}
          >
            <KeyboardArrowUpIcon />
          </Fab>
        </Zoom>
      </Box>
    </ThemeProvider>
  );
}

export default App;

