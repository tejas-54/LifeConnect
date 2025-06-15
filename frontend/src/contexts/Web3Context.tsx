import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ethers } from 'ethers';
import { toast } from 'react-toastify';

// Import contract ABIs - these will be empty for now but prevent import errors
const donorConsentABI = { abi: [] };
const organLifecycleABI = { abi: [] };
const lifeTokenABI = { abi: [] };
const chainOfCustodyABI = { abi: [] };

interface Web3ContextType {
  provider: ethers.BrowserProvider | null;
  signer: ethers.JsonRpcSigner | null;
  account: string | null;
  network: ethers.Network | null;
  contracts: {
    donorConsent: ethers.Contract | null;
    organLifecycle: ethers.Contract | null;
    lifeToken: ethers.Contract | null;
    chainOfCustody: ethers.Contract | null;
  };
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  isConnected: boolean;
  isLoading: boolean;
}

const Web3Context = createContext<Web3ContextType | undefined>(undefined);

export const useWeb3 = () => {
  const context = useContext(Web3Context);
  if (context === undefined) {
    throw new Error('useWeb3 must be used within a Web3Provider');
  }
  return context;
};

interface Web3ProviderProps {
  children: ReactNode;
}

// Mock contract addresses for development
const CONTRACT_ADDRESSES = {
  donorConsent: '0x5FbDB2315678afecb367f032d93F642f64180aa3',
  organLifecycle: '0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512',
  lifeToken: '0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0',
  chainOfCustody: '0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9'
};

export const Web3Provider: React.FC<Web3ProviderProps> = ({ children }) => {
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null);
  const [signer, setSigner] = useState<ethers.JsonRpcSigner | null>(null);
  const [account, setAccount] = useState<string | null>(null);
  const [network, setNetwork] = useState<ethers.Network | null>(null);
  const [contracts, setContracts] = useState({
    donorConsent: null,
    organLifecycle: null,
    lifeToken: null,
    chainOfCustody: null,
  });
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const connectWallet = async () => {
    if (typeof window.ethereum !== 'undefined') {
      try {
        setIsLoading(true);
        
        // Request account access
        await window.ethereum.request({ method: 'eth_requestAccounts' });
        
        // Create provider and signer
        const web3Provider = new ethers.BrowserProvider(window.ethereum);
        const web3Signer = await web3Provider.getSigner();
        const address = await web3Signer.getAddress();
        const currentNetwork = await web3Provider.getNetwork();
        
        setProvider(web3Provider);
        setSigner(web3Signer);
        setAccount(address);
        setNetwork(currentNetwork);
        setIsConnected(true);
        
        // For now, set mock contracts to prevent errors
        setContracts({
          donorConsent: null, // Will be initialized when contracts are deployed
          organLifecycle: null,
          lifeToken: null,
          chainOfCustody: null,
        });
        
        toast.success('Wallet connected successfully!');
      } catch (error) {
        console.error('Error connecting wallet:', error);
        toast.error('Failed to connect wallet');
      } finally {
        setIsLoading(false);
      }
    } else {
      toast.error('Please install MetaMask!');
    }
  };

  const disconnectWallet = () => {
    setProvider(null);
    setSigner(null);
    setAccount(null);
    setNetwork(null);
    setContracts({
      donorConsent: null,
      organLifecycle: null,
      lifeToken: null,
      chainOfCustody: null,
    });
    setIsConnected(false);
    toast.info('Wallet disconnected');
  };

  // Listen for account changes
  useEffect(() => {
    if (window.ethereum) {
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          disconnectWallet();
        } else {
          connectWallet();
        }
      };

      const handleChainChanged = () => {
        window.location.reload();
      };

      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);

      return () => {
        if (window.ethereum) {
          window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
          window.ethereum.removeListener('chainChanged', handleChainChanged);
        }
      };
    }
  }, []);

  const value: Web3ContextType = {
    provider,
    signer,
    account,
    network,
    contracts,
    connectWallet,
    disconnectWallet,
    isConnected,
    isLoading,
  };

  return <Web3Context.Provider value={value}>{children}</Web3Context.Provider>;
};
