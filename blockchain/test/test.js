const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("LifeConnect Contracts", function () {
    let donorConsent, organLifecycle, lifeToken, chainOfCustody;
    let owner, donor, recipient, hospital;

    beforeEach(async function () {
        [owner, donor, recipient, hospital] = await ethers.getSigners();

        // Deploy contracts
        const DonorConsent = await ethers.getContractFactory("DonorConsent");
        donorConsent = await DonorConsent.deploy();

        const OrganLifecycle = await ethers.getContractFactory("OrganLifecycle");
        organLifecycle = await OrganLifecycle.deploy();

        const LifeToken = await ethers.getContractFactory("LifeToken");
        lifeToken = await LifeToken.deploy();

        const ChainOfCustody = await ethers.getContractFactory("ChainOfCustody");
        chainOfCustody = await ChainOfCustody.deploy();
    });

    describe("DonorConsent", function () {
        it("Should register a donor", async function () {
            await donorConsent.connect(donor).registerDonor(
                "John Doe",
                25,
                "O+",
                ["heart", "liver"],
                "QmTestCID123"
            );

            const donorData = await donorConsent.getDonor(donor.address);
            expect(donorData.name).to.equal("John Doe");
            expect(donorData.age).to.equal(25);
            expect(donorData.bloodType).to.equal("O+");
        });
    });

    describe("LifeToken", function () {
        it("Should have correct initial supply", async function () {
            const totalSupply = await lifeToken.totalSupply();
            expect(totalSupply).to.equal(ethers.parseEther("1000000"));
        });

        it("Should reward donor registration", async function () {
            await lifeToken.rewardDonorRegistration(donor.address);
            const balance = await lifeToken.balanceOf(donor.address);
            expect(balance).to.equal(ethers.parseEther("100"));
        });
    });
});
