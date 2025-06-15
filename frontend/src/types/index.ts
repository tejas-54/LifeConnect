export interface User {
  id: string;
  address: string;
  role: 'donor' | 'recipient' | 'hospital' | 'admin';
  name: string;
  email: string;
  phone?: string;
  isActive: boolean;
  createdAt: string;
}

export interface Donor {
  address: string;
  fullName: string;
  age: number;
  bloodType: string;
  organTypes: string[];
  healthCardCID: string;
  isActive: boolean;
  consentGiven: boolean;
  registrationTimestamp: number;
  accessRules: string;
  emergencyContact: string;
}

export interface Recipient {
  address: string;
  fullName: string;
  age: number;
  bloodType: string;
  requiredOrganType: string;
  urgencyScore: number;
  registrationTimestamp: number;
  isActive: boolean;
  healthCardCID: string;
}

export interface Organ {
  organId: number;
  donor: string;
  organType: string;
  bloodType: string;
  harvestTimestamp: number;
  expiryTimestamp: number;
  status: OrganStatus;
  assignedRecipient: string;
  viabilityScore: string;
  transportDocCID: string;
  currentCustodian: string;
  location: string;
}

export enum OrganStatus {
  AVAILABLE = 0,
  MATCHED = 1,
  IN_TRANSIT = 2,
  TRANSPLANTED = 3,
  EXPIRED = 4,
  REJECTED = 5
}

export interface Checkpoint {
  checkpointId: number;
  organId: number;
  checkpointType: CheckpointType;
  custodian: string;
  location: string;
  timestamp: number;
  notes: string;
  documentCID: string;
  verified: boolean;
  verifiedBy: string;
}

export enum CheckpointType {
  HARVEST = 0,
  PICKUP = 1,
  TRANSIT_START = 2,
  CUSTOMS_CHECK = 3,
  HANDOVER = 4,
  ARRIVAL = 5,
  DELIVERY = 6,
  TRANSPLANT_START = 7,
  TRANSPLANT_COMPLETE = 8
}

export interface TokenTransaction {
  id: string;
  address: string;
  amount: number;
  type: 'earned' | 'redeemed';
  reason?: string;
  rewardType?: string;
  timestamp: string;
  txHash?: string;
}

export interface TransportRoute {
  organId: number;
  startCustodian: string;
  endCustodian: string;
  startLocation: string;
  endLocation: string;
  estimatedDuration: number;
  actualDuration: number;
  transportMode: string;
  completed: boolean;
}
