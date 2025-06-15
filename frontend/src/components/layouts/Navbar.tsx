import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Chip,
} from '@mui/material';
import {
  AccountCircle,
  Logout,
  Dashboard,
  LocalHospital,
  Favorite,
  Timeline,
  Token,
} from '@mui/icons-material';
import { useNavigate, Link } from 'react-router-dom';
import { useWeb3 } from '../../contexts/Web3Context';
import { useApp } from '../../contexts/AppContext';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { account, isConnected, connectWallet, disconnectWallet } = useWeb3();
  const { user, setUser, isAuthenticated } = useApp();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    setUser(null);
    disconnectWallet();
    localStorage.removeItem('authToken');
    navigate('/');
    handleMenuClose();
  };

  const getDashboardRoute = () => {
    switch (user?.role) {
      case 'donor':
        return '/donor-dashboard';
      case 'recipient':
        return '/recipient-dashboard';
      case 'hospital':
        return '/hospital-dashboard';
      case 'admin':
        return '/admin-dashboard';
      default:
        return '/';
    }
  };

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <AppBar position="fixed" sx={{ backgroundColor: '#2e7d32' }}>
      <Toolbar>
        <LocalHospital sx={{ mr: 2 }} />
        <Typography
          variant="h6"
          component={Link}
          to="/"
          sx={{
            flexGrow: 1,
            textDecoration: 'none',
            color: 'inherit',
            fontWeight: 'bold',
          }}
        >
          LifeConnect
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {isAuthenticated && (
            <>
              <Button
                color="inherit"
                startIcon={<Dashboard />}
                component={Link}
                to={getDashboardRoute()}
              >
                Dashboard
              </Button>
              <Button
                color="inherit"
                startIcon={<Timeline />}
                component={Link}
                to="/organ-tracking"
              >
                Tracking
              </Button>
              <Button
                color="inherit"
                startIcon={<Token />}
                component={Link}
                to="/token-management"
              >
                Tokens
              </Button>
            </>
          )}

          {isConnected && account && (
            <Chip
              label={formatAddress(account)}
              variant="outlined"
              sx={{ color: 'white', borderColor: 'white' }}
            />
          )}

          {isAuthenticated ? (
            <>
              <IconButton
                color="inherit"
                onClick={handleMenuClick}
                sx={{ ml: 1 }}
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                  {user?.name?.charAt(0).toUpperCase()}
                </Avatar>
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
              >
                <MenuItem>
                  <AccountCircle sx={{ mr: 1 }} />
                  {user?.name} ({user?.role})
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                  <Logout sx={{ mr: 1 }} />
                  Logout
                </MenuItem>
              </Menu>
            </>
          ) : (
            <Box sx={{ display: 'flex', gap: 1 }}>
              {!isConnected ? (
                <Button
                  color="inherit"
                  variant="outlined"
                  onClick={connectWallet}
                >
                  Connect Wallet
                </Button>
              ) : (
                <>
                  <Button
                    color="inherit"
                    component={Link}
                    to="/login"
                  >
                    Login
                  </Button>
                  <Button
                    color="inherit"
                    variant="outlined"
                    component={Link}
                    to="/register"
                  >
                    Register
                  </Button>
                </>
              )}
            </Box>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
