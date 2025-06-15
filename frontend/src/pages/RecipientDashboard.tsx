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
  LinearProgress,
  Alert,
  CircularProgress,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Slider,
} from '@mui/material';
import {
  Favorite,
  LocalHospital,
  Search,
  Timeline,
  Emergency,
  Update,
  Verified,
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import { useWeb3 } from '../contexts/Web3Context';
import { useApp } from '../contexts/AppContext';
import { recipientAPI, matchingAPI, organAPI } from '../services/api';

interface RecipientInfo {
  fullName: string;
  age: number;
  bloodType: string;
  requiredOrganType: string;
  urgencyScore: number;
  registrationTimestamp: number;
  isActive: boolean;
  healthCardCID: string;
}

interface MatchedOrgan {
  organId: number;
  donor: string;
  organType: string;
  bloodType: string;
  viabilityScore: string;
  location: string;
  compatibilityScore: number;
}

const RecipientDashboard: React.FC = () => {
  const { account, contracts, isConnected } = useWeb3();
  const { user } = useApp();
  
  const [recipientInfo, setRecipientInfo] = useState<RecipientInfo | null>(null);
  const [matches, setMatches] = useState<MatchedOrgan[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchingMatches, setSearchingMatches] = useState(false);
  const [updatingUrgency, setUpdatingUrgency] = useState(false);

  useEffect(() => {
    if (isConnected && account) {
      loadRecipientData();
      searchForMatches();
    }
  }, [isConnected, account]);

  const loadRecipientData = async () => {
    try {
      if (!contracts.organLifecycle || !account) return;
      
      const recipientData = await contracts.organLifecycle.recipients(account);
      setRecipientInfo({
        fullName: recipientData.fullName,
        age: Number(recipientData.age),
        bloodType: recipientData.bloodType,
        requiredOrganType: recipientData.requiredOrganType,
        urgencyScore: Number(recipientData.urgencyScore),
        registrationTimestamp: Number(recipientData.registrationTimestamp),
        isActive: recipientData.isActive,
        healthCardCID: recipientData.healthCardCID,
      });
    } catch (error) {
      console.error('Error loading recipient data:', error);
      toast.error('Failed to load recipient information');
    }
  };

  const searchForMatches = async () => {
    if (!account) return;
    
    setSearchingMatches(true);
    try {
      const response = await matchingAPI.findMatches(account);
      setMatches(response.data);
    } catch (error) {
      console.error('Error searching for matches:', error);
    } finally {
      setSearchingMatches(false);
      setLoading(false);
    }
  };

  const handleUrgencyUpdate = async (newUrgency: number) => {
    if (!contracts.organLifecycle) return;
    
    setUpdatingUrgency(true);
    try {
      const tx = await contracts.organLifecycle.updateRecipientUrgency(account, newUrgency);
      await tx.wait();
      
      setRecipientInfo(prev => prev ? { ...prev, urgencyScore: newUrgency } : null);
      toast.success('Urgency score updated successfully');
      
      // Re-search for matches with new urgency
      await searchForMatches();
    } catch (error) {
      console.error('Error updating urgency:', error);
      toast.error('Failed to update urgency score');
    } finally {
      setUpdatingUrgency(false);
    }
  };

  const getUrgencyColor = (score: number) => {
    if (score >= 8) return 'error';
    if (score >= 6) return 'warning';
    return 'info';
  };

  const getWaitingTime = () => {
    if (!recipientInfo) return 0;
    const waitingDays = Math.floor((Date.now() - recipientInfo.registrationTimestamp * 1000) / (1000 * 60 * 60 * 24));
    return waitingDays;
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
          Recipient Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back, {user?.name}! Track your organ matching status and manage your profile.
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Recipient Status Card */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <LocalHospital />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Recipient Status
                </Typography>
              </Box>

              {recipientInfo && (
                <Box>
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="text.secondary">Full Name</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 2 }}>
                        {recipientInfo.fullName}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary">Age</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 2 }}>
                        {recipientInfo.age} years
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary">Blood Type</Typography>
                      <Chip 
                        label={recipientInfo.bloodType} 
                        color="primary" 
                        variant="outlined"
                        sx={{ mb: 2 }}
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="text.secondary">Required Organ</Typography>
                      <Chip 
                        label={recipientInfo.requiredOrganType} 
                        color="secondary"
                        sx={{ mb: 2 }}
                      />
                      
                      <Typography variant="body2" color="text.secondary">Waiting Time</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 2 }}>
                        {getWaitingTime()} days
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary">Registration Date</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                        {new Date(recipientInfo.registrationTimestamp * 1000).toLocaleDateString()}
                      </Typography>
                    </Grid>
                  </Grid>

                  <Divider sx={{ my: 3 }} />

                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                        Medical Urgency Score: {recipientInfo.urgencyScore}/10
                      </Typography>
                      <Chip 
                        icon={<Emergency />}
                        label={recipientInfo.urgencyScore >= 8 ? 'Critical' : recipientInfo.urgencyScore >= 6 ? 'High' : 'Moderate'}
                        color={getUrgencyColor(recipientInfo.urgencyScore)}
                      />
                    </Box>
                    
                    <LinearProgress 
                      variant="determinate" 
                      value={recipientInfo.urgencyScore * 10} 
                      color={getUrgencyColor(recipientInfo.urgencyScore)}
                      sx={{ height: 8, borderRadius: 4, mb: 2 }}
                    />
                    
                    <Slider
                      value={recipientInfo.urgencyScore}
                      onChange={(_, value) => handleUrgencyUpdate(value as number)}
                      min={1}
                      max={10}
                      disabled={updatingUrgency}
                      marks
                      valueLabelDisplay="auto"
                      sx={{ mt: 2 }}
                    />
                    
                    <Typography variant="body2" color="text.secondary">
                      Update your urgency score if your medical condition changes
                    </Typography>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Matching Status Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <Search />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Matching Status
                </Typography>
              </Box>
              
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                {matches.length}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Potential matches found
              </Typography>
              
              <Button
                variant="outlined"
                fullWidth
                startIcon={searchingMatches ? <CircularProgress size={20} /> : <Search />}
                onClick={searchForMatches}
                disabled={searchingMatches}
                sx={{ mb: 2 }}
              >
                {searchingMatches ? 'Searching...' : 'Search Again'}
              </Button>
              
              <Button
                variant="contained"
                fullWidth
                onClick={() => window.location.href = '/organ-tracking'}
              >
                View All Matches
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Potential Matches */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <Favorite />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Potential Organ Matches
                </Typography>
              </Box>

              {matches.length > 0 ? (
                <List>
                  {matches.map((match, index) => (
                    <ListItem key={index} divider sx={{ px: 0 }}>
                      <ListItemIcon>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          {match.organId}
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                              {match.organType} - {match.bloodType}
                            </Typography>
                            <Chip 
                              label={`${match.compatibilityScore}% Match`} 
                              color={match.compatibilityScore >= 90 ? 'success' : match.compatibilityScore >= 70 ? 'warning' : 'default'}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Viability: {match.viabilityScore} | Location: {match.location}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Donor: {match.donor.slice(0, 6)}...{match.donor.slice(-4)}
                            </Typography>
                          </Box>
                        }
                      />
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => window.location.href = `/organ-tracking?id=${match.organId}`}
                      >
                        View Details
                      </Button>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                    No matches found at the moment
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    We'll notify you as soon as compatible organs become available
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Important Alerts */}
        <Grid item xs={12}>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Keep your medical information up to date for better matching accuracy. 
              Contact your medical team if your condition changes.
            </Typography>
          </Alert>
          
          {recipientInfo && recipientInfo.urgencyScore >= 8 && (
            <Alert severity="warning">
              <Typography variant="body2">
                Your case is marked as critical. You have priority in the matching algorithm.
              </Typography>
            </Alert>
          )}
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
                    startIcon={<Timeline />}
                    onClick={() => window.location.href = '/organ-tracking'}
                  >
                    Track Matches
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Update />}
                    onClick={() => handleUrgencyUpdate(recipientInfo?.urgencyScore || 5)}
                    disabled={updatingUrgency}
                  >
                    Update Profile
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<LocalHospital />}
                    disabled
                  >
                    Medical Records
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Verified />}
                    disabled
                  >
                    Contact Support
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

export default RecipientDashboard;
