import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  TextField,
  Chip,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
  Paper,
  Alert,
  CircularProgress,
  Avatar,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Search,
  LocationOn,
  Schedule,
  LocalHospital,
  FlightTakeoff,
  Verified,
  Warning,
  CheckCircle,
  LocalShipping,
  Emergency,
  QrCodeScanner,
  Map,
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import { useWeb3 } from '../contexts/Web3Context';
import { organAPI, logisticsAPI } from '../services/api';

const OrganTracking: React.FC = () => {
  const { contracts, isConnected } = useWeb3();
  
  const [searchId, setSearchId] = useState('');
  const [organData, setOrganData] = useState<any>(null);
  const [checkpoints, setCheckpoints] = useState<any[]>([]);
  const [transportRoute, setTransportRoute] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [openUpdateDialog, setOpenUpdateDialog] = useState(false);
  const [newCheckpoint, setNewCheckpoint] = useState({
    type: 0,
    location: '',
    notes: '',
    documentCID: '',
  });

  const checkpointTypes = [
    'HARVEST',
    'PICKUP',
    'TRANSIT_START',
    'CUSTOMS_CHECK',
    'HANDOVER',
    'ARRIVAL',
    'DELIVERY',
    'TRANSPLANT_START',
    'TRANSPLANT_COMPLETE'
  ];

  const statusIcons = {
    0: <LocalHospital color="primary" />,
    1: <LocalShipping color="info" />,
    2: <FlightTakeoff color="warning" />,
    3: <Verified color="success" />,
    4: <LocalShipping color="info" />,
    5: <LocationOn color="secondary" />,
    6: <CheckCircle color="success" />,
    7: <Emergency color="error" />,
    8: <Verified color="success" />,
  };

  const statusColors = {
    0: 'primary',
    1: 'info',
    2: 'warning',
    3: 'success',
    4: 'info',
    5: 'secondary',
    6: 'success',
    7: 'error',
    8: 'success',
  };

  useEffect(() => {
    // Check URL params for organ ID
    const urlParams = new URLSearchParams(window.location.search);
    const organId = urlParams.get('id');
    if (organId) {
      setSearchId(organId);
      handleSearch(organId);
    }
  }, []);

  const handleSearch = async (id?: string) => {
    const organId = id || searchId;
    if (!organId) {
      toast.error('Please enter an organ ID');
      return;
    }

    setLoading(true);
    try {
      // Get organ data from blockchain
      if (contracts.organLifecycle) {
        const organInfo = await contracts.organLifecycle.getOrganInfo(parseInt(organId));
        setOrganData({
          organId: Number(organInfo.organId),
          donor: organInfo.donor,
          organType: organInfo.organType,
          bloodType: organInfo.bloodType,
          harvestTimestamp: Number(organInfo.harvestTimestamp),
          expiryTimestamp: Number(organInfo.expiryTimestamp),
          status: Number(organInfo.status),
          assignedRecipient: organInfo.assignedRecipient,
          viabilityScore: organInfo.viabilityScore,
          location: organInfo.location,
        });
      }

      // Get checkpoints from chain of custody
      if (contracts.chainOfCustody) {
        const checkpointData = await contracts.chainOfCustody.getOrganCheckpoints(parseInt(organId));
        setCheckpoints(checkpointData.map((cp: any) => ({
          checkpointId: Number(cp.checkpointId),
          organId: Number(cp.organId),
          checkpointType: Number(cp.checkpointType),
          custodian: cp.custodian,
          location: cp.location,
          timestamp: Number(cp.timestamp),
          notes: cp.notes,
          documentCID: cp.documentCID,
          verified: cp.verified,
          verifiedBy: cp.verifiedBy,
        })));
      }

      // Get transport route data
      try {
        const routeResponse = await logisticsAPI.trackTransport(organId);
        setTransportRoute(routeResponse.data);
      } catch (error) {
        console.log('No transport route found');
      }

    } catch (error) {
      console.error('Error searching for organ:', error);
      toast.error('Organ not found or error occurred');
      setOrganData(null);
      setCheckpoints([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCheckpoint = async () => {
    if (!contracts.chainOfCustody || !organData) return;

    try {
      const tx = await contracts.chainOfCustody.addCheckpoint(
        organData.organId,
        newCheckpoint.type,
        newCheckpoint.location,
        newCheckpoint.notes,
        newCheckpoint.documentCID
      );
      await tx.wait();

      toast.success('Checkpoint added successfully');
      setOpenUpdateDialog(false);
      setNewCheckpoint({ type: 0, location: '', notes: '', documentCID: '' });
      await handleSearch(organData.organId.toString());
    } catch (error) {
      console.error('Error adding checkpoint:', error);
      toast.error('Failed to add checkpoint');
    }
  };

  const getTimeRemaining = () => {
    if (!organData) return 'N/A';
    const now = Math.floor(Date.now() / 1000);
    const remaining = organData.expiryTimestamp - now;
    if (remaining <= 0) return 'EXPIRED';
    
    const hours = Math.floor(remaining / 3600);
    const minutes = Math.floor((remaining % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const getStatusLabel = (status: number) => {
    const labels = ['Available', 'Matched', 'In Transit', 'Transplanted', 'Expired', 'Rejected'];
    return labels[status] || 'Unknown';
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
          Organ Tracking
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time tracking of organ location, transport, and status updates.
        </Typography>
      </Box>

      {/* Search Section */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <TextField
              label="Organ ID"
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              placeholder="Enter organ ID to track"
              sx={{ flexGrow: 1 }}
            />
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <Search />}
              onClick={() => handleSearch()}
              disabled={loading}
              sx={{ px: 4 }}
            >
              {loading ? 'Searching...' : 'Track'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<QrCodeScanner />}
              disabled
            >
              Scan QR
            </Button>
          </Box>
        </CardContent>
      </Card>

      {organData && (
        <Grid container spacing={4}>
          {/* Organ Information Card */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    Organ #{organData.organId} - {organData.organType}
                  </Typography>
                  <Chip 
                    label={getStatusLabel(organData.status)}
                    color={statusColors[organData.status as keyof typeof statusColors] as any}
                  />
                </Box>

                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">Blood Type</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 2 }}>
                      {organData.bloodType}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary">Donor Address</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 2, fontFamily: 'monospace' }}>
                      {organData.donor.slice(0, 6)}...{organData.donor.slice(-4)}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary">Viability Score</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 2 }}>
                      {organData.viabilityScore}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">Current Location</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <LocationOn sx={{ fontSize: 16, mr: 0.5 }} />
                      <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                        {organData.location}
                      </Typography>
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary">Time Remaining</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Schedule sx={{ fontSize: 16, mr: 0.5 }} />
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          fontWeight: 'medium',
                          color: getTimeRemaining().includes('EXPIRED') ? 'error.main' : 'inherit'
                        }}
                      >
                        {getTimeRemaining()}
                      </Typography>
                    </Box>
                    
                    {organData.assignedRecipient !== '0x0000000000000000000000000000000000000000' && (
                      <>
                        <Typography variant="body2" color="text.secondary">Assigned Recipient</Typography>
                        <Typography variant="body1" sx={{ fontWeight: 'medium', fontFamily: 'monospace' }}>
                          {organData.assignedRecipient.slice(0, 6)}...{organData.assignedRecipient.slice(-4)}
                        </Typography>
                      </>
                    )}
                  </Grid>
                </Grid>

                <Divider sx={{ my: 3 }} />

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Harvested: {new Date(organData.harvestTimestamp * 1000).toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Expires: {new Date(organData.expiryTimestamp * 1000).toLocaleString()}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Quick Actions Card */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                  Quick Actions
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={<LocationOn />}
                    onClick={() => setOpenUpdateDialog(true)}
                    fullWidth
                  >
                    Add Checkpoint
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Map />}
                    fullWidth
                    disabled
                  >
                    View on Map
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Emergency />}
                    color="error"
                    fullWidth
                    disabled
                  >
                    Report Issue
                  </Button>
                </Box>

                <Divider sx={{ my: 3 }} />

                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                  Transport Info
                </Typography>
                
                {transportRoute ? (
                  <List>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemIcon>
                        <LocalShipping />
                      </ListItemIcon>
                      <ListItemText
                        primary="Transport Mode"
                        secondary={transportRoute.transportMode}
                      />
                    </ListItem>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemIcon>
                        <Schedule />
                      </ListItemIcon>
                      <ListItemText
                        primary="Estimated Duration"
                        secondary={`${transportRoute.estimatedDuration} hours`}
                      />
                    </ListItem>
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No transport information available
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Chain of Custody Timeline */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                  Chain of Custody
                </Typography>

                {checkpoints.length > 0 ? (
                  <Timeline>
                    {checkpoints.map((checkpoint, index) => (
                      <TimelineItem key={checkpoint.checkpointId}>
                        <TimelineOppositeContent sx={{ m: 'auto 0' }} variant="body2" color="text.secondary">
                          {new Date(checkpoint.timestamp * 1000).toLocaleString()}
                        </TimelineOppositeContent>
                        <TimelineSeparator>
                          <TimelineDot color={statusColors[checkpoint.checkpointType as keyof typeof statusColors] as any}>
                            {statusIcons[checkpoint.checkpointType as keyof typeof statusIcons]}
                          </TimelineDot>
                          {index < checkpoints.length - 1 && <TimelineConnector />}
                        </TimelineSeparator>
                        <TimelineContent sx={{ py: '12px', px: 2 }}>
                          <Paper elevation={2} sx={{ p: 2 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 1 }}>
                              <Typography variant="h6" component="span">
                                {checkpointTypes[checkpoint.checkpointType]}
                              </Typography>
                              {checkpoint.verified && (
                                <Chip icon={<Verified />} label="Verified" color="success" size="small" />
                              )}
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                              <LocationOn sx={{ fontSize: 14, mr: 0.5 }} />
                              {checkpoint.location}
                            </Typography>
                            {checkpoint.notes && (
                              <Typography variant="body2" sx={{ mb: 1 }}>
                                {checkpoint.notes}
                              </Typography>
                            )}
                            <Typography variant="caption" color="text.secondary">
                              Custodian: {checkpoint.custodian.slice(0, 6)}...{checkpoint.custodian.slice(-4)}
                            </Typography>
                            {checkpoint.documentCID && (
                              <Typography variant="caption" color="primary" sx={{ display: 'block' }}>
                                Document: {checkpoint.documentCID.slice(0, 12)}...
                              </Typography>
                            )}
                          </Paper>
                        </TimelineContent>
                      </TimelineItem>
                    ))}
                  </Timeline>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      No custody checkpoints recorded yet
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Alerts */}
          <Grid item xs={12}>
            {getTimeRemaining().includes('EXPIRED') && (
              <Alert severity="error" sx={{ mb: 2 }}>
                This organ has expired and is no longer viable for transplantation.
              </Alert>
            )}
            
            {organData.status === 4 && (
              <Alert severity="error">
                This organ has been marked as expired in the system.
              </Alert>
            )}
            
            {organData.status === 5 && (
              <Alert severity="warning">
                This organ has been rejected and is no longer in the transplant process.
              </Alert>
            )}
          </Grid>
        </Grid>
      )}

      {!organData && !loading && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
              Enter an Organ ID to begin tracking
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Track real-time location, transport status, and chain of custody for any organ in the system.
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Add Checkpoint Dialog */}
      <Dialog open={openUpdateDialog} onClose={() => setOpenUpdateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Checkpoint</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Checkpoint Type</InputLabel>
              <Select
                value={newCheckpoint.type}
                onChange={(e) => setNewCheckpoint({...newCheckpoint, type: Number(e.target.value)})}
                label="Checkpoint Type"
              >
                {checkpointTypes.map((type, index) => (
                  <MenuItem key={index} value={index}>{type}</MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <TextField
              label="Location"
              value={newCheckpoint.location}
              onChange={(e) => setNewCheckpoint({...newCheckpoint, location: e.target.value})}
              fullWidth
              required
            />
            
            <TextField
              label="Notes"
              value={newCheckpoint.notes}
              onChange={(e) => setNewCheckpoint({...newCheckpoint, notes: e.target.value})}
              multiline
              rows={3}
              fullWidth
            />
            
            <TextField
              label="Document CID (optional)"
              value={newCheckpoint.documentCID}
              onChange={(e) => setNewCheckpoint({...newCheckpoint, documentCID: e.target.value})}
              fullWidth
              helperText="IPFS hash of supporting documents"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenUpdateDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleAddCheckpoint}
            disabled={!newCheckpoint.location}
          >
            Add Checkpoint
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default OrganTracking;
