import React from 'react';
import { Container, Typography, CircularProgress, Box } from '@mui/material';
import { useParams } from 'react-router-dom';

const OpenHouseDetail = () => {
  const { id } = useParams();

  return (
    <Container maxWidth="lg">
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <Box textAlign="center">
          <Typography variant="h4" gutterBottom>
            🏠 Open House Detail
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Detailed view for Open House ID: {id}
          </Typography>
          <Typography variant="body2" sx={{ mt: 2 }}>
            This page will show:
            • Property details and photos
            • Agent recommendations with AI scores
            • Agent selection interface
            • Performance metrics and feedback
          </Typography>
        </Box>
      </Box>
    </Container>
  );
};

export default OpenHouseDetail;
