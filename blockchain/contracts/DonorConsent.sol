// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DonorConsent {
    struct Donor {
        address donorAddress;
        string name;
        uint256 age;
        string bloodType;
        string[] organTypes;
        bool isActive;
        uint256 registrationTime;
        string healthCardCID; // IPFS CID for health records
        bool familyConsent;
    }

    mapping(address => Donor) public donors;
    mapping(address => bool) public isRegistered;
    address[] public donorList;
    
    event DonorRegistered(address indexed donor, string name, uint256 timestamp);
    event ConsentUpdated(address indexed donor, bool consent);
    event HealthCardUpdated(address indexed donor, string newCID);

    modifier onlyRegisteredDonor() {
        require(isRegistered[msg.sender], "Not a registered donor");
        _;
    }

    function registerDonor(
        string memory _name,
        uint256 _age,
        string memory _bloodType,
        string[] memory _organTypes,
        string memory _healthCardCID
    ) external {
        require(!isRegistered[msg.sender], "Already registered");
        require(_age >= 18, "Must be 18 or older");

        donors[msg.sender] = Donor({
            donorAddress: msg.sender,
            name: _name,
            age: _age,
            bloodType: _bloodType,
            organTypes: _organTypes,
            isActive: true,
            registrationTime: block.timestamp,
            healthCardCID: _healthCardCID,
            familyConsent: false
        });

        isRegistered[msg.sender] = true;
        donorList.push(msg.sender);

        emit DonorRegistered(msg.sender, _name, block.timestamp);
    }

    function updateConsent(bool _consent) external onlyRegisteredDonor {
        donors[msg.sender].familyConsent = _consent;
        emit ConsentUpdated(msg.sender, _consent);
    }

    function updateHealthCard(string memory _newCID) external onlyRegisteredDonor {
        donors[msg.sender].healthCardCID = _newCID;
        emit HealthCardUpdated(msg.sender, _newCID);
    }

    function getDonor(address _donorAddress) external view returns (Donor memory) {
        require(isRegistered[_donorAddress], "Donor not registered");
        return donors[_donorAddress];
    }

    function getAllDonors() external view returns (address[] memory) {
        return donorList;
    }

    function getDonorCount() external view returns (uint256) {
        return donorList.length;
    }
}
