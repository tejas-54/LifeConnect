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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  Token,
  Redeem,
  History,
  TrendingUp,
  LocalHospital,
  Favorite,
  School,
  SportsEsports,
  Restaurant,
  ShoppingCart,
  AccountBalance,
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import { useWeb3 } from '../contexts/Web3Context';
import { useApp } from '../contexts/AppContext';
import { tokenAPI } from '../services/api';

const TokenManagement: React.FC = () => {
  const { account, contracts, isConnected } = useWeb3();
  const { user } = useApp();
  
  const [tokenBalance, setTokenBalance] = useState('0');
  const [totalEarned, setTotalEarned] = useState('0');
  const [totalRedeemed, setTotalRedeemed] = useState('0');
  const [transactions, setTransactions] = useState([]);
  const [rewards, setRewards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openRedeemDialog, setOpenRedeemDialog] = useState(false);
  const [selectedReward, setSelectedReward] = useState<any>(null);
  const [redeemAmount, setRedeemAmount] = useState('');

  const rewardCategories = [
    {
      id: 'health_checkup',
      name: 'Health Checkup',
      icon: <LocalHospital />,
      description: 'Free annual health checkup',
      cost: 1000,
      color: 'primary',
    },
    {
      id: 'emergency_care',
      name: 'Emergency Care Discount',
      icon: <Favorite />,
      description: '20% discount on emergency medical care',
      cost: 2500,
      color: 'error',
    },
    {
      id: 'education',
      name: 'Educational Course',
      icon: <School />,
      description: 'Free online medical education course',
      cost: 500,
      color: 'info',
    },
    {
      id: 'wellness',
      name: 'Wellness Program',
      icon: <SportsEsports />,
      description: 'Access to premium wellness programs',
      cost: 1500,
      color: 'success',
    },
    {
      id: 'nutrition',
      name: 'Nutrition Consultation',
      icon: <Restaurant />,
      description: 'One-on-one nutrition consultation',
      cost: 750,
      color: 'warning',
    },
    {
      id: 'medical_supplies',
      name: 'Medical Supplies',
      icon: <ShoppingCart />,
      description: 'Discount on medical supplies and equipment',
      cost: 1200,
      color: 'secondary',
    },
  ];

  useEffect(() => {
    if (isConnected && account) {
      loadTokenData();
    }
  }, [isConnected, account]);

  const loadTokenData = async () => {
    try {
      if (!contracts.lifeToken || !account) return;
      
      // Get token balance from smart contract
      const balance = await contracts.lifeToken.balanceOf(account);
      setTokenBalance(balance.toString());
      
      // Get transaction history from API
      const transactionResponse = await tokenAPI.getTransactions(account);
      setTransactions(transactionResponse.data);
      
      // Get available rewards
      const rewardsResponse = await tokenAPI.getRewards();
      setRewards(rewardsResponse.data);
      
      // Calculate totals
      const earned = transactionResponse.data
        .filter((tx: any) => tx.type === 'earned')
        .reduce((sum: number, tx: any) => sum + parseFloat(tx.amount), 0);
      
      const redeemed = transactionResponse.data
        .filter((tx: any) => tx.type === 'redeemed')
        .reduce((sum: number, tx: any) => sum + parseFloat(tx.amount), 0);
      
      setTotalEarned(earned.toString());
      setTotalRedeemed(redeemed.toString());
      
    } catch (error) {
      console.error('Error loading token data:', error);
      toast.error('Failed to load token data');
    } finally {
      setLoading(false);
    }
  };

  const handleRedeemTokens = async () => {
    if (!contracts.lifeToken || !selectedReward || !redeemAmount) return;
    
    const amount = parseFloat(redeemAmount);
    if (amount > parseFloat(tokenBalance)) {
      toast.error('Insufficient token balance');
      return;
    }
    
    try {
      setLoading(true);
      
      // Call smart contract to redeem tokens
      const tx = await contracts.lifeToken.redeemTokens(
        amount.toString(),
        selectedReward.id
      );
      await tx.wait();
      
      // Update backend
      await tokenAPI.redeem(account!, amount, selectedReward.id);
      
      toast.success(`Successfully redeemed ${amount} tokens for ${selectedReward.name}`);
      setOpenRedeemDialog(false);
      setSelectedReward(null);
      setRedeemAmount('');
      
      // Reload data
      await loadTokenData();
      
    } catch (error) {
      console.error('Error redeeming tokens:', error);
      toast.error('Failed to redeem tokens');
    } finally {
      setLoading(false);
    }
  };

  const formatTokenAmount = (amount: string) => {
    return parseFloat(amount).toLocaleString();
  };

  const getTransactionIcon = (type: string, reason: string) => {
    if (type === 'earned') {
      if (reason.includes('DONATION')) return <Favorite color="success" />;
      if (reason.includes('REGISTRATION')) return <AccountBalance color="primary" />;
      if (reason.includes('CHECKUP')) return <LocalHospital color="info" />;
      return <TrendingUp color="success" />;
    }
    return <Redeem color="error" />;
  };

  const getProgressToNextReward = () => {
    const balance = parseFloat(tokenBalance);
    const nextReward = rewardCategories
      .filter(reward => reward.cost > balance)
      .sort((a, b) => a.cost - b.cost)[0];
    
    if (!nextReward) return null;
    
    const progress = (balance / nextReward.cost) * 100;
    return {
      reward: nextReward,
      progress: Math.min(progress, 100),
      tokensNeeded: nextReward.cost - balance,
    };
  };

  const nextRewardProgress = getProgressToNextReward();

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
          Token Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your LifeTokens, view transaction history, and redeem rewards.
        </Typography>
      </Box>

      {/* Token Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <Token />
                </Avatar>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {formatTokenAmount(tokenBalance)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Current Balance
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <TrendingUp />
                </Avatar>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {formatTokenAmount(totalEarned)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Earned
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <Redeem />
                </Avatar>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {formatTokenAmount(totalRedeemed)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Redeemed
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <History />
                </Avatar>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {transactions.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Transactions
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Progress to Next Reward */}
      {nextRewardProgress && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
              Progress to Next Reward
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Avatar sx={{ bgcolor: nextRewardProgress.reward.color + '.main', mr: 2 }}>
                {nextRewardProgress.reward.icon}
              </Avatar>
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                  {nextRewardProgress.reward.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {nextRewardProgress.tokensNeeded > 0 
                    ? `${Math.ceil(nextRewardProgress.tokensNeeded)} more tokens needed`
                    : 'You can claim this reward!'
                  }
                </Typography>
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                {nextRewardProgress.reward.cost} LIFE
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={nextRewardProgress.progress}
              sx={{ height: 8, borderRadius: 4 }}
            />
          </CardContent>
        </Card>
      )}

      <Grid container spacing={4}>
        {/* Available Rewards */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                Available Rewards
              </Typography>

              <Grid container spacing={2}>
                {rewardCategories.map((reward) => (
                  <Grid item xs={12} sm={6} key={reward.id}>
                    <Card 
                      variant="outlined"
                      sx={{ 
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: 2,
                        }
                      }}
                      onClick={() => {
                        setSelectedReward(reward);
                        setOpenRedeemDialog(true);
                      }}
                    >
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <Avatar sx={{ bgcolor: reward.color + '.main', mr: 2 }}>
                            {reward.icon}
                          </Avatar>
                          <Box sx={{ flexGrow: 1 }}>
                            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                              {reward.name}
                            </Typography>
                            <Chip 
                              label={`${reward.cost} LIFE`}
                              color={parseFloat(tokenBalance) >= reward.cost ? 'success' : 'default'}
                              size="small"
                            />
                          </Box>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {reward.description}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Transaction History */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                Recent Transactions
              </Typography>

              <List>
                {transactions.slice(0, 10).map((transaction: any, index) => (
                  <React.Fragment key={index}>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemIcon>
                        {getTransactionIcon(transaction.type, transaction.reason)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Typography variant="body2">
                              {transaction.type === 'earned' ? '+' : '-'}{transaction.amount} LIFE
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(transaction.timestamp).toLocaleDateString()}
                            </Typography>
                          </Box>
                        }
                        secondary={transaction.reason || transaction.rewardType}
                      />
                    </ListItem>
                    {index < transactions.slice(0, 10).length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>

              {transactions.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                  No transactions yet
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Earning Opportunities */}
        <Grid item xs={12}>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Earn more LifeTokens by participating in organ donation activities, 
              completing health checkups, and referring new users to the platform.
            </Typography>
          </Alert>
        </Grid>
      </Grid>

      {/* Redeem Dialog */}
      <Dialog open={openRedeemDialog} onClose={() => setOpenRedeemDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Redeem Reward</DialogTitle>
        <DialogContent>
          {selectedReward && (
            <Box sx={{ py: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar sx={{ bgcolor: selectedReward.color + '.main', mr: 2, width: 56, height: 56 }}>
                  {selectedReward.icon}
                </Avatar>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {selectedReward.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {selectedReward.description}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mb: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Cost: {selectedReward.cost} LIFE tokens
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Your Balance: {formatTokenAmount(tokenBalance)} LIFE tokens
                </Typography>
                <Typography variant="body2" color={parseFloat(tokenBalance) >= selectedReward.cost ? 'success.main' : 'error.main'}>
                  {parseFloat(tokenBalance) >= selectedReward.cost 
                    ? '✓ You have sufficient tokens' 
                    : `✗ Need ${selectedReward.cost - parseFloat(tokenBalance)} more tokens`
                  }
                </Typography>
              </Box>

              <TextField
                label="Amount to Redeem"
                type="number"
                value={redeemAmount}
                onChange={(e) => setRedeemAmount(e.target.value)}
                fullWidth
                inputProps={{ min: 1, max: Math.min(selectedReward.cost, parseFloat(tokenBalance)) }}
                helperText={`Minimum: ${selectedReward.cost} tokens`}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRedeemDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleRedeemTokens}
            disabled={
              !redeemAmount || 
              parseFloat(redeemAmount) < selectedReward?.cost ||
              parseFloat(redeemAmount) > parseFloat(tokenBalance)
            }
          >
            Redeem Tokens
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TokenManagement;
