const pinataSDK = require('@pinata/sdk');
const fs = require("fs");
require("dotenv").config();

// Initialize Pinata SDK with API keys
const pinata = new pinataSDK(process.env.PINATA_API_KEY, process.env.PINATA_SECRET_KEY);

// Sample comprehensive health data
const generateHealthCardData = (donorInfo) => ({
    // Patient Identity
    patientId: donorInfo.id || `DONOR_${Date.now()}`,
    name: donorInfo.name || "John Doe",
    age: donorInfo.age || 35,
    bloodType: donorInfo.bloodType || "O+",
    gender: donorInfo.gender || "Male",
    
    // Medical History
    medicalHistory: {
        allergies: donorInfo.allergies || ["None"],
        medications: donorInfo.medications || ["None"],
        surgeries: donorInfo.surgeries || ["Appendectomy - 2015"],
        chronicConditions: donorInfo.chronicConditions || [],
        familyHistory: {
            heartDisease: false,
            diabetes: false,
            cancer: false
        }
    },
    
    // Organ Data
    organData: {
        availableOrgans: donorInfo.organs || ["heart", "liver", "kidneys"],
        organHealth: {
            heart: "Excellent",
            liver: "Good", 
            kidneys: "Excellent",
            lungs: "Good",
            pancreas: "Good"
        },
        compatibilityData: {
            hlaTyping: "A1, A2; B7, B8; C1, C7; DR15, DR4; DQ6, DQ8",
            crossmatchResults: "Negative"
        }
    },
    
    // Laboratory Results
    labResults: {
        bloodTests: {
            hemoglobin: "14.5 g/dL",
            whiteBloodCells: "7,200/μL",
            platelets: "250,000/μL",
            creatinine: "1.0 mg/dL",
            alt: "25 U/L",
            ast: "22 U/L"
        },
        viralScreening: {
            hiv: "Negative",
            hepatitisB: "Negative", 
            hepatitisC: "Negative",
            cmv: "Negative",
            ebv: "Negative"
        },
        tissueTyping: {
            blood_group: donorInfo.bloodType || "O+",
            rh_factor: "Positive",
            hla_match_score: 95
        }
    },
    
    // Metadata
    timestamp: new Date().toISOString(),
    hospitalId: donorInfo.hospitalId || "HOSPITAL_001",
    doctorSignature: "Dr. Sarah Johnson, MD",
    version: "1.0",
    ipfsHash: null, // Will be filled after upload
    
    // Blockchain Integration
    blockchainData: {
        donorAddress: donorInfo.donorAddress || null,
        consentGiven: true,
        familyConsent: donorInfo.familyConsent || false
    }
});

async function uploadHealthCard(donorInfo = {}) {
    try {
        console.log('🏥 Generating health card data...');
        const healthData = generateHealthCardData(donorInfo);
        
        console.log('📤 Uploading health card to IPFS via Pinata...');
        
        // Create metadata for better organization
        const options = {
            pinataMetadata: {
                name: `HealthCard_${healthData.patientId}`,
                keyvalues: {
                    patientId: healthData.patientId,
                    bloodType: healthData.bloodType,
                    timestamp: healthData.timestamp,
                    version: healthData.version
                }
            },
            pinataOptions: {
                cidVersion: 0
            }
        };
        
        // Upload JSON to IPFS
        const result = await pinata.pinJSONToIPFS(healthData, options);
        
        console.log('✅ Health card uploaded successfully!');
        console.log('📋 IPFS CID:', result.IpfsHash);
        console.log('🔗 Gateway URL:', `https://${process.env.PINATA_GATEWAY}/ipfs/${result.IpfsHash}`);
        console.log('📊 File Size:', result.PinSize, 'bytes');
        console.log('⏰ Timestamp:', result.Timestamp);
        
        return {
            cid: result.IpfsHash,
            url: `https://${process.env.PINATA_GATEWAY}/ipfs/${result.IpfsHash}`,
            size: result.PinSize,
            timestamp: result.Timestamp,
            healthData: healthData
        };
        
    } catch (error) {
        console.error('❌ Error uploading health card:', error.message);
        throw error;
    }
}

async function retrieveHealthCard(cid) {
    try {
        console.log(`📥 Retrieving health card with CID: ${cid}`);
        
        const response = await fetch(`https://${process.env.PINATA_GATEWAY}/ipfs/${cid}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const healthData = await response.json();
        
        console.log('✅ Health card retrieved successfully!');
        console.log('👤 Patient:', healthData.name);
        console.log('🩸 Blood Type:', healthData.bloodType);
        console.log('🫀 Available Organs:', healthData.organData.availableOrgans.join(', '));
        
        return healthData;
        
    } catch (error) {
        console.error('❌ Error retrieving health card:', error.message);
        throw error;
    }
}

async function testConnection() {
    try {
        console.log('🔍 Testing Pinata connection...');
        const result = await pinata.testAuthentication();
        console.log('✅ Pinata connection successful!', result.message);
        return true;
    } catch (error) {
        console.error('❌ Pinata connection failed:', error.message);
        console.error('🔧 Check your PINATA_API_KEY and PINATA_SECRET_KEY in .env file');
        return false;
    }
}

// CLI Interface
async function main() {
    const action = process.argv[2];
    
    if (action === 'test') {
        await testConnection();
    } else if (action === 'upload') {
        try {
            // Sample donor info for demo
            const sampleDonor = {
                id: "DONOR_001",
                name: "Alice Johnson", 
                age: 28,
                bloodType: "O+",
                organs: ["heart", "liver"],
                donorAddress: "0x1234567890123456789012345678901234567890"
            };
            
            const result = await uploadHealthCard(sampleDonor);
            console.log('\n📊 Upload Result:', JSON.stringify(result, null, 2));
        } catch (error) {
            console.error('Upload failed:', error);
        }
    } else if (action === 'retrieve') {
        const cid = process.argv[3];
        if (!cid) {
            console.error('❌ Please provide CID: node upload_healthcard.js retrieve <CID>');
            return;
        }
        
        try {
            const data = await retrieveHealthCard(cid);
            console.log('\n📋 Retrieved Health Data:');
            console.log('   Patient ID:', data.patientId);
            console.log('   Name:', data.name);
            console.log('   Blood Type:', data.bloodType);
            console.log('   Available Organs:', data.organData.availableOrgans);
        } catch (error) {
            console.error('Retrieval failed:', error);
        }
    } else {
        console.log('Usage:');
        console.log('  Test connection: node upload_healthcard.js test');
        console.log('  Upload sample: node upload_healthcard.js upload');
        console.log('  Retrieve: node upload_healthcard.js retrieve <CID>');
    }
}

module.exports = {
    uploadHealthCard,
    retrieveHealthCard,
    generateHealthCardData,
    testConnection
};

if (require.main === module) {
    main();
}
