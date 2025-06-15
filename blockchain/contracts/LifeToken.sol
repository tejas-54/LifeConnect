// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract LifeToken is ERC20, Ownable {
    mapping(address => bool) public authorizedMinters;
    mapping(address => uint256) public donorRewards;
    mapping(address => uint256) public lastRewardTime;
    
    uint256 public constant REGISTRATION_REWARD = 100 * 10**18; // 100 tokens
    uint256 public constant DONATION_REWARD = 1000 * 10**18; // 1000 tokens
    uint256 public constant ANNUAL_REWARD = 50 * 10**18; // 50 tokens per year

    event RewardMinted(address indexed recipient, uint256 amount, string reason);
    event MinterAuthorized(address indexed minter);
    event MinterRevoked(address indexed minter);

    constructor() ERC20("LifeToken", "LIFE") Ownable(msg.sender) {
        _mint(msg.sender, 1000000 * 10**18); // Initial supply of 1 million tokens
        authorizedMinters[msg.sender] = true;
    }

    modifier onlyAuthorizedMinter() {
        require(authorizedMinters[msg.sender], "Not authorized to mint");
        _;
    }

    function authorizeMinter(address _minter) external onlyOwner {
        authorizedMinters[_minter] = true;
        emit MinterAuthorized(_minter);
    }

    function revokeMinter(address _minter) external onlyOwner {
        authorizedMinters[_minter] = false;
        emit MinterRevoked(_minter);
    }

    function rewardDonorRegistration(address _donor) external onlyAuthorizedMinter {
        require(donorRewards[_donor] == 0, "Already rewarded for registration");
        
        _mint(_donor, REGISTRATION_REWARD);
        donorRewards[_donor] += REGISTRATION_REWARD;
        lastRewardTime[_donor] = block.timestamp;
        
        emit RewardMinted(_donor, REGISTRATION_REWARD, "Registration");
    }

    function rewardDonation(address _donor) external onlyAuthorizedMinter {
        _mint(_donor, DONATION_REWARD);
        donorRewards[_donor] += DONATION_REWARD;
        
        emit RewardMinted(_donor, DONATION_REWARD, "Organ Donation");
    }

    function claimAnnualReward() external {
        require(lastRewardTime[msg.sender] > 0, "Not a registered donor");
        require(
            block.timestamp >= lastRewardTime[msg.sender] + 365 days,
            "Annual reward not yet available"
        );

        _mint(msg.sender, ANNUAL_REWARD);
        donorRewards[msg.sender] += ANNUAL_REWARD;
        lastRewardTime[msg.sender] = block.timestamp;
        
        emit RewardMinted(msg.sender, ANNUAL_REWARD, "Annual Reward");
    }

    function getTotalRewards(address _donor) external view returns (uint256) {
        return donorRewards[_donor];
    }

    function getTimeUntilNextReward(address _donor) external view returns (uint256) {
        if (lastRewardTime[_donor] == 0) return 0;
        
        uint256 nextRewardTime = lastRewardTime[_donor] + 365 days;
        if (block.timestamp >= nextRewardTime) return 0;
        
        return nextRewardTime - block.timestamp;
    }
}
