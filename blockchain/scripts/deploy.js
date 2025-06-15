const { ethers } = require("hardhat");
const fs = require('fs');
const path = require('path');

async function main() {
    const [deployer, donor1, donor2, recipient1, recipient2] = await ethers.getSigners();
    console.log('Deploying contracts with the account:', deployer.address);
    console.log('Additional test accounts available:', {
        donor1: donor1.address,
        donor2: donor2.address,
        recipient1: recipient1.address,
        recipient2: recipient2.address
    });

    const balance = await deployer.provider.getBalance(deployer.address);
    console.log('Account balance:', ethers.formatEther(balance));

    // Deploy DonorConsent
    console.log('\n=== Deploying DonorConsent ===');
    const DonorConsent = await ethers.getContractFactory('DonorConsent');
    const donorConsent = await DonorConsent.deploy();
    await donorConsent.waitForDeployment();
    const donorConsentAddress = await donorConsent.getAddress();
    console.log('DonorConsent deployed to:', donorConsentAddress);

    // Deploy OrganLifecycle
    console.log('\n=== Deploying OrganLifecycle ===');
    const OrganLifecycle = await ethers.getContractFactory('OrganLifecycle');
    const organLifecycle = await OrganLifecycle.deploy();
    await organLifecycle.waitForDeployment();
    const organLifecycleAddress = await organLifecycle.getAddress();
    console.log('OrganLifecycle deployed to:', organLifecycleAddress);

    // Deploy LifeToken
    console.log('\n=== Deploying LifeToken ===');
    const LifeToken = await ethers.getContractFactory('LifeToken');
    const lifeToken = await LifeToken.deploy();
    await lifeToken.waitForDeployment();
    const lifeTokenAddress = await lifeToken.getAddress();
    console.log('LifeToken deployed to:', lifeTokenAddress);

    // Deploy ChainOfCustody
    console.log('\n=== Deploying ChainOfCustody ===');
    const ChainOfCustody = await ethers.getContractFactory('ChainOfCustody');
    const chainOfCustody = await ChainOfCustody.deploy();
    await chainOfCustody.waitForDeployment();
    const chainOfCustodyAddress = await chainOfCustody.getAddress();
    console.log('ChainOfCustody deployed to:', chainOfCustodyAddress);

    // Save contract addresses and ABIs for integration
    const contractData = {
        addresses: {
            DonorConsent: donorConsentAddress,
            OrganLifecycle: organLifecycleAddress,
            LifeToken: lifeTokenAddress,
            ChainOfCustody: chainOfCustodyAddress
        },
        abis: {
            DonorConsent: DonorConsent.interface.formatJson(),
            OrganLifecycle: OrganLifecycle.interface.formatJson(),
            LifeToken: LifeToken.interface.formatJson(),
            ChainOfCustody: ChainOfCustody.interface.formatJson()
        },
        networkInfo: {
            name: 'localhost',
            chainId: 31337,
            rpcUrl: 'http://127.0.0.1:8545'
        },
        deployedAt: new Date().toISOString()
    };

    // Save to multiple locations for easy access
    const contractsFile = 'deployed-contracts.json';
    const integrationFile = '../integration-contracts.json';
    
    fs.writeFileSync(contractsFile, JSON.stringify(contractData, null, 2));
    fs.writeFileSync(integrationFile, JSON.stringify(contractData, null, 2));

    // Also save simplified ABI files for easier access
    const abiDir = './abis';
    if (!fs.existsSync(abiDir)) {
        fs.mkdirSync(abiDir, { recursive: true });
    }

    fs.writeFileSync(path.join(abiDir, 'DonorConsent.json'), JSON.stringify(JSON.parse(DonorConsent.interface.formatJson()), null, 2));
    fs.writeFileSync(path.join(abiDir, 'OrganLifecycle.json'), JSON.stringify(JSON.parse(OrganLifecycle.interface.formatJson()), null, 2));
    fs.writeFileSync(path.join(abiDir, 'LifeToken.json'), JSON.stringify(JSON.parse(LifeToken.interface.formatJson()), null, 2));
    fs.writeFileSync(path.join(abiDir, 'ChainOfCustody.json'), JSON.stringify(JSON.parse(ChainOfCustody.interface.formatJson()), null, 2));

    console.log('\n=== Deployment Summary ===');
    console.log('✅ Contract addresses saved to:', contractsFile);
    console.log('✅ Integration data saved to:', integrationFile);
    console.log('✅ ABI files saved to:', abiDir);
    console.log('✅ All contracts deployed successfully!');

    // **NEW: POPULATE CONTRACTS WITH TEST DATA**
    console.log('\n=== Populating Contracts with Test Data ===');
    
    try {
        // Sample IPFS CIDs (you can replace these with actual CIDs from your uploads)
        const sampleHealthCIDs = [
            "QmVHDsiDNzvnf4nQZ857mb89iP9d8MJcbgVuZqEYU5w88W", // Use actual CIDs from your IPFS uploads
            "QmdQKtNh9dQLh2cfkz5ZXpU9CnX9jQMLxKm6ccvJLagYHD",
            "Qmeqpm7ePaFGma7m2PjTeYduyGCz8z8fR1E9EG22K6PoH3"
        ];

        // 1. Register Test Donors
        console.log('\n1️⃣ Registering Test Donors...');
        
        // Donor 1: Alice Johnson (Heart & Liver donor)
        await donorConsent.connect(donor1).registerDonor(
            "Alice Johnson",
            28,
            "O+",
            ["heart", "liver"],
            sampleHealthCIDs[0]
        );
        console.log('✅ Donor 1 registered:', donor1.address, '- Alice Johnson');

        // Donor 2: Bob Smith (Kidney donor)
        await donorConsent.connect(donor2).registerDonor(
            "Bob Smith",
            35,
            "A-",
            ["kidney"],
            sampleHealthCIDs[1]
        );
        console.log('✅ Donor 2 registered:', donor2.address, '- Bob Smith');

        // Donor 3: Demo Donor (using deployer account)
        await donorConsent.connect(deployer).registerDonor(
            "Demo Donor",
            30,
            "B+",
            ["liver", "pancreas"],
            sampleHealthCIDs[2]
        );
        console.log('✅ Donor 3 registered:', deployer.address, '- Demo Donor');

        // Update family consent for all donors
        await donorConsent.connect(donor1).updateConsent(true);
        await donorConsent.connect(donor2).updateConsent(true);
        await donorConsent.connect(deployer).updateConsent(true);
        console.log('✅ Family consent updated for all donors');

        // 2. Register Test Recipients
        console.log('\n2️⃣ Registering Test Recipients...');
        
        // Recipient 1: Charlie Brown (Heart recipient)
        await organLifecycle.connect(recipient1).registerRecipient(
            "Charlie Brown",
            "O+",
            "heart",
            95 // High urgency
        );
        console.log('✅ Recipient 1 registered:', recipient1.address, '- Charlie Brown (Heart)');

        // Recipient 2: Diana Prince (Kidney recipient)
        await organLifecycle.connect(recipient2).registerRecipient(
            "Diana Prince",
            "A-",
            "kidney",
            85 // Medium-high urgency
        );
        console.log('✅ Recipient 2 registered:', recipient2.address, '- Diana Prince (Kidney)');

        // Recipient 3: Demo Recipient (Liver recipient)
        await organLifecycle.registerRecipient(
            "Demo Recipient",
            "B+",
            "liver",
            75 // Medium urgency
        );
        console.log('✅ Recipient 3 registered:', deployer.address, '- Demo Recipient (Liver)');

        // 3. Register Sample Organs
        console.log('\n3️⃣ Registering Sample Organs...');
        
        // Register heart from donor1
        const heartTx = await organLifecycle.registerOrgan(
            donor1.address,
            "heart",
            12 // 12 hours viability
        );
        console.log('✅ Heart organ registered from Alice Johnson');

        // Register kidney from donor2
        const kidneyTx = await organLifecycle.registerOrgan(
            donor2.address,
            "kidney",
            24 // 24 hours viability
        );
        console.log('✅ Kidney organ registered from Bob Smith');

        // Register liver from deployer
        const liverTx = await organLifecycle.registerOrgan(
            deployer.address,
            "liver",
            16 // 16 hours viability
        );
        console.log('✅ Liver organ registered from Demo Donor');

        // 4. Setup LifeToken Rewards
        console.log('\n4️⃣ Setting up LifeToken Rewards...');
        
        // Authorize deployer to mint tokens for rewards
        await lifeToken.authorizeMinter(deployer.address);
        console.log('✅ Deployer authorized as token minter');

        // Reward donors for registration
        await lifeToken.rewardDonorRegistration(donor1.address);
        await lifeToken.rewardDonorRegistration(donor2.address);
        await lifeToken.rewardDonorRegistration(deployer.address);
        console.log('✅ Registration rewards distributed to all donors');

        // 5. Verify Test Data
        console.log('\n5️⃣ Verifying Test Data...');
        
        const donorCount = await donorConsent.getDonorCount();
        const allRecipients = await organLifecycle.getAllRecipients();
        
        console.log(`✅ Total donors registered: ${donorCount}`);
        console.log(`✅ Total recipients registered: ${allRecipients.length}`);

        // Get specific donor data to verify
        const donor1Data = await donorConsent.getDonor(donor1.address);
        const recipient1Data = await organLifecycle.getRecipient(recipient1.address);
        
        console.log(`✅ Sample donor verification: ${donor1Data[1]} (${donor1Data[3]}) - Organs: ${donor1Data[4]}`);
        console.log(`✅ Sample recipient verification: ${recipient1Data[1]} (${recipient1Data[2]}) - Needs: ${recipient1Data[3]}`);

        // 6. Log Chain of Custody Events
        console.log('\n6️⃣ Logging Chain of Custody Events...');
        
        await chainOfCustody.logCustodyEvent(
            0, // First organ (heart)
            0, // Pickup event
            "City General Hospital OR-3",
            "Heart organ harvested and prepared for transport",
            "QmSampleTransportDoc123"
        );
        
        await chainOfCustody.logCustodyEvent(
            1, // Second organ (kidney)
            0, // Pickup event
            "Metro Medical Center OR-2",
            "Kidney organ harvested and prepared for transport",
            "QmSampleTransportDoc456"
        );
        
        console.log('✅ Chain of custody events logged for sample organs');

        console.log('\n🎉 TEST DATA POPULATION COMPLETE!');
        console.log('📊 Summary:');
        console.log(`   - ${donorCount} donors registered and active`);
        console.log(`   - ${allRecipients.length} recipients registered and waiting`);
        console.log('   - 3 organs available for matching');
        console.log('   - Chain of custody tracking enabled');
        console.log('   - Token rewards system active');

    } catch (error) {
        console.log('⚠️ Error populating test data:', error.message);
        console.log('💡 Contracts deployed successfully, but test data failed');
        console.log('💡 You can manually add test data later using the admin scripts');
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
