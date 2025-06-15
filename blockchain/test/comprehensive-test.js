const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("🏥 LifeConnect Comprehensive Testing Suite", function () {
    let donorConsent, organLifecycle, lifeToken, chainOfCustody;
    let owner, donor1, donor2, recipient1, recipient2, hospital, transport;
    let contractAddresses = {};

    before(async function () {
        console.log("\n🚀 Setting up LifeConnect Test Environment...\n");
        
        // Get signers
        [owner, donor1, donor2, recipient1, recipient2, hospital, transport] = await ethers.getSigners();
        
        console.log("👥 Test Accounts:");
        console.log("   Owner:", owner.address);
        console.log("   Donor1:", donor1.address);
        console.log("   Donor2:", donor2.address);
        console.log("   Recipient1:", recipient1.address);
        console.log("   Recipient2:", recipient2.address);
        console.log("   Hospital:", hospital.address);
        console.log("   Transport:", transport.address);

        // Deploy all contracts
        console.log("\n📜 Deploying Smart Contracts...");
        
        const DonorConsent = await ethers.getContractFactory("DonorConsent");
        donorConsent = await DonorConsent.deploy();
        await donorConsent.waitForDeployment();
        contractAddresses.DonorConsent = await donorConsent.getAddress();

        const OrganLifecycle = await ethers.getContractFactory("OrganLifecycle");
        organLifecycle = await OrganLifecycle.deploy();
        await organLifecycle.waitForDeployment();
        contractAddresses.OrganLifecycle = await organLifecycle.getAddress();

        const LifeToken = await ethers.getContractFactory("LifeToken");
        lifeToken = await LifeToken.deploy();
        await lifeToken.waitForDeployment();
        contractAddresses.LifeToken = await lifeToken.getAddress();

        const ChainOfCustody = await ethers.getContractFactory("ChainOfCustody");
        chainOfCustody = await ChainOfCustody.deploy();
        await chainOfCustody.waitForDeployment();
        contractAddresses.ChainOfCustody = await chainOfCustody.getAddress();

        console.log("✅ All contracts deployed successfully!");
        console.log("📋 Contract Addresses:", contractAddresses);
        
        // Authorize minting for testing
        await lifeToken.authorizeMinter(hospital.address);
        await lifeToken.authorizeMinter(owner.address);
    });

    describe("🔐 1. Donor Registration & Consent Management", function () {
        it("Should register multiple donors with different profiles", async function () {
            console.log("\n🧑‍⚕️ Testing Donor Registration...");
            
            // Register Donor 1 - Heart & Liver donor
            await donorConsent.connect(donor1).registerDonor(
                "Alice Johnson",
                28,
                "O+",
                ["heart", "liver"],
                "QmHealthCard1ABC123"
            );

            // Register Donor 2 - Kidney donor
            await donorConsent.connect(donor2).registerDonor(
                "Bob Smith", 
                35,
                "A+",
                ["kidney"],
                "QmHealthCard2DEF456"
            );

            // Verify registrations
            const donor1Data = await donorConsent.getDonor(donor1.address);
            const donor2Data = await donorConsent.getDonor(donor2.address);

            expect(donor1Data.name).to.equal("Alice Johnson");
            expect(donor1Data.bloodType).to.equal("O+");
            expect(donor1Data.organTypes.length).to.equal(2);
            
            expect(donor2Data.name).to.equal("Bob Smith");
            expect(donor2Data.bloodType).to.equal("A+");
            expect(donor2Data.organTypes.length).to.equal(1);

            console.log("✅ Donor registration successful");
            console.log("   Donor1:", donor1Data.name, "- Organs:", donor1Data.organTypes);
            console.log("   Donor2:", donor2Data.name, "- Organs:", donor2Data.organTypes);
        });

        it("Should manage consent updates", async function () {
            console.log("\n📝 Testing Consent Management...");
            
            // Update family consent
            await donorConsent.connect(donor1).updateConsent(true);
            await donorConsent.connect(donor2).updateConsent(true);

            const donor1Data = await donorConsent.getDonor(donor1.address);
            const donor2Data = await donorConsent.getDonor(donor2.address);

            expect(donor1Data.familyConsent).to.be.true;
            expect(donor2Data.familyConsent).to.be.true;
            
            console.log("✅ Family consent granted for both donors");
        });

        it("Should reward donor registration with LifeTokens", async function () {
            console.log("\n🪙 Testing Token Rewards...");
            
            // Reward donors for registration
            await lifeToken.connect(hospital).rewardDonorRegistration(donor1.address);
            await lifeToken.connect(hospital).rewardDonorRegistration(donor2.address);

            const donor1Balance = await lifeToken.balanceOf(donor1.address);
            const donor2Balance = await lifeToken.balanceOf(donor2.address);

            expect(donor1Balance).to.equal(ethers.parseEther("100"));
            expect(donor2Balance).to.equal(ethers.parseEther("100"));
            
            console.log("✅ Registration rewards distributed");
            console.log(`   Donor1 balance: ${ethers.formatEther(donor1Balance)} LIFE`);
            console.log(`   Donor2 balance: ${ethers.formatEther(donor2Balance)} LIFE`);
        });
    });

    describe("🫀 2. Organ Lifecycle Management", function () {
        let heartOrganId, kidneyOrganId;

        it("Should register recipients", async function () {
            console.log("\n🏥 Registering Recipients...");
            
            // Register recipients
            await organLifecycle.connect(recipient1).registerRecipient(
                "Charlie Brown",
                "O+", 
                "heart",
                95 // High urgency
            );

            await organLifecycle.connect(recipient2).registerRecipient(
                "Diana Prince",
                "A+",
                "kidney", 
                75 // Medium urgency
            );

            const recipient1Data = await organLifecycle.getRecipient(recipient1.address);
            const recipient2Data = await organLifecycle.getRecipient(recipient2.address);

            expect(recipient1Data.name).to.equal("Charlie Brown");
            expect(recipient1Data.requiredOrgan).to.equal("heart");
            expect(recipient1Data.urgencyScore).to.equal(95);

            console.log("✅ Recipients registered successfully");
            console.log("   Recipient1:", recipient1Data.name, "needs", recipient1Data.requiredOrgan);
            console.log("   Recipient2:", recipient2Data.name, "needs", recipient2Data.requiredOrgan);
        });

        it("Should register organs and track lifecycle", async function () {
            console.log("\n🫀 Registering Organs...");
            
            // Register heart from donor1
            const heartTx = await organLifecycle.connect(hospital).registerOrgan(
                donor1.address,
                "heart",
                12 // 12 hours viability
            );

            // Register kidney from donor2  
            const kidneyTx = await organLifecycle.connect(hospital).registerOrgan(
                donor2.address,
                "kidney",
                24 // 24 hours viability
            );

            // Get organ IDs from events
            const heartReceipt = await heartTx.wait();
            const kidneyReceipt = await kidneyTx.wait();
            
            heartOrganId = 0; // First organ registered
            kidneyOrganId = 1; // Second organ registered

            const heartOrgan = await organLifecycle.getOrgan(heartOrganId);
            const kidneyOrgan = await organLifecycle.getOrgan(kidneyOrganId);

            expect(heartOrgan.organType).to.equal("heart");
            expect(heartOrgan.donor).to.equal(donor1.address);
            expect(Number(heartOrgan.status)).to.equal(0); // Available

            console.log("✅ Organs registered successfully");
            console.log(`   Heart (ID: ${heartOrganId}) from ${heartOrgan.donor}`);
            console.log(`   Kidney (ID: ${kidneyOrganId}) from ${kidneyOrgan.donor}`);
        });

        it("Should match organs with recipients", async function () {
            console.log("\n🎯 Testing AI Organ Matching...");
            
            // Match heart with recipient1 (AI score: 95)
            await organLifecycle.connect(hospital).matchOrgan(
                heartOrganId,
                recipient1.address,
                95
            );

            // Match kidney with recipient2 (AI score: 88)
            await organLifecycle.connect(hospital).matchOrgan(
                kidneyOrganId,
                recipient2.address,
                88
            );

            const heartOrgan = await organLifecycle.getOrgan(heartOrganId);
            const kidneyOrgan = await organLifecycle.getOrgan(kidneyOrganId);

            expect(heartOrgan.matchedRecipient).to.equal(recipient1.address);
            expect(Number(heartOrgan.status)).to.equal(1); // Matched
            expect(heartOrgan.aiMatchScore).to.equal(95);

            console.log("✅ Organ matching completed");
            console.log(`   Heart matched with score: ${heartOrgan.aiMatchScore}`);
            console.log(`   Kidney matched with score: ${kidneyOrgan.aiMatchScore}`);
        });

        it("Should track transport phase", async function () {
            console.log("\n🚚 Testing Transport Tracking...");
            
            // Start transport for both organs
            await organLifecycle.connect(transport).startTransport(
                heartOrganId,
                "QmTransportDoc1XYZ789"
            );

            await organLifecycle.connect(transport).startTransport(
                kidneyOrganId,
                "QmTransportDoc2ABC123"
            );

            const heartOrgan = await organLifecycle.getOrgan(heartOrganId);
            const kidneyOrgan = await organLifecycle.getOrgan(kidneyOrganId);

            expect(Number(heartOrgan.status)).to.equal(2); // InTransit
            expect(heartOrgan.transportDocCID).to.equal("QmTransportDoc1XYZ789");

            console.log("✅ Transport started successfully");
            console.log(`   Heart status: InTransit`);
            console.log(`   Kidney status: InTransit`);
        });

        it("Should complete transplant process", async function () {
            console.log("\n⚕️ Testing Transplant Completion...");
            
            // Complete transplants
            await organLifecycle.connect(hospital).completeTransplant(heartOrganId);
            await organLifecycle.connect(hospital).completeTransplant(kidneyOrganId);

            const heartOrgan = await organLifecycle.getOrgan(heartOrganId);
            const kidneyOrgan = await organLifecycle.getOrgan(kidneyOrganId);

            expect(Number(heartOrgan.status)).to.equal(3); // Transplanted
            expect(Number(kidneyOrgan.status)).to.equal(3); // Transplanted

            console.log("✅ Transplants completed successfully");
            
            // Reward donors for successful donation
            await lifeToken.connect(hospital).rewardDonation(donor1.address);
            await lifeToken.connect(hospital).rewardDonation(donor2.address);

            const donor1FinalBalance = await lifeToken.balanceOf(donor1.address);
            const donor2FinalBalance = await lifeToken.balanceOf(donor2.address);

            console.log(`   Donor1 final balance: ${ethers.formatEther(donor1FinalBalance)} LIFE`);
            console.log(`   Donor2 final balance: ${ethers.formatEther(donor2FinalBalance)} LIFE`);
        });
    });

    describe("📋 3. Chain of Custody Tracking", function () {
        let heartOrganId = 0;

        it("Should log complete custody chain", async function () {
            console.log("\n📋 Testing Chain of Custody...");
            
            // Log pickup event
            await chainOfCustody.connect(hospital).logCustodyEvent(
                heartOrganId,
                0, // Pickup
                "City General Hospital OR-3",
                "Organ harvested and prepared for transport",
                "QmPickupDoc123"
            );

            // Log checkpoint
            await chainOfCustody.connect(transport).logCustodyEvent(
                heartOrganId,
                2, // Checkpoint
                "Highway Checkpoint A",
                "Temperature check: 4°C - Optimal",
                "QmCheckpoint123"
            );

            // Log delivery
            await chainOfCustody.connect(hospital).logCustodyEvent(
                heartOrganId,
                3, // Delivery
                "Metro Medical Center OR-1", 
                "Organ delivered and ready for transplant",
                "QmDelivery123"
            );

            // Verify custody chain
            const custodyChain = await chainOfCustody.getCustodyChain(heartOrganId);
            const eventCount = await chainOfCustody.getEventCount(heartOrganId);

            expect(eventCount).to.equal(3);
            expect(custodyChain[0].location).to.equal("City General Hospital OR-3");
            expect(custodyChain[1].location).to.equal("Highway Checkpoint A");
            expect(custodyChain[2].location).to.equal("Metro Medical Center OR-1");

            console.log("✅ Custody chain logged successfully");
            console.log(`   Total events logged: ${eventCount}`);
            custodyChain.forEach((event, index) => {
                console.log(`   Event ${index + 1}: ${event.location}`);
            });
        });

        it("Should handle emergency stops", async function () {
            console.log("\n🚨 Testing Emergency Procedures...");
            
            const kidneyOrganId = 1;
            
            // Simulate emergency stop
            await chainOfCustody.connect(transport).emergencyStop(
                kidneyOrganId,
                "Medical emergency - route diversion required"
            );

            const latestEvent = await chainOfCustody.getLatestEvent(kidneyOrganId);
            expect(Number(latestEvent.eventType)).to.equal(4); // Emergency

            console.log("✅ Emergency stop logged successfully");
            console.log(`   Emergency reason: ${latestEvent.notes}`);
        });
    });

    describe("📊 4. System Integration & Final Verification", function () {
        it("Should provide comprehensive system status", async function () {
            console.log("\n📊 Final System Status Report");
            
            // Get total donors and recipients
            const totalDonors = await donorConsent.getDonorCount();
            const allDonors = await donorConsent.getAllDonors();
            const allRecipients = await organLifecycle.getAllRecipients();
            
            // Get token distribution
            const totalSupply = await lifeToken.totalSupply();
            const owner1Balance = await lifeToken.balanceOf(donor1.address);
            const owner2Balance = await lifeToken.balanceOf(donor2.address);
            
            console.log("\n=== LIFECONNECT SYSTEM STATUS ===");
            console.log(`👥 Total Donors Registered: ${totalDonors}`);
            console.log(`🏥 Total Recipients Registered: ${allRecipients.length}`);
            console.log(`🪙 Total LIFE Tokens in circulation: ${ethers.formatEther(totalSupply)}`);
            console.log(`💰 Donor rewards distributed: ${ethers.formatEther(owner1Balance + owner2Balance)}`);
            
            // Verify all organs processed
            const heartOrgan = await organLifecycle.getOrgan(0);
            const kidneyOrgan = await organLifecycle.getOrgan(1);
            
            console.log(`🫀 Heart organ status: ${getStatusName(heartOrgan.status)}`);
            console.log(`🫘 Kidney organ status: ${getStatusName(kidneyOrgan.status)}`);
            
            expect(totalDonors).to.equal(2);
            expect(allRecipients.length).to.equal(2);
            expect(Number(heartOrgan.status)).to.equal(3); // Transplanted
            expect(Number(kidneyOrgan.status)).to.equal(3); // Transplanted
            
            console.log("\n✅ ALL SYSTEMS OPERATIONAL - READY FOR DEMO! 🎉");
        });
    });

    // Helper function to get status names
    function getStatusName(status) {
        const statuses = ["Available", "Matched", "InTransit", "Transplanted", "Expired"];
        return statuses[Number(status)];
    }
});
