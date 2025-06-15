import React from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardMedia,
  CardActions,
  Chip,
  Avatar,
  Paper,
} from '@mui/material';
import {
  LocalHospital,
  Security,
  Psychology,
  Speed,
  Favorite,
  People,
  Timeline,
  Token,
} from '@mui/icons-material';
import { Link, useNavigate } from 'react-router-dom';
import { useWeb3 } from '../contexts/Web3Context';
import { useApp } from '../contexts/AppContext';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const { isConnected, connectWallet } = useWeb3();
  const { isAuthenticated } = useApp();

  const features = [
    {
      icon: <Security />,
      title: 'Blockchain Security',
      description: 'Immutable records and smart contracts ensure data integrity and consent management.',
    },
    {
      icon: <Psychology />,
      title: 'AI-Powered Matching',
      description: 'Advanced algorithms find the best donor-recipient matches based on medical compatibility.',
    },
    {
      icon: <Speed />,
      title: 'Real-time Tracking',
      description: 'Track organ transport with GPS and IoT sensors for optimal timing and safety.',
    },
    {
      icon: <Token />,
      title: 'Token Rewards',
      description: 'Earn LifeTokens for participation and redeem them for healthcare benefits.',
    },
  ];

  const stats = [
    { number: '10,000+', label: 'Lives Saved', icon: <Favorite /> },
    { number: '25,000+', label: 'Registered Donors', icon: <People /> },
    { number: '500+', label: 'Partner Hospitals', icon: <LocalHospital /> },
    { number: '99.9%', label: 'Success Rate', icon: <Timeline /> },
  ];

  const handleGetStarted = () => {
    if (!isConnected) {
      connectWallet();
    } else if (!isAuthenticated) {
      navigate('/register');
    } else {
      navigate('/donor-dashboard');
    }
  };

  return (
    <Box>
      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%)',
          color: 'white',
          py: 8,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography
                variant="h2"
                component="h1"
                sx={{
                  fontWeight: 'bold',
                  mb: 3,
                  fontSize: { xs: '2.5rem', md: '3.5rem' },
                }}
              >
                Save Lives with
                <br />
                <span style={{ color: '#ff6f00' }}>LifeConnect</span>
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  mb: 4,
                  opacity: 0.9,
                  lineHeight: 1.4,
                }}
              >
                Revolutionary organ donation platform powered by blockchain,
                AI matching, and real-time logistics to connect donors and
                recipients seamlessly.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleGetStarted}
                  sx={{
                    bgcolor: '#ff6f00',
                    '&:hover': { bgcolor: '#f57c00' },
                    px: 4,
                    py: 1.5,
                  }}
                >
                  {!isConnected ? 'Connect Wallet' : !isAuthenticated ? 'Get Started' : 'Go to Dashboard'}
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  component={Link}
                  to="/organ-tracking"
                  sx={{
                    borderColor: 'white',
                    color: 'white',
                    '&:hover': { borderColor: '#ff6f00', color: '#ff6f00' },
                    px: 4,
                    py: 1.5,
                  }}
                >
                  Track Organs
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: 400,
                }}
              >
                <LocalHospital
                  sx={{
                    fontSize: '20rem',
                    opacity: 0.2,
                    color: 'white',
                  }}
                />
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Stats Section */}
      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Grid container spacing={4}>
          {stats.map((stat, index) => (
            <Grid item xs={6} md={3} key={index}>
              <Paper
                elevation={3}
                sx={{
                  p: 3,
                  textAlign: 'center',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: '#2e7d32',
                    width: 60,
                    height: 60,
                    mb: 2,
                  }}
                >
                  {stat.icon}
                </Avatar>
                <Typography
                  variant="h4"
                  sx={{ fontWeight: 'bold', color: '#2e7d32', mb: 1 }}
                >
                  {stat.number}
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  {stat.label}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Features Section */}
      <Box sx={{ bgcolor: '#f5f5f5', py: 8 }}>
        <Container maxWidth="lg">
          <Typography
            variant="h3"
            component="h2"
            sx={{
              textAlign: 'center',
              mb: 2,
              fontWeight: 'bold',
              color: '#2e7d32',
            }}
          >
            Revolutionary Technology
          </Typography>
          <Typography
            variant="h6"
            sx={{
              textAlign: 'center',
              mb: 6,
              color: 'text.secondary',
              maxWidth: 600,
              mx: 'auto',
            }}
          >
            Combining cutting-edge technologies to create the most efficient
            and transparent organ donation ecosystem.
          </Typography>

          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
                    },
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Avatar
                        sx={{
                          bgcolor: '#2e7d32',
                          mr: 2,
                          width: 48,
                          height: 48,
                        }}
                      >
                        {feature.icon}
                      </Avatar>
                      <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold' }}>
                        {feature.title}
                      </Typography>
                    </Box>
                    <Typography variant="body1" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* How It Works Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography
          variant="h3"
          component="h2"
          sx={{
            textAlign: 'center',
            mb: 6,
            fontWeight: 'bold',
            color: '#2e7d32',
          }}
        >
          How LifeConnect Works
        </Typography>

        <Grid container spacing={4} alignItems="center">
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{
                  bgcolor: '#ff6f00',
                  width: 80,
                  height: 80,
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                  1
                </Typography>
              </Avatar>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                Register & Consent
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Donors and recipients register on the blockchain with verified
                medical records stored on IPFS.
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{
                  bgcolor: '#ff6f00',
                  width: 80,
                  height: 80,
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                  2
                </Typography>
              </Avatar>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                AI Matching
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Advanced AI algorithms analyze medical compatibility and find
                the best donor-recipient matches.
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{
                  bgcolor: '#ff6f00',
                  width: 80,
                  height: 80,
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                  3
                </Typography>
              </Avatar>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                Safe Transport
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Real-time tracking and optimized logistics ensure organs reach
                recipients in optimal condition.
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box
        sx={{
          bgcolor: '#1a1a1a',
          color: 'white',
          py: 8,
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Typography
            variant="h3"
            component="h2"
            sx={{ mb: 3, fontWeight: 'bold' }}
          >
            Ready to Save Lives?
          </Typography>
          <Typography
            variant="h6"
            sx={{ mb: 4, opacity: 0.8 }}
          >
            Join thousands of donors, recipients, and healthcare providers
            making a difference through LifeConnect.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              size="large"
              component={Link}
              to="/register"
              sx={{
                bgcolor: '#2e7d32',
                '&:hover': { bgcolor: '#1b5e20' },
                px: 4,
                py: 1.5,
              }}
            >
              Become a Donor
            </Button>
            <Button
              variant="outlined"
              size="large"
              component={Link}
              to="/register"
              sx={{
                borderColor: '#ff6f00',
                color: '#ff6f00',
                '&:hover': { bgcolor: '#ff6f00', color: 'white' },
                px: 4,
                py: 1.5,
              }}
            >
              Find a Match
            </Button>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default Home;
