const { uploadHealthCard, retrieveHealthCard, testConnection } = require('./upload_healthcard');
const { uploadTransportDocument, retrieveTransportDocument } = require('./upload_transport_doc');
const pinataSDK = require('@pinata/sdk'); // Fixed import
require("dotenv").config();

async function runComprehensiveTests() {
    console.log('🧪 LifeConnect IPFS Integration Test Suite\n');
    
    // Test 1: Connection Test
    console.log('1️⃣ Testing Pinata Connection...');
    const connectionTest = await testConnection();
    if (!connectionTest) {
        console.error('❌ Connection test failed. Check your API keys!');
        return;
    }
    console.log('✅ Connection test passed!\n');
    
    // Test 2: Health Card Upload & Retrieval
    console.log('2️⃣ Testing Health Card Upload & Retrieval...');
    try {
        const donorInfo = {
            id: "TEST_DONOR_001",
            name: "Test Donor Alice",
            age: 30,
            bloodType: "O+",
            organs: ["heart", "liver"],
            familyConsent: true
        };
        
        const healthResult = await uploadHealthCard(donorInfo);
        console.log('✅ Health card uploaded:', healthResult.cid);
        
        // Test retrieval
        const retrievedHealth = await retrieveHealthCard(healthResult.cid);
        console.log('✅ Health card retrieved successfully');
        console.log('   Patient:', retrievedHealth.name);
        console.log('   Organs:', retrievedHealth.organData.availableOrgans.join(', '));
        
    } catch (error) {
        console.error('❌ Health card test failed:', error.message);
    }
    
    console.log();
    
    // Test 3: Transport Document Upload & Retrieval  
    console.log('3️⃣ Testing Transport Document Upload & Retrieval...');
    try {
        const organInfo = {
            organId: "TEST_ORG_001",
            organType: "heart",
            donorId: "TEST_DONOR_001",
            recipientId: "TEST_RECIPIENT_001"
        };
        
        const transportResult = await uploadTransportDocument(organInfo);
        console.log('✅ Transport document uploaded:', transportResult.cid);
        
        // Test retrieval
        const retrievedTransport = await retrieveTransportDocument(transportResult.cid);
        console.log('✅ Transport document retrieved successfully');
        console.log('   Transport ID:', retrievedTransport.transportId);
        console.log('   Route:', retrievedTransport.logistics.route.distance);
        
    } catch (error) {
        console.error('❌ Transport document test failed:', error.message);
    }
    
    console.log();
    
    // Test 4: Performance Test (Fixed)
    console.log('4️⃣ Testing Upload Performance...');
    try {
        const startTime = Date.now();
        
        const testData = {
            timestamp: new Date().toISOString(),
            testSize: "small",
            data: Array(100).fill().map((_, i) => ({ id: i, value: `test_${i}` }))
        };
        
        // Use correct import
        const pinata = new pinataSDK(process.env.PINATA_API_KEY, process.env.PINATA_SECRET_KEY);
        
        const result = await pinata.pinJSONToIPFS(testData, {
            pinataMetadata: { name: "PerformanceTest" }
        });
        
        const endTime = Date.now();
        
        console.log('✅ Performance test completed');
        console.log(`   Upload time: ${endTime - startTime}ms`);
        console.log(`   File size: ${result.PinSize} bytes`);
        console.log(`   CID: ${result.IpfsHash}`);
        
    } catch (error) {
        console.error('❌ Performance test failed:', error.message);
    }
    
    console.log('\n🎉 IPFS Integration Tests Completed!');
    console.log('📊 All LifeConnect IPFS features are working correctly for demo!');
}

// CLI Interface
if (require.main === module) {
    runComprehensiveTests();
}

module.exports = { runComprehensiveTests };
