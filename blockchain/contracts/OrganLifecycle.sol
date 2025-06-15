// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract OrganLifecycle {
    enum OrganStatus { Available, Matched, InTransit, Transplanted, Expired }
    
    struct Organ {
        uint256 organId;
        address donor;
        string organType;
        uint256 harvestTime;
        uint256 expiryTime;
        address matchedRecipient;
        OrganStatus status;
        string transportDocCID; // IPFS CID for transport documents
        uint256 aiMatchScore;
    }

    struct Recipient {
        address recipientAddress;
        string name;
        string bloodType;
        string requiredOrgan;
        uint256 urgencyScore;
        uint256 registrationTime;
        bool isActive;
    }

    mapping(uint256 => Organ) public organs;
    mapping(address => Recipient) public recipients;
    mapping(address => bool) public isRecipientRegistered;
    
    uint256 public organCounter;
    address[] public recipientList;

    event OrganRegistered(uint256 indexed organId, address indexed donor, string organType);
    event RecipientRegistered(address indexed recipient, string name, string requiredOrgan);
    event OrganMatched(uint256 indexed organId, address indexed recipient, uint256 matchScore);
    event OrganStatusUpdated(uint256 indexed organId, OrganStatus newStatus);
    event TransportStarted(uint256 indexed organId, string transportDocCID);

    modifier validOrgan(uint256 _organId) {
        require(_organId < organCounter, "Invalid organ ID");
        _;
    }

    function registerRecipient(
        string memory _name,
        string memory _bloodType,
        string memory _requiredOrgan,
        uint256 _urgencyScore
    ) external {
        require(!isRecipientRegistered[msg.sender], "Already registered");

        recipients[msg.sender] = Recipient({
            recipientAddress: msg.sender,
            name: _name,
            bloodType: _bloodType,
            requiredOrgan: _requiredOrgan,
            urgencyScore: _urgencyScore,
            registrationTime: block.timestamp,
            isActive: true
        });

        isRecipientRegistered[msg.sender] = true;
        recipientList.push(msg.sender);

        emit RecipientRegistered(msg.sender, _name, _requiredOrgan);
    }

    function registerOrgan(
        address _donor,
        string memory _organType,
        uint256 _expiryHours
    ) external returns (uint256) {
        uint256 organId = organCounter++;
        
        organs[organId] = Organ({
            organId: organId,
            donor: _donor,
            organType: _organType,
            harvestTime: block.timestamp,
            expiryTime: block.timestamp + (_expiryHours * 1 hours),
            matchedRecipient: address(0),
            status: OrganStatus.Available,
            transportDocCID: "",
            aiMatchScore: 0
        });

        emit OrganRegistered(organId, _donor, _organType);
        return organId;
    }

    function matchOrgan(
        uint256 _organId,
        address _recipient,
        uint256 _matchScore
    ) external validOrgan(_organId) {
        require(organs[_organId].status == OrganStatus.Available, "Organ not available");
        require(isRecipientRegistered[_recipient], "Recipient not registered");
        require(block.timestamp < organs[_organId].expiryTime, "Organ expired");

        organs[_organId].matchedRecipient = _recipient;
        organs[_organId].status = OrganStatus.Matched;
        organs[_organId].aiMatchScore = _matchScore;

        emit OrganMatched(_organId, _recipient, _matchScore);
    }

    function startTransport(uint256 _organId, string memory _transportDocCID) 
        external validOrgan(_organId) {
        require(organs[_organId].status == OrganStatus.Matched, "Organ not matched");
        
        organs[_organId].status = OrganStatus.InTransit;
        organs[_organId].transportDocCID = _transportDocCID;

        emit TransportStarted(_organId, _transportDocCID);
        emit OrganStatusUpdated(_organId, OrganStatus.InTransit);
    }

    function completeTransplant(uint256 _organId) external validOrgan(_organId) {
        require(organs[_organId].status == OrganStatus.InTransit, "Organ not in transit");
        require(block.timestamp < organs[_organId].expiryTime, "Organ expired");

        organs[_organId].status = OrganStatus.Transplanted;
        emit OrganStatusUpdated(_organId, OrganStatus.Transplanted);
    }

    function markExpired(uint256 _organId) external validOrgan(_organId) {
        require(block.timestamp >= organs[_organId].expiryTime, "Organ not yet expired");
        
        organs[_organId].status = OrganStatus.Expired;
        emit OrganStatusUpdated(_organId, OrganStatus.Expired);
    }

    function getOrgan(uint256 _organId) external view validOrgan(_organId) returns (Organ memory) {
        return organs[_organId];
    }

    function getRecipient(address _recipient) external view returns (Recipient memory) {
        require(isRecipientRegistered[_recipient], "Recipient not registered");
        return recipients[_recipient];
    }

    function getAllRecipients() external view returns (address[] memory) {
        return recipientList;
    }
}
