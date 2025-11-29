import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
} from '@mui/material';
import StockTracking from './StockTracking';
import Portfolio from './Portfolio';
import Analytics from './Analytics';
import Recommendations from './Recommendations';

function Equity() {
  const [currentTab, setCurrentTab] = useState(0);

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 'bold' }}>
        Stocks
      </Typography>

      {/* Sub-Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, val) => setCurrentTab(val)}>
          <Tab label="Stock Tracking" />
          <Tab label="Holdings" />
          <Tab label="Transactions" />
          <Tab label="Analytics" />
          <Tab label="Recommendations" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {currentTab === 0 && <StockTracking />}
      {currentTab === 1 && <PortfolioHoldings />}
      {currentTab === 2 && <PortfolioTransactions />}
      {currentTab === 3 && <Analytics />}
      {currentTab === 4 && <Recommendations />}
    </Box>
  );
}

// Wrapper to show only Holdings tab from Portfolio
function PortfolioHoldings() {
  return (
    <Box>
      <Portfolio initialTab={0} />
    </Box>
  );
}

// Wrapper to show only Transactions tab from Portfolio
function PortfolioTransactions() {
  return (
    <Box>
      <Portfolio initialTab={1} />
    </Box>
  );
}

export default Equity;

