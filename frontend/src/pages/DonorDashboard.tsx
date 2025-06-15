import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  Favorite,
  LocalHospital,
  Verified,
  Update,
  Token,
  History,
  CloudUpload,
  Warning,
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import { useWeb3 } from '../contexts/Web3Context';
import { useApp } from '../contexts/AppContext';
import { donorAPI, tokenAPI } from '../services/api';
import { ipfsService } from '../services/ipfs';

interface DonorInfo {
  fullName: string;
  age: number;
  bloodType: string;
  organTypes: string[];
  isActive: boolean;
  consentGiven: boolean;
  registrationTimestamp: number;
  healthCardCID: string;
}

const DonorDashboard: React.FC = () => {
  const { account, contracts, isConnected } = useWeb3();
  const { user } = useApp();
  
  const [donorInfo, setDonorInfo] = useState<DonorInfo | null>(null);
  const [tokenBalance, setTokenBalance] = useState('0');
  const [loading, setLoading] = useState(true);
  const [updatingConsent, setUpdatingConsent] = useState(false);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    if (isConnected && account) {
      loadDonorData();
      loadTokenData();
    }
  }, [isConnected, account]);

  const loadDonorData = async () => {
    try {
      if (!contracts.donorConsent || !account) return;
      
      const donorData = await contracts.donorConsent.getDonorInfo(account);
      setDonorInfo({
        fullName: donorData.fullName,
        age: Number(donorData.age),
        bloodType: donorData.bloodType,
        organTypes: donorData.organTypes,
        isActive: donorData.isActive,
        consentGiven: donorData.consentGiven,
        registrationTimestamp: Number(donorData.registrationTimestamp),
        healthCardCID: donorData.healthCardCID,
      });
    } catch (error) {
      console.error('Error loading donor data:', error);
      toast.error('Failed to load donor information');
    }
  };

  const loadTokenData = async () => {
    try {
      if (!contracts.lifeToken || !account) return;
      
      const balance = await contracts.lifeToken.balanceOf(account);
      setTokenBalance(balance.toString());
      
      const txResponse = await tokenAPI.getTransactions(account);
      setTransactions(txResponse.data);
    } catch (error) {
      console.error('Error loading token data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConsentToggle = async (newConsent: boolean) => {
    if (!contracts.donorConsent) return;
    
    setUpdatingConsent(true);
    try {
      const tx = await contracts.donorConsent.updateConsent(newConsent);
      await tx.wait();
      
      setDonorInfo(prev => prev ? { ...prev, consentGiven: newConsent } : null);
      toast.success(`Consent ${newConsent ? 'granted' : 'revoked'} successfully`);
    } catch (error) {
      console.error('Error updating consent:', error);
      toast.error('Failed to update consent');
    } finally {
      setUpdatingConsent(false);
    }
  };

  const handleHealthRecordUpdate = async (file: File) => {
    try {
      setLoading(true);
      const cid = await ipfsService.uploadFile(file);
      
      if (!contracts.donorConsent) return;
      const tx = await contracts.donorConsent.updateHealthCard(cid);
      await tx.wait();
      
      setDonorInfo(prev => prev ? { ...prev, healthCardCID: cid } : null);
      toast.success('Health record updated successfully');
    } catch (error) {
      console.error('Error updating health record:', error);
      toast.error('Failed to update health record');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
          Donor Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back, {user?.name}! Manage your organ donation status and track your impact.
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Donor Status Card */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <Favorite />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Donor Status
                </Typography>
              </Box>

              {donorInfo && (
                <Box>
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="text.secondary">Full Name</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 2 }}>
                        {donorInfo.fullName}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary">Age</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 2 }}>
                        {donorInfo.age} years
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary">Blood Type</Typography>
                      <Chip 
                        label={donorInfo.bloodType} 
                        color="primary" 
                        variant="outlined"
                        sx={{ mb: 2 }}
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        Organ Types
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                        {donorInfo.organTypes.map((organ) => (
                          <Chip key={organ} label={organ} size="small" />
                        ))}
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary">Registration Date</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 2 }}>
                        {new Date(donorInfo.registrationTimestamp * 1000).toLocaleDateString()}
                      </Typography>
                    </Grid>
                  </Grid>

                  <Divider sx={{ my: 3 }} />

                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={donorInfo.consentGiven}
                          onChange={(e) => handleConsentToggle(e.target.checked)}
                          disabled={updatingConsent}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body1">
                            Donation Consent {donorInfo.consentGiven ? 'Active' : 'Inactive'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Toggle to update your consent status
                          </Typography>
                        </Box>
                      }
                    />
                    
                    {donorInfo.isActive ? (
                      <Chip 
                        icon={<Verified />} 
                        label="Active Donor" 
                        color="success" 
                      />
                    ) : (
                      <Chip 
                        icon={<Warning />} 
                        label="Inactive" 
                        color="warning" 
                      />
                    )}
                  </Box>

                  {!donorInfo.consentGiven && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      Your donation consent is currently inactive. Enable it to participate in organ matching.
                    </Alert>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Token Balance Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                  <Token />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  LifeTokens
                </Typography>
              </Box>
              
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                {parseFloat(tokenBalance).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Total tokens earned
              </Typography>
              
              <Button
                variant="outlined"
                fullWidth
                onClick={() => window.location.href = '/token-management'}
              >
                Manage Tokens
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Health Records Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <LocalHospital />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Health Records
                </Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Keep your health information up to date for better matching
              </Typography>

              <Button
                variant="outlined"
                component="label"
                startIcon={<CloudUpload />}
                fullWidth
                sx={{ mb: 2 }}
              >
                Update Health Record
                <input
                  type="file"
                  hidden
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleHealthRecordUpdate(file);
                  }}
                />
              </Button>

              {donorInfo?.healthCardCID && (
                <Typography variant="body2" color="success.main">
                  ✓ Health record stored on IPFS: {donorInfo.healthCardCID.slice(0, 12)}...
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <History />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Recent Activity
                </Typography>
              </Box>

              <List>
                {transactions.length > 0 ? (
                  transactions.slice(0, 5).map((tx: any, index) => (
                    <ListItem key={index} divider>
                      <ListItemIcon>
                        <Token color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={`+${tx.amount} LIFE tokens`}
                        secondary={`${tx.reason} - ${new Date(tx.timestamp).toLocaleDateString()}`}
                      />
                    </ListItem>
                  ))
                ) : (
                  <ListItem>
                    <ListItemText
                      primary="No recent activity"
                      secondary="Your token transactions will appear here"
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                Quick Actions
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<Update />}
                    onClick={() => window.location.href = '/organ-tracking'}
                  >
                    Track Organs
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Token />}
                    onClick={() => window.location.href = '/token-management'}
                  >
                    View Rewards
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<LocalHospital />}
                    disabled
                  >
                    Medical History
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Verified />}
                    disabled
                  >
                    Verify Identity
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DonorDashboard;
