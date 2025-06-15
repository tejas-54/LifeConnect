const { ethers } = require("hardhat");

async function main() {
    console.log("🎬 LIFECONNECT HACKATHON DEMO - LIVE TESTING\n");
    
    // Get deployed contract addresses
    const fs = require('fs');
    let contractAddresses;
    
    try {
        contractAddresses = JSON.parse(fs.readFileSync('deployed-contracts.json', 'utf8'));
        console.log("📜 Loaded deployed contracts:", contractAddresses);
    } catch (error) {
        console.log("❌ Please deploy contracts first: npx hardhat run scripts/deploy.js --network localhost");
        return;
    }
    
    // Connect to deployed contracts
    const [owner, donor, recipient, hospital] = await ethers.getSigners();
    
    const donorConsent = await ethers.getContractAt("DonorConsent", contractAddresses.DonorConsent);
    const organLifecycle = await ethers.getContractAt("OrganLifecycle", contractAddresses.OrganLifecycle);
    const lifeToken = await ethers.getContractAt("LifeToken", contractAddresses.LifeToken);
    const chainOfCustody = await ethers.getContractAt("ChainOfCustody", contractAddresses.ChainOfCustody);
    
    console.log("\n🔗 Connected to deployed contracts successfully!");
    
    // Live demo sequence
    console.log("\n=== DEMO SEQUENCE START ===");
    
    // 1. Register a donor
    console.log("\n1️⃣ Registering new donor...");
    await donorConsent.connect(donor).registerDonor(
        "Demo Donor",
        30,
        "O+",
        ["heart"],
        "QmDemoHealthCard123"
    );
    console.log("✅ Donor registered successfully");
    
    // 2. Register recipient
    console.log("\n2️⃣ Registering recipient...");
    await organLifecycle.connect(recipient).registerRecipient(
        "Demo Recipient",
        "O+",
        "heart",
        90
    );
    console.log("✅ Recipient registered successfully");
    
    // 3. Register organ
    console.log("\n3️⃣ Registering organ...");
    await organLifecycle.connect(hospital).registerOrgan(
        donor.address,
        "heart",
        8
    );
    console.log("✅ Organ registered successfully");
    
    // 4. Match organ
    console.log("\n4️⃣ AI matching organ...");
    await organLifecycle.connect(hospital).matchOrgan(0, recipient.address, 92);
    console.log("✅ Organ matched with 92% compatibility");
    
    // 5. Start transport
    console.log("\n5️⃣ Starting transport...");
    await organLifecycle.connect(hospital).startTransport(0, "QmTransportDemo123");
    console.log("✅ Transport started");
    
    // 6. Log custody events
    console.log("\n6️⃣ Logging custody chain...");
    await chainOfCustody.connect(hospital).logCustodyEvent(
        0, 0, "Origin Hospital", "Organ prepared", "QmCustody1"
    );
    await chainOfCustody.connect(hospital).logCustodyEvent(
        0, 3, "Destination Hospital", "Organ delivered", "QmCustody2"
    );
    console.log("✅ Custody chain logged");
    
    // 7. Complete transplant
    console.log("\n7️⃣ Completing transplant...");
    await organLifecycle.connect(hospital).completeTransplant(0);
    console.log("✅ Transplant completed successfully");
    
    // 8. Reward donor
    console.log("\n8️⃣ Rewarding donor with LIFE tokens...");
    await lifeToken.authorizeMinter(hospital.address);
    await lifeToken.connect(hospital).rewardDonorRegistration(donor.address);
    await lifeToken.connect(hospital).rewardDonation(donor.address);
    
    const donorBalance = await lifeToken.balanceOf(donor.address);
    console.log(`✅ Donor rewarded with ${ethers.formatEther(donorBalance)} LIFE tokens`);
    
    console.log("\n🎉 DEMO SEQUENCE COMPLETED SUCCESSFULLY!");
    console.log("💡 All LifeConnect features working perfectly for hackathon presentation!");
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
