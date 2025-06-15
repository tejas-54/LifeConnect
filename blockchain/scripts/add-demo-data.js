const { ethers } = require("hardhat");

async function addDemoData() {
    console.log('🎭 Adding Quick Demo Data to LifeConnect');
    
    const [deployer] = await ethers.getSigners();
    
    // Load contract addresses
    const contractData = require('../deployed-contracts.json');
    const donorConsent = await ethers.getContractAt("DonorConsent", contractData.addresses.DonorConsent);
    const organLifecycle = await ethers.getContractAt("OrganLifecycle", contractData.addresses.OrganLifecycle);

    // Use your actual IPFS CIDs from recent uploads
    const recentHealthCID = "bafkreif2oa4hkgl22llnvpg3vztxvkqymlpijq232juta6t36q72xlfiq4";

    try {
        // Add demo donor
        await donorConsent.registerDonor(
            "Demo Donor",
            30,
            "O+",
            ["heart"],
            recentHealthCID
        );
        
        await donorConsent.updateConsent(true);
        
        // Add demo recipient
        await organLifecycle.registerRecipient(
            "Demo Recipient",
            "O+",
            "heart",
            90
        );

        console.log('✅ Demo data added successfully!');
        
        // Verify
        const donorCount = await donorConsent.getDonorCount();
        const recipients = await organLifecycle.getAllRecipients();
        console.log(`📊 Donors: ${donorCount}, Recipients: ${recipients.length}`);
        
    } catch (error) {
        if (error.message.includes('Already registered')) {
            console.log('💡 Demo accounts already registered');
        } else {
            console.error('❌ Error:', error.message);
        }
    }
}

addDemoData();
