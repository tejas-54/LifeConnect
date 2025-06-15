import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Stepper,
  Step,
  StepLabel,
  Alert,
  CircularProgress,
  Chip,
  Grid,
} from '@mui/material';
import { CloudUpload, PersonAdd } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useWeb3 } from '../contexts/Web3Context';
import { useApp } from '../contexts/AppContext';
import { authAPI, donorAPI, recipientAPI } from '../services/api';
import { ipfsService } from '../services/ipfs';

const steps = ['Basic Info', 'Medical Info', 'Verification'];

const organTypes = [
  'heart', 'liver', 'kidney', 'lung', 'pancreas', 'cornea', 'bone', 'skin', 'tissue'
];

const bloodTypes = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { account, isConnected, connectWallet, contracts } = useWeb3();
  const { setUser } = useApp();
  
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    // Basic Info
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: '',
    phone: '',
    address: '',
    
    // Medical Info
    age: '',
    bloodType: '',
    organTypes: [] as string[],
    medicalHistory: '',
    allergies: '',
    medications: '',
    urgencyScore: 5,
    requiredOrganType: '',
    emergencyContact: '',
    
    // Verification
    healthCard: null as File | null,
    idDocument: null as File | null,
    consent: false,
    termsAccepted: false,
  });

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleOrganTypeToggle = (organType: string) => {
    setFormData(prev => ({
      ...prev,
      organTypes: prev.organTypes.includes(organType)
        ? prev.organTypes.filter(type => type !== organType)
        : [...prev.organTypes, organType]
    }));
  };

  const handleFileUpload = (field: string, file: File | null) => {
    setFormData(prev => ({ ...prev, [field]: file }));
  };

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 0:
        return !!(formData.name && formData.email && formData.password && 
                 formData.password === formData.confirmPassword && formData.role);
      case 1:
        if (formData.role === 'donor') {
          return !!(formData.age && formData.bloodType && formData.organTypes.length > 0);
        } else if (formData.role === 'recipient') {
          return !!(formData.age && formData.bloodType && formData.requiredOrganType);
        }
        return true;
      case 2:
        return !!(formData.healthCard && formData.idDocument && 
                 formData.consent && formData.termsAccepted);
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep(prev => prev + 1);
    } else {
      toast.error('Please fill in all required fields');
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const uploadToIPFS = async (file: File): Promise<string> => {
    try {
      const hash = await ipfsService.uploadFile(file);
      return hash;
    } catch (error) {
      console.error('IPFS upload error:', error);
      throw new Error('Failed to upload file to IPFS');
    }
  };

  const registerOnBlockchain = async (healthCardCID: string) => {
    if (!contracts.donorConsent || !account) {
      throw new Error('Smart contract not available');
    }

    try {
      if (formData.role === 'donor') {
        const tx = await contracts.donorConsent.registerDonor(
          formData.name,
          parseInt(formData.age),
          formData.bloodType,
          formData.organTypes,
          healthCardCID,
          'international', // access rules
          formData.emergencyContact || account
        );
        await tx.wait();
      } else if (formData.role === 'recipient') {
        const tx = await contracts.organLifecycle.registerRecipient(
          formData.name,
          parseInt(formData.age),
          formData.bloodType,
          formData.requiredOrganType,
          formData.urgencyScore,
          healthCardCID
        );
        await tx.wait();
      }
    } catch (error) {
      console.error('Blockchain registration error:', error);
      throw new Error('Failed to register on blockchain');
    }
  };

  const handleSubmit = async () => {
    if (!isConnected) {
      toast.error('Please connect your wallet first');
      await connectWallet();
      return;
    }

    if (!validateStep(2)) {
      toast.error('Please complete all required fields');
      return;
    }

    setLoading(true);
    try {
      // Upload files to IPFS
      const healthCardCID = await uploadToIPFS(formData.healthCard!);
      const idDocumentCID = await uploadToIPFS(formData.idDocument!);

      // Register on blockchain
      await registerOnBlockchain(healthCardCID);

      // Register user in backend
      const userData = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        role: formData.role,
        walletAddress: account!,
        phone: formData.phone,
        address: formData.address,
        age: parseInt(formData.age),
        bloodType: formData.bloodType,
        healthCardCID,
        idDocumentCID,
        organTypes: formData.organTypes,
        medicalHistory: formData.medicalHistory,
        allergies: formData.allergies,
        medications: formData.medications,
        urgencyScore: formData.urgencyScore,
        requiredOrganType: formData.requiredOrganType,
        emergencyContact: formData.emergencyContact,
      };

      const response = await authAPI.register(userData);
      
      if (response.data.token) {
        localStorage.setItem('authToken', response.data.token);
        setUser(response.data.user);
        toast.success('Registration successful!');
        
        // Navigate to appropriate dashboard
        const dashboardRoute = formData.role === 'donor' ? '/donor-dashboard' :
                             formData.role === 'recipient' ? '/recipient-dashboard' :
                             formData.role === 'hospital' ? '/hospital-dashboard' : '/admin-dashboard';
        navigate(dashboardRoute);
      }
    } catch (error: any) {
      console.error('Registration error:', error);
      toast.error(error.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              label="Full Name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              required
              fullWidth
            />
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  required
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Confirm Password"
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  required
                  fullWidth
                  error={formData.password !== formData.confirmPassword && formData.confirmPassword !== ''}
                  helperText={formData.password !== formData.confirmPassword && formData.confirmPassword !== '' ? 'Passwords do not match' : ''}
                />
              </Grid>
            </Grid>
            <FormControl required fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                value={formData.role}
                onChange={(e) => handleInputChange('role', e.target.value)}
                label="Role"
              >
                <MenuItem value="donor">Organ Donor</MenuItem>
                <MenuItem value="recipient">Organ Recipient</MenuItem>
                <MenuItem value="hospital">Hospital/Medical Institution</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Phone Number"
              value={formData.phone}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              fullWidth
            />
            <TextField
              label="Address"
              multiline
              rows={3}
              value={formData.address}
              onChange={(e) => handleInputChange('address', e.target.value)}
              fullWidth
            />
          </Box>
        );

      case 1:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Age"
                  type="number"
                  value={formData.age}
                  onChange={(e) => handleInputChange('age', e.target.value)}
                  required
                  fullWidth
                  inputProps={{ min: 1, max: 120 }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl required fullWidth>
                  <InputLabel>Blood Type</InputLabel>
                  <Select
                    value={formData.bloodType}
                    onChange={(e) => handleInputChange('bloodType', e.target.value)}
                    label="Blood Type"
                  >
                    {bloodTypes.map(type => (
                      <MenuItem key={type} value={type}>{type}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            {formData.role === 'donor' && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Organs willing to donate:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {organTypes.map(organ => (
                    <Chip
                      key={organ}
                      label={organ}
                      clickable
                      color={formData.organTypes.includes(organ) ? 'primary' : 'default'}
                      onClick={() => handleOrganTypeToggle(organ)}
                    />
                  ))}
                </Box>
              </Box>
            )}

            {formData.role === 'recipient' && (
              <Box>
                <FormControl required fullWidth>
                  <InputLabel>Required Organ Type</InputLabel>
                  <Select
                    value={formData.requiredOrganType}
                    onChange={(e) => handleInputChange('requiredOrganType', e.target.value)}
                    label="Required Organ Type"
                  >
                    {organTypes.map(organ => (
                      <MenuItem key={organ} value={organ}>{organ}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Typography variant="body2" sx={{ mt: 1, mb: 2 }}>
                  Urgency Score: {formData.urgencyScore}/10
                </Typography>
                <Box sx={{ px: 2 }}>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={formData.urgencyScore}
                    onChange={(e) => handleInputChange('urgencyScore', parseInt(e.target.value))}
                    style={{ width: '100%' }}
                  />
                </Box>
              </Box>
            )}

            <TextField
              label="Medical History"
              multiline
              rows={3}
              value={formData.medicalHistory}
              onChange={(e) => handleInputChange('medicalHistory', e.target.value)}
              fullWidth
              helperText="Include relevant medical conditions, surgeries, etc."
            />
            <TextField
              label="Allergies"
              value={formData.allergies}
              onChange={(e) => handleInputChange('allergies', e.target.value)}
              fullWidth
            />
            <TextField
              label="Current Medications"
              multiline
              rows={2}
              value={formData.medications}
              onChange={(e) => handleInputChange('medications', e.target.value)}
              fullWidth
            />
            <TextField
              label="Emergency Contact"
              value={formData.emergencyContact}
              onChange={(e) => handleInputChange('emergencyContact', e.target.value)}
              fullWidth
              helperText="Wallet address or phone number"
            />
          </Box>
        );

      case 2:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Typography variant="h6" gutterBottom>
              Upload Required Documents
            </Typography>
            
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Health Card / Medical Records
              </Typography>
              <Button
                variant="outlined"
                component="label"
                startIcon={<CloudUpload />}
                sx={{ mb: 1 }}
              >
                Upload Health Card
                <input
                  type="file"
                  hidden
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => handleFileUpload('healthCard', e.target.files?.[0] || null)}
                />
              </Button>
              {formData.healthCard && (
                <Typography variant="body2" color="success.main">
                  ✓ {formData.healthCard.name}
                </Typography>
              )}
            </Box>

            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Government ID
              </Typography>
              <Button
                variant="outlined"
                component="label"
                startIcon={<CloudUpload />}
                sx={{ mb: 1 }}
              >
                Upload ID Document
                <input
                  type="file"
                  hidden
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => handleFileUpload('idDocument', e.target.files?.[0] || null)}
                />
              </Button>
              {formData.idDocument && (
                <Typography variant="body2" color="success.main">
                  ✓ {formData.idDocument.name}
                </Typography>
              )}
            </Box>

            <Box>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.consent}
                    onChange={(e) => handleInputChange('consent', e.target.checked)}
                  />
                }
                label="I give consent for my medical information to be stored on IPFS and my organ donation status to be recorded on the blockchain"
              />
            </Box>

            <Box>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.termsAccepted}
                    onChange={(e) => handleInputChange('termsAccepted', e.target.checked)}
                  />
                }
                label="I accept the Terms of Service and Privacy Policy"
              />
            </Box>

            {!isConnected && (
              <Alert severity="warning">
                Please connect your wallet to complete registration
              </Alert>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
          <PersonAdd sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold' }}>
            Join LifeConnect
          </Typography>
        </Box>

        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {renderStepContent(activeStep)}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            disabled={activeStep === 0}
            onClick={handleBack}
          >
            Back
          </Button>
          
          <Box sx={{ flex: '1 1 auto' }} />
          
          {activeStep === steps.length - 1 ? (
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={loading || !validateStep(activeStep)}
              startIcon={loading ? <CircularProgress size={20} /> : null}
            >
              {loading ? 'Registering...' : 'Complete Registration'}
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleNext}
              disabled={!validateStep(activeStep)}
            >
              Next
            </Button>
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default Register;
