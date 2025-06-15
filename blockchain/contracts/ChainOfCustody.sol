// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ChainOfCustody {
    enum EventType { Pickup, Handover, Checkpoint, Delivery, Emergency }
    
    struct CustodyEvent {
        uint256 eventId;
        uint256 organId;
        EventType eventType;
        address handler;
        string location;
        uint256 timestamp;
        string notes;
        string documentCID; // IPFS CID for related documents
        bool verified;
    }

    mapping(uint256 => CustodyEvent[]) public organCustodyChain;
    mapping(uint256 => uint256) public eventCounter;
    
    event CustodyEventLogged(
        uint256 indexed organId,
        uint256 indexed eventId,
        EventType eventType,
        address indexed handler,
        string location
    );
    event EventVerified(uint256 indexed organId, uint256 indexed eventId);

    function logCustodyEvent(
        uint256 _organId,
        EventType _eventType,
        string memory _location,
        string memory _notes,
        string memory _documentCID
    ) public returns (uint256) {  // Changed from 'external' to 'public'
        uint256 eventId = eventCounter[_organId]++;
        
        CustodyEvent memory newEvent = CustodyEvent({
            eventId: eventId,
            organId: _organId,
            eventType: _eventType,
            handler: msg.sender,
            location: _location,
            timestamp: block.timestamp,
            notes: _notes,
            documentCID: _documentCID,
            verified: false
        });

        organCustodyChain[_organId].push(newEvent);

        emit CustodyEventLogged(_organId, eventId, _eventType, msg.sender, _location);
        return eventId;
    }

    function verifyEvent(uint256 _organId, uint256 _eventId) external {
        require(_eventId < organCustodyChain[_organId].length, "Invalid event ID");
        
        organCustodyChain[_organId][_eventId].verified = true;
        emit EventVerified(_organId, _eventId);
    }

    function getCustodyChain(uint256 _organId) external view returns (CustodyEvent[] memory) {
        return organCustodyChain[_organId];
    }

    function getLatestEvent(uint256 _organId) external view returns (CustodyEvent memory) {
        require(organCustodyChain[_organId].length > 0, "No events for this organ");
        
        uint256 latestIndex = organCustodyChain[_organId].length - 1;
        return organCustodyChain[_organId][latestIndex];
    }

    function getEventCount(uint256 _organId) external view returns (uint256) {
        return organCustodyChain[_organId].length;
    }

    function emergencyStop(uint256 _organId, string memory _reason) external {
        logCustodyEvent(_organId, EventType.Emergency, "Emergency Stop", _reason, "");
    }
}
