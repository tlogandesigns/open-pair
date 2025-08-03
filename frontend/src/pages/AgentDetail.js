import React from 'react';
import { Container, Typography, CircularProgress, Box } from '@mui/material';
import { useParams } from 'react-router-dom';

const AgentDetail = () => {
  const { id } = useParams();

  return (
    <Container maxWidth="lg">
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <Box textAlign="center">
          <Typography variant="h4" gutterBottom>
            👤 Agent Profile
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Detailed view for Agent ID: {id}
          </Typography>
          <Typography variant="body2" sx={{ mt: 2 }}>
            This page will show:
            • Agent contact information and photo
            • Performance history and metrics
            • Fairness score and opportunity distribution
            • Areas of expertise and buyer profiles
            • Calendar availability and preferences
          </Typography>
        </Box>
      </Box>
    </Container>
  );
};

export default AgentDetail;
