import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials: { email: string; password: string }) =>
    api.post('/auth/login', credentials),
  
  register: (userData: {
    name: string;
    email: string;
    password: string;
    role: string;
    walletAddress: string;
  }) => api.post('/auth/register', userData),
  
  profile: () => api.get('/auth/profile'),
};

// Donor API
export const donorAPI = {
  register: (donorData: any) => api.post('/donors/register', donorData),
  getDonor: (address: string) => api.get(`/donors/${address}`),
  updateConsent: (address: string, consent: boolean) => 
    api.put(`/donors/${address}/consent`, { consent }),
  getAllDonors: () => api.get('/donors'),
  getActiveDonors: () => api.get('/donors/active'),
};

// Recipient API
export const recipientAPI = {
  register: (recipientData: any) => api.post('/recipients/register', recipientData),
  getRecipient: (address: string) => api.get(`/recipients/${address}`),
  updateUrgency: (address: string, urgencyScore: number) =>
    api.put(`/recipients/${address}/urgency`, { urgencyScore }),
  getAllRecipients: () => api.get('/recipients'),
  getByOrganType: (organType: string) => api.get(`/recipients/organ/${organType}`),
};

// Organ API
export const organAPI = {
  register: (organData: any) => api.post('/organs/register', organData),
  getOrgan: (id: number) => api.get(`/organs/${id}`),
  getAllOrgans: () => api.get('/organs'),
  getAvailableOrgans: () => api.get('/organs/available'),
  matchOrgan: (organId: number, recipientAddress: string) =>
    api.post(`/organs/${organId}/match`, { recipientAddress }),
  updateStatus: (organId: number, status: string, data: any) =>
    api.put(`/organs/${organId}/status`, { status, ...data }),
};

// AI Matching API
export const matchingAPI = {
  findMatches: (recipientAddress: string) => 
    api.get(`/matching/find/${recipientAddress}`),
  getCompatibilityScore: (organId: number, recipientAddress: string) =>
    api.get(`/matching/compatibility/${organId}/${recipientAddress}`),
  optimizeMatching: (organIds: number[]) => 
    api.post('/matching/optimize', { organIds }),
};

// Logistics API
export const logisticsAPI = {
  calculateRoute: (routeData: any) => api.post('/logistics/route', routeData),
  optimizeRoute: (routeData: any) => api.post('/logistics/optimize', routeData),
  trackTransport: (transportId: string) => api.get(`/logistics/track/${transportId}`),
  updateLocation: (transportId: string, locationData: any) =>
    api.put(`/logistics/track/${transportId}`, locationData),
};

// Token API
export const tokenAPI = {
  getBalance: (address: string) => api.get(`/tokens/balance/${address}`),
  getTransactions: (address: string) => api.get(`/tokens/transactions/${address}`),
  getRewards: () => api.get('/tokens/rewards'),
  redeem: (address: string, amount: number, rewardType: string) =>
    api.post('/tokens/redeem', { address, amount, rewardType }),
};

// IPFS API
export const ipfsAPI = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/ipfs/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  get: (hash: string) => api.get(`/ipfs/${hash}`),
  pin: (hash: string) => api.post(`/ipfs/pin/${hash}`),
};

// Analytics API
export const analyticsAPI = {
  getDashboardStats: () => api.get('/analytics/dashboard'),
  getOrganStats: () => api.get('/analytics/organs'),
  getMatchingStats: () => api.get('/analytics/matching'),
  getTokenStats: () => api.get('/analytics/tokens'),
  getTransportStats: () => api.get('/analytics/transport'),
};

export default api;
