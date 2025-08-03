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
  Card,
  CardContent,
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Event as EventIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { listingsAPI, agentsAPI } from '../services/api';

const Listings = () => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({
    status: 'Active',
  });
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newListing, setNewListing] = useState({
    mls_number: '',
    address: '',
    city: '',
    state: 'CA',
    zip_code: '',
    price: '',
    bedrooms: '',
    bathrooms: '',
    square_feet: '',
    property_type: 'Single Family',
    listing_agent_id: '',
  });

  const { data: listings, isLoading } = useQuery(
    ['listings', filters],
    () => listingsAPI.getAll(filters),
    {
      select: (response) => response.data,
    }
  );

  const { data: agents } = useQuery(
    'agents',
    () => agentsAPI.getAll({ active_only: true }),
    {
      select: (response) => response.data,
    }
  );

  const { data: listingStats } = useQuery(
    'listingStats',
    listingsAPI.getStats,
    {
      select: (response) => response.data,
    }
  );

  const createMutation = useMutation(listingsAPI.create, {
    onSuccess: () => {
      queryClient.invalidateQueries('listings');
      queryClient.invalidateQueries('listingStats');
      setCreateDialogOpen(false);
      setNewListing({
        mls_number: '',
        address: '',
        city: '',
        state: 'CA',
        zip_code: '',
        price: '',
        bedrooms: '',
        bathrooms: '',
        square_feet: '',
        property_type: 'Single Family',
        listing_agent_id: '',
      });
    },
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'Active': return 'success';
      case 'Pending': return 'warning';
      case 'Sold': return 'info';
      case 'Expired': return 'error';
      default: return 'default';
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const handleCreateListing = () => {
    if (newListing.mls_number && newListing.address && newListing.price && newListing.listing_agent_id) {
      const listingData = {
        ...newListing,
        price: parseFloat(newListing.price),
        bedrooms: parseInt(newListing.bedrooms) || null,
        bathrooms: parseFloat(newListing.bathrooms) || null,
        square_feet: parseInt(newListing.square_feet) || null,
        listing_agent_id: parseInt(newListing.listing_agent_id),
      };
      createMutation.mutate(listingData);
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
    <Container maxWidth="xl">
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Typography variant="h4">
          🏢 Listings
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Add Listing
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Listings
              </Typography>
              <Typography variant="h5">
                {listingStats?.total_listings || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Listings
              </Typography>
              <Typography variant="h5">
                {listingStats?.active_listings || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Sold This Month
              </Typography>
              <Typography variant="h5">
                {listingStats?.sold_listings || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Average Price
              </Typography>
              <Typography variant="h5">
                {listingStats?.average_price ? formatPrice(listingStats.average_price) : '$0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status || ''}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                label="Status"
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="Active">Active</MenuItem>
                <MenuItem value="Pending">Pending</MenuItem>
                <MenuItem value="Sold">Sold</MenuItem>
                <MenuItem value="Expired">Expired</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="City"
              onChange={(e) => handleFilterChange('city', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Min Price"
              type="number"
              onChange={(e) => handleFilterChange('min_price', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Max Price"
              type="number"
              onChange={(e) => handleFilterChange('max_price', e.target.value)}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Listings Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Property</TableCell>
              <TableCell>Price</TableCell>
              <TableCell>Details</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Listing Agent</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {listings?.map((listing) => (
              <TableRow key={listing.id}>
                <TableCell>
                  <Box>
                    <Typography variant="body1" fontWeight="bold">
                      {listing.address}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {listing.city}, {listing.state} {listing.zip_code}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      MLS: {listing.mls_number}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="h6" color="primary">
                    {formatPrice(listing.price)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2">
                      {listing.bedrooms || '?'} bed • {listing.bathrooms || '?'} bath
                    </Typography>
                    <Typography variant="body2">
                      {listing.square_feet ? `${listing.square_feet.toLocaleString()} sq ft` : 'Size N/A'}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {listing.property_type}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={listing.status}
                    color={getStatusColor(listing.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {listing.listing_agent?.name || 'Not assigned'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Button
                      size="small"
                      startIcon={<ViewIcon />}
                    >
                      View
                    </Button>
                    <Button
                      size="small"
                      startIcon={<EventIcon />}
                      color="secondary"
                    >
                      Schedule
                    </Button>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Listing Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Listing</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="MLS Number"
                value={newListing.mls_number}
                onChange={(e) => setNewListing(prev => ({ ...prev, mls_number: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Listing Agent</InputLabel>
                <Select
                  value={newListing.listing_agent_id}
                  onChange={(e) => setNewListing(prev => ({ ...prev, listing_agent_id: e.target.value }))}
                  label="Listing Agent"
                >
                  {agents?.map((agent) => (
                    <MenuItem key={agent.id} value={agent.id}>
                      {agent.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Address"
                value={newListing.address}
                onChange={(e) => setNewListing(prev => ({ ...prev, address: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="City"
                value={newListing.city}
                onChange={(e) => setNewListing(prev => ({ ...prev, city: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="State"
                value={newListing.state}
                onChange={(e) => setNewListing(prev => ({ ...prev, state: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="ZIP Code"
                value={newListing.zip_code}
                onChange={(e) => setNewListing(prev => ({ ...prev, zip_code: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Price"
                type="number"
                value={newListing.price}
                onChange={(e) => setNewListing(prev => ({ ...prev, price: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Property Type</InputLabel>
                <Select
                  value={newListing.property_type}
                  onChange={(e) => setNewListing(prev => ({ ...prev, property_type: e.target.value }))}
                  label="Property Type"
                >
                  <MenuItem value="Single Family">Single Family</MenuItem>
                  <MenuItem value="Condo">Condo</MenuItem>
                  <MenuItem value="Townhouse">Townhouse</MenuItem>
                  <MenuItem value="Multi Family">Multi Family</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Bedrooms"
                type="number"
                value={newListing.bedrooms}
                onChange={(e) => setNewListing(prev => ({ ...prev, bedrooms: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Bathrooms"
                type="number"
                step="0.5"
                value={newListing.bathrooms}
                onChange={(e) => setNewListing(prev => ({ ...prev, bathrooms: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Square Feet"
                type="number"
                value={newListing.square_feet}
                onChange={(e) => setNewListing(prev => ({ ...prev, square_feet: e.target.value }))}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateListing}
            variant="contained"
            disabled={createMutation.isLoading}
          >
            {createMutation.isLoading ? <CircularProgress size={20} /> : 'Add Listing'}
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
  );
};

export default Listings;
