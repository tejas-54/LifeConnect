import React from 'react';
import {
  Box,
  Container,
  Grid,
  Typography,
  Link,
  IconButton,
} from '@mui/material';
import {
  Facebook,
  Twitter,
  LinkedIn,
  GitHub,
  LocalHospital,
} from '@mui/icons-material';

const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: '#1a1a1a',
        color: 'white',
        py: 4,
        mt: 'auto',
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <LocalHospital sx={{ mr: 1, color: '#2e7d32' }} />
              <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
                LifeConnect
              </Typography>
            </Box>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Revolutionizing organ donation through blockchain technology, 
              AI-powered matching, and transparent logistics to save more lives.
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <IconButton sx={{ color: 'white' }}>
                <Facebook />
              </IconButton>
              <IconButton sx={{ color: 'white' }}>
                <Twitter />
              </IconButton>
              <IconButton sx={{ color: 'white' }}>
                <LinkedIn />
              </IconButton>
              <IconButton sx={{ color: 'white' }}>
                <GitHub />
              </IconButton>
            </Box>
          </Grid>

          <Grid item xs={12} md={2}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
              Platform
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link href="/donor-dashboard" color="inherit" underline="hover">
                For Donors
              </Link>
              <Link href="/recipient-dashboard" color="inherit" underline="hover">
                For Recipients
              </Link>
              <Link href="/hospital-dashboard" color="inherit" underline="hover">
                For Hospitals
              </Link>
              <Link href="/organ-tracking" color="inherit" underline="hover">
                Track Organs
              </Link>
            </Box>
          </Grid>

          <Grid item xs={12} md={2}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
              Technology
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link href="#" color="inherit" underline="hover">
                Blockchain
              </Link>
              <Link href="#" color="inherit" underline="hover">
                Smart Contracts
              </Link>
              <Link href="#" color="inherit" underline="hover">
                AI Matching
              </Link>
              <Link href="#" color="inherit" underline="hover">
                IPFS Storage
              </Link>
            </Box>
          </Grid>

          <Grid item xs={12} md={2}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
              Support
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link href="#" color="inherit" underline="hover">
                Documentation
              </Link>
              <Link href="#" color="inherit" underline="hover">
                Help Center
              </Link>
              <Link href="#" color="inherit" underline="hover">
                Contact Us
              </Link>
              <Link href="#" color="inherit" underline="hover">
                Privacy Policy
              </Link>
            </Box>
          </Grid>

          <Grid item xs={12} md={2}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
              Emergency
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="body2" sx={{ color: '#ff6f00' }}>
                24/7 Hotline
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                +1-800-LIFE-911
              </Typography>
              <Typography variant="body2" sx={{ color: '#ff6f00' }}>
                emergency@lifeconnect.org
              </Typography>
            </Box>
          </Grid>
        </Grid>

        <Box
          sx={{
            borderTop: '1px solid #333',
            mt: 4,
            pt: 2,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <Typography variant="body2" sx={{ color: '#888' }}>
            © 2025 LifeConnect. All rights reserved.
          </Typography>
          <Typography variant="body2" sx={{ color: '#888' }}>
            Built with ❤️ for saving lives
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;
