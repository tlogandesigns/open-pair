import React, { useState } from 'react';
import {
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  Box,
  TextField,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Fab,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { openHousesAPI, listingsAPI } from '../services/api';

const OpenHouses = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({
    status: '',
    start_date: null,
    end_date: null,
  });
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newOpenHouse, setNewOpenHouse] = useState({
    listing_id: '',
    scheduled_date: null,
    start_time: null,
    end_time: null,
  });

  const { data: openHouses, isLoading } = useQuery(
    ['openHouses', filters],
    () => openHousesAPI.getAll(filters),
    {
      select: (response) => response.data,
    }
  );

  const { data: listings } = useQuery(
    'listings',
    () => listingsAPI.getAll({ status: 'Active' }),
    {
      select: (response) => response.data,
    }
  );

  const createMutation = useMutation(openHousesAPI.create, {
    onSuccess: () => {
      queryClient.invalidateQueries('openHouses');
      setCreateDialogOpen(false);
      setNewOpenHouse({
        listing_id: '',
        scheduled_date: null,
        start_time: null,
        end_time: null,
      });
    },
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'Scheduled': return 'primary';
      case 'Completed': return 'success';
      case 'Cancelled': return 'error';
      default: return 'default';
    }
  };

  const handleCreateOpenHouse = () => {
    if (newOpenHouse.listing_id && newOpenHouse.start_time && newOpenHouse.end_time) {
      createMutation.mutate({
        listing_id: parseInt(newOpenHouse.listing_id),
        scheduled_date: newOpenHouse.start_time,
        start_time: newOpenHouse.start_time,
        end_time: newOpenHouse.end_time,
      });
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="xl">
        <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
          <Typography variant="h4">
            🏠 Open Houses
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Schedule Open House
          </Button>
        </Box>

        {/* Filters */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  label="Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="Scheduled">Scheduled</MenuItem>
                  <MenuItem value="Completed">Completed</MenuItem>
                  <MenuItem value="Cancelled">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <DateTimePicker
                label="Start Date"
                value={filters.start_date}
                onChange={(date) => handleFilterChange('start_date', date)}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <DateTimePicker
                label="End Date"
                value={filters.end_date}
                onChange={(date) => handleFilterChange('end_date', date)}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                onClick={() => setFilters({ status: '', start_date: null, end_date: null })}
                fullWidth
              >
                Clear Filters
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {/* Open Houses Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Property</TableCell>
                <TableCell>Date & Time</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Host Agent</TableCell>
                <TableCell>Attendees</TableCell>
                <TableCell>Leads</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {openHouses?.map((openHouse) => (
                <TableRow key={openHouse.id}>
                  <TableCell>
                    <Box>
                      <Typography variant="body2" fontWeight="bold">
                        {openHouse.listing?.address || 'Address not available'}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        ${openHouse.listing?.price?.toLocaleString() || 'N/A'}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2">
                        {new Date(openHouse.start_time).toLocaleDateString()}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {new Date(openHouse.start_time).toLocaleTimeString()} - {' '}
                        {new Date(openHouse.end_time).toLocaleTimeString()}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={openHouse.status}
                      color={getStatusColor(openHouse.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {openHouse.host_agent ? (
                      <Typography variant="body2">
                        {openHouse.host_agent.name}
                      </Typography>
                    ) : (
                      <Chip label="Unassigned" color="warning" size="small" />
                    )}
                  </TableCell>
                  <TableCell>{openHouse.attendee_count}</TableCell>
                  <TableCell>{openHouse.leads_generated}</TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Button
                        size="small"
                        startIcon={<ViewIcon />}
                        onClick={() => navigate(`/open-houses/${openHouse.id}`)}
                      >
                        View
                      </Button>
                      {!openHouse.host_agent_id && openHouse.status === 'Scheduled' && (
                        <Button
                          size="small"
                          startIcon={<AssignmentIcon />}
                          color="secondary"
                          onClick={() => navigate(`/open-houses/${openHouse.id}`)}
                        >
                          Assign
                        </Button>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Create Open House Dialog */}
        <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Schedule New Open House</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Listing</InputLabel>
                  <Select
                    value={newOpenHouse.listing_id}
                    onChange={(e) => setNewOpenHouse(prev => ({ ...prev, listing_id: e.target.value }))}
                    label="Listing"
                  >
                    {listings?.map((listing) => (
                      <MenuItem key={listing.id} value={listing.id}>
                        {listing.address} - ${listing.price?.toLocaleString()}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <DateTimePicker
                  label="Start Time"
                  value={newOpenHouse.start_time}
                  onChange={(date) => setNewOpenHouse(prev => ({ ...prev, start_time: date }))}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <DateTimePicker
                  label="End Time"
                  value={newOpenHouse.end_time}
                  onChange={(date) => setNewOpenHouse(prev => ({ ...prev, end_time: date }))}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreateOpenHouse}
              variant="contained"
              disabled={createMutation.isLoading}
            >
              {createMutation.isLoading ? <CircularProgress size={20} /> : 'Schedule'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Floating Action Button for mobile */}
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16, display: { xs: 'flex', sm: 'none' } }}
          onClick={() => setCreateDialogOpen(true)}
        >
          <AddIcon />
        </Fab>
      </Container>
    </LocalizationProvider>
  );
};

export default OpenHouses;
