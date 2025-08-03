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
  Edit as EditIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { agentsAPI } from '../services/api';

const Agents = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({
    active_only: true,
  });
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newAgent, setNewAgent] = useState({
    name: '',
    email: '',
    phone: '',
    license_number: '',
    experience_years: 0,
    areas_of_expertise: [],
    buyer_price_ranges: [],
  });

  const { data: agents, isLoading } = useQuery(
    ['agents', filters],
    () => agentsAPI.getAll(filters),
    {
      select: (response) => response.data,
    }
  );

  const createMutation = useMutation(agentsAPI.create, {
    onSuccess: () => {
      queryClient.invalidateQueries('agents');
      setCreateDialogOpen(false);
      setNewAgent({
        name: '',
        email: '',
        phone: '',
        license_number: '',
        experience_years: 0,
        areas_of_expertise: [],
        buyer_price_ranges: [],
      });
    },
  });

  const getExperienceTier = (years) => {
    if (years < 2) return { label: 'Junior', color: 'info' };
    if (years < 5) return { label: 'Mid-Level', color: 'warning' };
    return { label: 'Senior', color: 'success' };
  };

  const handleCreateAgent = () => {
    if (newAgent.name && newAgent.email) {
      createMutation.mutate(newAgent);
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
          👥 Agents
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Add Agent
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Agents
              </Typography>
              <Typography variant="h5">
                {agents?.length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Agents
              </Typography>
              <Typography variant="h5">
                {agents?.filter(a => a.is_active).length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Senior Agents
              </Typography>
              <Typography variant="h5">
                {agents?.filter(a => a.experience_years >= 5).length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                New Agents
              </Typography>
              <Typography variant="h5">
                {agents?.filter(a => a.experience_years < 2).length || 0}
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
                value={filters.active_only ? 'active' : 'all'}
                onChange={(e) => handleFilterChange('active_only', e.target.value === 'active')}
                label="Status"
              >
                <MenuItem value="all">All Agents</MenuItem>
                <MenuItem value="active">Active Only</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Search by name"
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Agents Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Agent</TableCell>
              <TableCell>Experience</TableCell>
              <TableCell>Areas of Expertise</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {agents?.map((agent) => {
              const tier = getExperienceTier(agent.experience_years);
              return (
                <TableRow key={agent.id}>
                  <TableCell>
                    <Box>
                      <Typography variant="body1" fontWeight="bold">
                        {agent.name}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {agent.email}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        License: {agent.license_number || 'N/A'}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Chip
                        label={tier.label}
                        color={tier.color}
                        size="small"
                        sx={{ mb: 0.5 }}
                      />
                      <Typography variant="body2">
                        {agent.experience_years} years
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box>
                      {agent.areas_of_expertise?.slice(0, 3).map((area, index) => (
                        <Chip
                          key={index}
                          label={area}
                          size="small"
                          variant="outlined"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                      {agent.areas_of_expertise?.length > 3 && (
                        <Typography variant="caption" color="textSecondary">
                          +{agent.areas_of_expertise.length - 3} more
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={agent.is_active ? 'Active' : 'Inactive'}
                      color={agent.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Button
                        size="small"
                        startIcon={<ViewIcon />}
                        onClick={() => navigate(`/agents/${agent.id}`)}
                      >
                        View
                      </Button>
                      <Button
                        size="small"
                        startIcon={<AssessmentIcon />}
                        color="secondary"
                        onClick={() => navigate(`/agents/${agent.id}`)}
                      >
                        Performance
                      </Button>
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Agent Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Agent</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Full Name"
                value={newAgent.name}
                onChange={(e) => setNewAgent(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={newAgent.email}
                onChange={(e) => setNewAgent(prev => ({ ...prev, email: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={newAgent.phone}
                onChange={(e) => setNewAgent(prev => ({ ...prev, phone: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="License Number"
                value={newAgent.license_number}
                onChange={(e) => setNewAgent(prev => ({ ...prev, license_number: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Years of Experience"
                type="number"
                value={newAgent.experience_years}
                onChange={(e) => setNewAgent(prev => ({ ...prev, experience_years: parseInt(e.target.value) || 0 }))}
                inputProps={{ min: 0, max: 50 }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateAgent}
            variant="contained"
            disabled={createMutation.isLoading}
          >
            {createMutation.isLoading ? <CircularProgress size={20} /> : 'Add Agent'}
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

export default Agents;
