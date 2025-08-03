import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import OpenHouses from './pages/OpenHouses';
import Agents from './pages/Agents';
import Listings from './pages/Listings';
import OpenHouseDetail from './pages/OpenHouseDetail';
import AgentDetail from './pages/AgentDetail';

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/open-houses" element={<OpenHouses />} />
          <Route path="/open-houses/:id" element={<OpenHouseDetail />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/agents/:id" element={<AgentDetail />} />
          <Route path="/listings" element={<Listings />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default App;
