const { ethers } = require("hardhat");

async function main() {
    console.log('🧪 Populating LifeConnect Contracts with Test Data');
    console.log('=' * 60);

    const [deployer, donor1, donor2, recipient1, recipient2] = await ethers.getSigners();

    // Load deployed contract addresses
    const contractData = require('../deployed-contracts.json');
    
    if (!contractData || !contractData.addresses) {
        throw new Error('❌ Contract deployment data not found. Please deploy contracts first.');
    }

    // Connect to deployed contracts
    const donorConsent = await ethers.getContractAt("DonorConsent", contractData.addresses.DonorConsent);
    const organLifecycle = await ethers.getContractAt("OrganLifecycle", contractData.addresses.OrganLifecycle);
    const lifeToken = await ethers.getContractAt("LifeToken", contractData.addresses.LifeToken);
    const chainOfCustody = await ethers.getContractAt("ChainOfCustody", contractData.addresses.ChainOfCustody);

    console.log('✅ Connected to deployed contracts');

    // Check if data already exists
    const existingDonorCount = await donorConsent.getDonorCount();
    const existingRecipients = await organLifecycle.getAllRecipients();

    if (existingDonorCount > 0) {
        console.log(`⚠️ Found ${existingDonorCount} existing donors and ${existingRecipients.length} recipients`);
        console.log('💡 Adding additional test data...');
    } else {
        console.log('📋 No existing data found. Adding fresh test data...');
    }

    // Sample IPFS CIDs (replace with real ones from your uploads)
    const sampleHealthCIDs = [
        "bafkreif2oa4hkgl22llnvpg3vztxvkqymlpijq232juta6t36q72xlfiq4", // Use your actual uploaded CIDs
        "bafkreidjjwhqy2bowryfnylfgkknro3zwvtdjidlxhvmpwgv66cykzz5pi",
        "QmVHDsiDNzvnf4nQZ857mb89iP9d8MJcbgVuZqEYU5w88W"
    ];

    try {
        // Add test donors
        console.log('\n1️⃣ Adding Test Donors...');
        
        await donorConsent.connect(donor1).registerDonor(
            "Alice Johnson",
            28,
            "O+",
            ["heart", "liver"],
            sampleHealthCIDs[0]
        );
        console.log(`✅ Donor registered: Alice Johnson (${donor1.address})`);

        await donorConsent.connect(donor2).registerDonor(
            "Bob Smith",
            35,
            "A-",
            ["kidney"],
            sampleHealthCIDs[1]
        );
        console.log(`✅ Donor registered: Bob Smith (${donor2.address})`);

        // Update consent
        await donorConsent.connect(donor1).updateConsent(true);
        await donorConsent.connect(donor2).updateConsent(true);
        console.log('✅ Family consent granted for all donors');

        // Add test recipients
        console.log('\n2️⃣ Adding Test Recipients...');
        
        await organLifecycle.connect(recipient1).registerRecipient(
            "Charlie Brown",
            "O+",
            "heart",
            95
        );
        console.log(`✅ Recipient registered: Charlie Brown (${recipient1.address})`);

        await organLifecycle.connect(recipient2).registerRecipient(
            "Diana Prince",
            "A-",
            "kidney",
            85
        );
        console.log(`✅ Recipient registered: Diana Prince (${recipient2.address})`);

        // Add more recipients for better testing
        await organLifecycle.registerRecipient(
            "Eva Davis",
            "B+",
            "liver",
            75
        );
        console.log(`✅ Recipient registered: Eva Davis (${deployer.address})`);

        // Register organs
        console.log('\n3️⃣ Registering Available Organs...');
        
        await organLifecycle.registerOrgan(donor1.address, "heart", 12);
        console.log('✅ Heart organ registered');

        await organLifecycle.registerOrgan(donor2.address, "kidney", 24);
        console.log('✅ Kidney organ registered');

        // Setup token rewards
        console.log('\n4️⃣ Setting up Token Rewards...');
        
        await lifeToken.authorizeMinter(deployer.address);
        await lifeToken.rewardDonorRegistration(donor1.address);
        await lifeToken.rewardDonorRegistration(donor2.address);
        console.log('✅ Token rewards distributed');

        // Final verification
        const finalDonorCount = await donorConsent.getDonorCount();
        const finalRecipients = await organLifecycle.getAllRecipients();
        
        console.log('\n🎉 TEST DATA POPULATION COMPLETE!');
        console.log(`✅ Total donors: ${finalDonorCount}`);
        console.log(`✅ Total recipients: ${finalRecipients.length}`);
        console.log('✅ Contracts ready for integration testing!');

    } catch (error) {
        console.error('❌ Error adding test data:', error.message);
        
        // If registration fails due to already being registered, that's okay
        if (error.message.includes('Already registered')) {
            console.log('💡 Some accounts already registered - this is normal');
        } else {
            throw error;
        }
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
