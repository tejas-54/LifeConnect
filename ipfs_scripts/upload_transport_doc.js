const pinataSDK = require('@pinata/sdk');
require("dotenv").config();

const pinata = new pinataSDK(process.env.PINATA_API_KEY, process.env.PINATA_SECRET_KEY);

const generateTransportDocument = (organInfo) => ({
    // Document Identity
    documentId: `TRANS_${Date.now()}`,
    organId: organInfo.organId || "ORG_001",
    transportId: `TRANSPORT_${Date.now()}`,
    
    // Organ Information
    organDetails: {
        type: organInfo.organType || "heart",
        harvestTime: organInfo.harvestTime || new Date().toISOString(),
        expiryTime: organInfo.expiryTime || new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
        viabilityWindow: "8 hours",
        currentStatus: "In Transit"
    },
    
    // Donor & Recipient
    donor: {
        id: organInfo.donorId || "DONOR_001",
        hospital: organInfo.donorHospital || "City General Hospital",
        location: "Downtown Medical District"
    },
    recipient: {
        id: organInfo.recipientId || "RECIPIENT_001",
        hospital: organInfo.recipientHospital || "Metro Medical Center", 
        location: "Uptown Medical Complex"
    },
    
    // Logistics & Route
    logistics: {
        pickupTime: new Date().toISOString(),
        estimatedDelivery: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(),
        actualDelivery: null,
        route: {
            origin: "City General Hospital, Downtown",
            destination: "Metro Medical Center, Uptown", 
            distance: "15.7 km",
            estimatedDuration: "45 minutes",
            actualDuration: null,
            waypoints: [
                { location: "Highway Junction A", eta: new Date(Date.now() + 15 * 60 * 1000).toISOString() },
                { location: "Medical District Bridge", eta: new Date(Date.now() + 30 * 60 * 1000).toISOString() }
            ]
        },
        transportMethod: organInfo.transportMethod || "Medical Helicopter",
        priority: "Critical",
        courierDetails: {
            name: "Emergency Medical Transport",
            licenseNumber: "EMT-2025-447", 
            contactNumber: "+1-555-0199",
            driverName: "Dr. Michael Chen",
            medicalPersonnel: "Nurse Jennifer Lopez"
        }
    },
    
    // Real-time Monitoring
    monitoring: {
        temperatureLog: [
            { 
                timestamp: new Date().toISOString(), 
                temperature: "4°C", 
                location: "Origin Hospital",
                status: "Optimal"
            }
        ],
        gpsTracking: {
            currentLocation: { lat: 40.7128, lng: -74.0060 },
            speed: "85 km/h",
            lastUpdate: new Date().toISOString()
        },
        qualityMetrics: {
            vibrationLevel: "Minimal",
            humidityLevel: "65%", 
            oxygenSaturation: "98%"
        }
    },
    
    // Chain of Custody
    custodyChain: [
        {
            timestamp: new Date().toISOString(),
            handler: "Dr. Sarah Johnson",
            role: "Harvesting Surgeon",
            action: "Organ harvested and prepared for transport",
            location: "City General Hospital OR-3",
            signature: "SJ_2025_001"
        }
    ],
    
    // Metadata
    metadata: {
        created: new Date().toISOString(),
        version: "2.0",
        status: "Active",
        ipfsHash: null,
        lastUpdated: new Date().toISOString()
    }
});

async function uploadTransportDocument(organInfo = {}) {
    try {
        console.log('🚚 Generating transport document...');
        const transportData = generateTransportDocument(organInfo);
        
        console.log('📤 Uploading transport document to IPFS...');
        
        const options = {
            pinataMetadata: {
                name: `TransportDoc_${transportData.documentId}`,
                keyvalues: {
                    organId: transportData.organId,
                    organType: transportData.organDetails.type,
                    transportId: transportData.transportId,
                    priority: transportData.logistics.priority,
                    timestamp: transportData.metadata.created
                }
            },
            pinataOptions: {
                cidVersion: 0
            }
        };
        
        const result = await pinata.pinJSONToIPFS(transportData, options);
        
        console.log('✅ Transport document uploaded successfully!');
        console.log('📋 IPFS CID:', result.IpfsHash);
        console.log('🔗 Gateway URL:', `https://${process.env.PINATA_GATEWAY}/ipfs/${result.IpfsHash}`);
        
        return {
            cid: result.IpfsHash,
            url: `https://${process.env.PINATA_GATEWAY}/ipfs/${result.IpfsHash}`,
            size: result.PinSize,
            transportData: transportData
        };
        
    } catch (error) {
        console.error('❌ Error uploading transport document:', error.message);
        throw error;
    }
}

async function retrieveTransportDocument(cid) {
    try {
        console.log(`📥 Retrieving transport document with CID: ${cid}`);
        
        const response = await fetch(`https://${process.env.PINATA_GATEWAY}/ipfs/${cid}`);
        const transportData = await response.json();
        
        console.log('✅ Transport document retrieved successfully!');
        console.log('🚚 Transport ID:', transportData.transportId);
        console.log('🫀 Organ Type:', transportData.organDetails.type);
        console.log('📍 Route:', `${transportData.logistics.route.origin} → ${transportData.logistics.route.destination}`);
        
        return transportData;
        
    } catch (error) {
        console.error('❌ Error retrieving transport document:', error.message);
        throw error;
    }
}

// CLI Interface
async function main() {
    const action = process.argv[2];
    
    if (action === 'upload') {
        try {
            const sampleOrgan = {
                organId: "ORG_001",
                organType: "heart",
                donorId: "DONOR_001", 
                recipientId: "RECIPIENT_001",
                transportMethod: "Medical Helicopter"
            };
            
            const result = await uploadTransportDocument(sampleOrgan);
            console.log('\n📊 Upload Result:', JSON.stringify(result, null, 2));
        } catch (error) {
            console.error('Upload failed:', error);
        }
    } else if (action === 'retrieve') {
        const cid = process.argv[3];
        if (!cid) {
            console.error('❌ Please provide CID: node upload_transport_doc.js retrieve <CID>');
            return;
        }
        
        try {
            const data = await retrieveTransportDocument(cid);
            console.log('\n📋 Transport Summary:');
            console.log('   Document ID:', data.documentId);
            console.log('   Organ Type:', data.organDetails.type);
            console.log('   Distance:', data.logistics.route.distance);
            console.log('   Status:', data.metadata.status);
        } catch (error) {
            console.error('Retrieval failed:', error);
        }
    } else {
        console.log('Usage:');
        console.log('  Upload: node upload_transport_doc.js upload');
        console.log('  Retrieve: node upload_transport_doc.js retrieve <CID>');
    }
}

module.exports = {
    uploadTransportDocument,
    retrieveTransportDocument,
    generateTransportDocument
};

if (require.main === module) {
    main();
}
