// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title AgentPact
/// @notice Trustless freelance agreements enforced on-chain.
///         Humans set boundaries. Agents negotiate and execute within them.
/// @dev Built for The Synthesis hackathon — "Agents that cooperate" track.

contract AgentPact {

    enum PactStatus {
        Created,
        Funded,
        WorkSubmitted,
        Completed,
        Disputed,
        Cancelled
    }

    struct Pact {
        address client;
        address freelancer;
        uint256 amount;
        uint256 deadline;
        string deliverableDescription;
        string workProof;
        PactStatus status;
        uint256 createdAt;
    }

    uint256 public pactCount;
    mapping(uint256 => Pact) public pacts;

    // ── Events ──────────────────────────────────────────────

    event PactCreated(
        uint256 indexed pactId,
        address indexed client,
        address indexed freelancer,
        uint256 amount,
        uint256 deadline,
        string deliverableDescription
    );

    event PactFunded(uint256 indexed pactId, uint256 amount);
    event WorkSubmitted(uint256 indexed pactId, string workProof);
    event FundsReleased(uint256 indexed pactId, address indexed freelancer, uint256 amount);
    event PactDisputed(uint256 indexed pactId, address indexed disputedBy);
    event PactCancelled(uint256 indexed pactId);
    event DisputeResolved(uint256 indexed pactId, address indexed recipient, uint256 amount);

    // ── Modifiers ───────────────────────────────────────────

    modifier onlyClient(uint256 _pactId) {
        require(msg.sender == pacts[_pactId].client, "Only client");
        _;
    }

    modifier onlyFreelancer(uint256 _pactId) {
        require(msg.sender == pacts[_pactId].freelancer, "Only freelancer");
        _;
    }

    modifier inStatus(uint256 _pactId, PactStatus _status) {
        require(pacts[_pactId].status == _status, "Invalid pact status");
        _;
    }

    // ── Core Functions ──────────────────────────────────────

    /// @notice Client creates a pact with terms. No funds locked yet.
    /// @param _freelancer Address of the freelancer (or their agent's wallet)
    /// @param _deadline Timestamp by which work must be submitted
    /// @param _deliverableDescription What the freelancer must deliver
    function createPact(
        address _freelancer,
        uint256 _deadline,
        string calldata _deliverableDescription
    ) external payable returns (uint256) {
        require(_freelancer != address(0), "Invalid freelancer");
        require(_freelancer != msg.sender, "Cannot hire yourself");
        require(_deadline > block.timestamp, "Deadline must be in the future");
        require(bytes(_deliverableDescription).length > 0, "Description required");

        uint256 pactId = pactCount++;

        pacts[pactId] = Pact({
            client: msg.sender,
            freelancer: _freelancer,
            amount: msg.value,
            deadline: _deadline,
            deliverableDescription: _deliverableDescription,
            workProof: "",
            status: msg.value > 0 ? PactStatus.Funded : PactStatus.Created,
            createdAt: block.timestamp
        });

        emit PactCreated(
            pactId,
            msg.sender,
            _freelancer,
            msg.value,
            _deadline,
            _deliverableDescription
        );

        if (msg.value > 0) {
            emit PactFunded(pactId, msg.value);
        }

        return pactId;
    }

    /// @notice Client funds an existing pact (escrow deposit)
    function fundPact(uint256 _pactId)
        external
        payable
        onlyClient(_pactId)
        inStatus(_pactId, PactStatus.Created)
    {
        require(msg.value > 0, "Must send ETH");

        pacts[_pactId].amount += msg.value;
        pacts[_pactId].status = PactStatus.Funded;

        emit PactFunded(_pactId, msg.value);
    }

    /// @notice Freelancer submits proof of work
    /// @param _workProof Link or hash of the completed deliverable
    function submitWork(uint256 _pactId, string calldata _workProof)
        external
        onlyFreelancer(_pactId)
        inStatus(_pactId, PactStatus.Funded)
    {
        require(block.timestamp <= pacts[_pactId].deadline, "Deadline passed");
        require(bytes(_workProof).length > 0, "Proof required");

        pacts[_pactId].workProof = _workProof;
        pacts[_pactId].status = PactStatus.WorkSubmitted;

        emit WorkSubmitted(_pactId, _workProof);
    }

    /// @notice Client approves the work and releases escrow to freelancer
    function releaseFunds(uint256 _pactId)
        external
        onlyClient(_pactId)
        inStatus(_pactId, PactStatus.WorkSubmitted)
    {
        Pact storage pact = pacts[_pactId];
        uint256 payment = pact.amount;

        pact.amount = 0;
        pact.status = PactStatus.Completed;

        (bool sent, ) = pact.freelancer.call{value: payment}("");
        require(sent, "Payment failed");

        emit FundsReleased(_pactId, pact.freelancer, payment);
    }

    /// @notice Either party can dispute a funded or submitted pact
    function disputePact(uint256 _pactId) external {
        Pact storage pact = pacts[_pactId];
        require(
            msg.sender == pact.client || msg.sender == pact.freelancer,
            "Not a party"
        );
        require(
            pact.status == PactStatus.Funded ||
            pact.status == PactStatus.WorkSubmitted,
            "Cannot dispute"
        );

        pact.status = PactStatus.Disputed;

        emit PactDisputed(_pactId, msg.sender);
    }

    /// @notice Auto-release if client doesn't act within 7 days of submission
    /// @dev Anyone can call this — acts as a trustless timeout
    function autoRelease(uint256 _pactId)
        external
        inStatus(_pactId, PactStatus.WorkSubmitted)
    {
        Pact storage pact = pacts[_pactId];
        require(
            block.timestamp > pact.deadline + 7 days,
            "Review period not over"
        );

        uint256 payment = pact.amount;
        pact.amount = 0;
        pact.status = PactStatus.Completed;

        (bool sent, ) = pact.freelancer.call{value: payment}("");
        require(sent, "Payment failed");

        emit FundsReleased(_pactId, pact.freelancer, payment);
    }

    /// @notice Client can cancel an unfunded pact
    function cancelPact(uint256 _pactId)
        external
        onlyClient(_pactId)
        inStatus(_pactId, PactStatus.Created)
    {
        pacts[_pactId].status = PactStatus.Cancelled;

        emit PactCancelled(_pactId);
    }

    /// @notice Refund client if freelancer misses the deadline
    function claimRefund(uint256 _pactId)
        external
        onlyClient(_pactId)
        inStatus(_pactId, PactStatus.Funded)
    {
        Pact storage pact = pacts[_pactId];
        require(block.timestamp > pact.deadline, "Deadline not passed");

        uint256 refund = pact.amount;
        pact.amount = 0;
        pact.status = PactStatus.Cancelled;

        (bool sent, ) = pact.client.call{value: refund}("");
        require(sent, "Refund failed");

        emit PactCancelled(_pactId);
    }

    // ── View Functions ──────────────────────────────────────

    /// @notice Get full pact details
    function getPact(uint256 _pactId) external view returns (Pact memory) {
        return pacts[_pactId];
    }

    /// @notice Check if a pact's deadline has passed
    function isExpired(uint256 _pactId) external view returns (bool) {
        return block.timestamp > pacts[_pactId].deadline;
    }
}
