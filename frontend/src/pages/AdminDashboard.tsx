import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Avatar,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  AdminPanelSettings,
  Analytics,
  Security,
  People,
  LocalHospital,
  Token,
  Warning,
  CheckCircle,
  Block,
  Settings,
} from '@mui/icons-material';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
} from 'chart.js';
import { toast } from 'react-toastify';
import { useWeb3 } from '../contexts/Web3Context';
import { useApp } from '../contexts/AppContext';
import { analyticsAPI, authAPI } from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
);

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const AdminDashboard: React.FC = () => {
  const { account, contracts, isConnected } = useWeb3();
  const { user } = useApp();
  
  const [tabValue, setTabValue] = useState(0);
  const [dashboardStats, setDashboardStats] = useState<any>({});
  const [users, setUsers] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [systemHealth, setSystemHealth] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [openUserDialog, setOpenUserDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);

  useEffect(() => {
    if (isConnected && account) {
      loadAdminData();
    }
  }, [isConnected, account]);

  const loadAdminData = async () => {
    try {
      const [statsRes, usersRes] = await Promise.all([
        analyticsAPI.getDashboardStats(),
        authAPI.profile() // This would get all users for admin
      ]);
      
      setDashboardStats(statsRes.data);
      // setUsers(usersRes.data); // Commented as this would need admin-specific endpoint
      
      // Mock system health data
      setSystemHealth({
        blockchain: 'healthy',
        ipfs: 'healthy',
        api: 'healthy',
        matching: 'warning',
        logistics: 'healthy'
      });
    } catch (error) {
      console.error('Error loading admin data:', error);
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  const handleUserStatusToggle = async (userId: string, newStatus: boolean) => {
    try {
      // API call to update user status
      toast.success(`User ${newStatus ? 'activated' : 'deactivated'} successfully`);
      await loadAdminData();
    } catch (error) {
      console.error('Error updating user status:', error);
      toast.error('Failed to update user status');
    }
  };

  const handleSystemMaintenance = async (component: string) => {
    try {
      toast.info(`Starting maintenance for ${component}...`);
      // API call for system maintenance
      setTimeout(() => {
        toast.success(`${component} maintenance completed`);
      }, 3000);
    } catch (error) {
      console.error('Error during maintenance:', error);
      toast.error('Maintenance failed');
    }
  };

  // Chart data
  const organMatchingData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Successful Matches',
        data: [12, 19, 15, 25, 22, 30],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
      },
      {
        label: 'Failed Matches',
        data: [3, 5, 2, 8, 4, 6],
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
      },
    ],
  };

  const organTypeDistribution = {
    labels: ['Heart', 'Liver', 'Kidney', 'Lung', 'Pancreas', 'Cornea'],
    datasets: [
      {
        data: [15, 25, 35, 10, 8, 7],
        backgroundColor: [
          '#FF6384',
          '#36A2EB',
          '#FFCE56',
          '#4BC0C0',
          '#9966FF',
          '#FF9F40',
        ],
      },
    ],
  };

  const systemPerformanceData = {
    labels: ['API Response', 'Blockchain Sync', 'IPFS Storage', 'AI Matching', 'Logistics'],
    datasets: [
      {
        label: 'Performance Score',
        data: [95, 88, 92, 78, 85],
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
      },
    ],
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
          Admin Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          System overview, user management, and platform analytics.
        </Typography>
      </Box>

      {/* System Health Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: systemHealth.blockchain === 'healthy' ? 'success.main' : 'error.main', mr: 2 }}>
                  <Security />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Blockchain
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {systemHealth.blockchain}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: systemHealth.ipfs === 'healthy' ? 'success.main' : 'error.main', mr: 2 }}>
                  <Settings />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    IPFS
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {systemHealth.ipfs}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: systemHealth.api === 'healthy' ? 'success.main' : 'error.main', mr: 2 }}>
                  <Analytics />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    API
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {systemHealth.api}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: systemHealth.matching === 'warning' ? 'warning.main' : 'success.main', mr: 2 }}>
                  <LocalHospital />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    AI Matching
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {systemHealth.matching}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: systemHealth.logistics === 'healthy' ? 'success.main' : 'error.main', mr: 2 }}>
                  <Token />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Logistics
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {systemHealth.logistics}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label="Analytics" />
            <Tab label="User Management" />
            <Tab label="System Control" />
            <Tab label="Reports" />
          </Tabs>
        </Box>

        {/* Analytics Tab */}
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
            Platform Analytics
          </Typography>

          <Grid container spacing={4}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Organ Matching Trends
                  </Typography>
                  <Line data={organMatchingData} />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Organ Type Distribution
                  </Typography>
                  <Doughnut data={organTypeDistribution} />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    System Performance Metrics
                  </Typography>
                  <Bar data={systemPerformanceData} />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* User Management Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              User Management
            </Typography>
            <Button variant="contained" startIcon={<People />}>
              Export Users
            </Button>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Registration</TableCell>
                  <TableCell>Last Activity</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {/* Mock user data */}
                <TableRow>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ mr: 2 }}>JD</Avatar>
                      <Box>
                        <Typography variant="body2">John Doe</Typography>
                        <Typography variant="caption" color="text.secondary">
                          john@example.com
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip label="Donor" color="primary" size="small" />
                  </TableCell>
                  <TableCell>
                    <Chip label="Active" color="success" size="small" />
                  </TableCell>
                  <TableCell>2025-01-15</TableCell>
                  <TableCell>2 hours ago</TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => setOpenUserDialog(true)}>
                      Edit
                    </Button>
                  </TableCell>
                </TableRow>
                {/* Add more mock rows as needed */}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* System Control Tab */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
            System Control Panel
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    System Maintenance
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Button
                      variant="outlined"
                      onClick={() => handleSystemMaintenance('Blockchain')}
                      startIcon={<Security />}
                    >
                      Sync Blockchain Data
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => handleSystemMaintenance('IPFS')}
                      startIcon={<Settings />}
                    >
                      Clear IPFS Cache
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => handleSystemMaintenance('AI Engine')}
                      startIcon={<Analytics />}
                    >
                      Restart AI Engine
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    System Alerts
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Alert severity="warning">
                      AI matching algorithm showing reduced performance
                    </Alert>
                    <Alert severity="info">
                      Scheduled maintenance in 2 hours
                    </Alert>
                    <Alert severity="success">
                      All systems operational
                    </Alert>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Reports Tab */}
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
            System Reports
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Monthly Report
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Generate comprehensive monthly statistics
                  </Typography>
                  <Button variant="contained" fullWidth>
                    Generate Report
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Audit Log
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Download system audit trail
                  </Typography>
                  <Button variant="outlined" fullWidth>
                    Download Log
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Compliance Report
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Generate regulatory compliance report
                  </Typography>
                  <Button variant="outlined" fullWidth>
                    Generate
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>

      {/* User Edit Dialog */}
      <Dialog open={openUserDialog} onClose={() => setOpenUserDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Full Name"
              defaultValue="John Doe"
              fullWidth
            />
            <TextField
              label="Email"
              defaultValue="john@example.com"
              fullWidth
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Account Active"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Email Verified"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenUserDialog(false)}>Cancel</Button>
          <Button variant="contained">Save Changes</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminDashboard;
