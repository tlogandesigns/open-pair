import React from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  EventAvailable as EventIcon,
  Assessment as AssessmentIcon,
  Email as EmailIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { dashboardAPI } from '../services/api';

const Dashboard = () => {
  const { data: stats, isLoading: statsLoading } = useQuery(
    'dashboardStats',
    dashboardAPI.getStats,
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  const { data: weeklyData, isLoading: weeklyLoading } = useQuery(
    'weeklySummary',
    dashboardAPI.getWeeklySummary
  );

  const { data: unassignedData, isLoading: unassignedLoading } = useQuery(
    'upcomingUnassigned',
    () => dashboardAPI.getUpcomingUnassigned(7)
  );

  const handleSendWeeklyEmail = () => {
    // This would typically open a dialog to select recipients
    const recipients = ['manager@realestate.com', 'team@realestate.com'];
    dashboardAPI.sendWeeklyEmail(recipients);
  };

  const handleRetrainModel = () => {
    dashboardAPI.retrainModel();
  };

  if (statsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        📊 Dashboard
      </Typography>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <PeopleIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Agents
                  </Typography>
                  <Typography variant="h5">
                    {stats?.active_agents || 0}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    of {stats?.total_agents || 0} total
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <EventIcon color="secondary" sx={{ fontSize: 40, mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Upcoming Open Houses
                  </Typography>
                  <Typography variant="h5">
                    {stats?.upcoming_open_houses || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingUpIcon color="success" sx={{ fontSize: 40, mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Avg Conversion Rate
                  </Typography>
                  <Typography variant="h5">
                    {((stats?.average_conversion_rate || 0) * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <AssessmentIcon color="warning" sx={{ fontSize: 40, mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Completed This Month
                  </Typography>
                  <Typography variant="h5">
                    {stats?.completed_open_houses_this_month || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Top Performing Agents */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              🌟 Top Performing Agents (Last 30 Days)
            </Typography>
            <List>
              {stats?.top_performing_agents?.map((agent, index) => (
                <ListItem key={agent.agent_id}>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: index === 0 ? 'gold' : index === 1 ? 'silver' : '#cd7f32' }}>
                      {index + 1}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={agent.agent_name}
                    secondary={
                      <Box>
                        <Typography variant="body2">
                          {agent.open_houses_hosted} open houses hosted
                        </Typography>
                        <Typography variant="body2">
                          {agent.total_leads} leads generated • {agent.avg_attendees?.toFixed(1)} avg attendees
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              )) || (
                <ListItem>
                  <ListItemText primary="No performance data available" />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>

        {/* Upcoming Unassigned Open Houses */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6">
                ⚠️ Need Assignment ({unassignedData?.count || 0})
              </Typography>
              <Chip 
                label={`${unassignedData?.count || 0} urgent`}
                color={unassignedData?.count > 0 ? 'error' : 'success'}
                size="small"
              />
            </Box>
            <List>
              {unassignedData?.unassigned_open_houses?.slice(0, 5).map((item) => (
                <ListItem key={item.open_house.id}>
                  <ListItemText
                    primary={item.listing?.address || 'Address not available'}
                    secondary={
                      <Box>
                        <Typography variant="body2">
                          {new Date(item.open_house.start_time).toLocaleDateString()} at{' '}
                          {new Date(item.open_house.start_time).toLocaleTimeString()}
                        </Typography>
                        {item.top_recommendations?.[0] && (
                          <Typography variant="body2" color="primary">
                            Recommended: {item.top_recommendations[0].agent?.name} ({(item.top_recommendations[0].score * 100).toFixed(0)}%)
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  <Chip 
                    label={`${item.days_until}d`}
                    size="small"
                    color={item.days_until <= 1 ? 'error' : item.days_until <= 3 ? 'warning' : 'default'}
                  />
                </ListItem>
              )) || (
                <ListItem>
                  <ListItemText primary="All open houses are assigned! 🎉" />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>

        {/* Weekly Summary Chart */}
        {weeklyData && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                📈 This Week's Open House Activity
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={[
                  {
                    name: 'Open Houses',
                    Total: weeklyData.summary_stats?.total_open_houses || 0,
                    Assigned: weeklyData.summary_stats?.assigned_houses || 0,
                    Pending: weeklyData.summary_stats?.pending_houses || 0,
                  }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="Total" fill="#2c3e50" />
                  <Bar dataKey="Assigned" fill="#27ae60" />
                  <Bar dataKey="Pending" fill="#e74c3c" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        )}

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              🚀 Quick Actions
            </Typography>
            <Box display="flex" gap={2} flexWrap="wrap">
              <Button
                variant="contained"
                startIcon={<EmailIcon />}
                onClick={handleSendWeeklyEmail}
                color="primary"
              >
                Send Weekly Summary
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleRetrainModel}
                color="secondary"
              >
                Retrain AI Model
              </Button>
              <Button
                variant="outlined"
                onClick={() => window.location.href = '/open-houses'}
              >
                View All Open Houses
              </Button>
              <Button
                variant="outlined"
                onClick={() => window.location.href = '/agents'}
              >
                Manage Agents
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
