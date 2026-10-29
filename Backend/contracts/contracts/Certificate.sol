// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

contract CertificateVerifier {
    struct Certificate {
        bytes32 certificateHash;
        string studentName;
        string schoolName;
        string schoolMajor;
        string schoolDepartment;
        bool verified;
    }

    // Only the owner (the backend wallet) may write to the registry.
    address public owner;
    mapping(bytes32 => Certificate) private certificates;
    mapping(bytes32 => bool) private exists;

    event CertificateVerified(bytes32 certificateHash);
    event CertificateAdded(bytes32 indexed certificateHash, string studentName, string schoolName, string schoolMajor, string schoolDepartment);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only the owner can do this");
        _;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "Invalid new owner");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function addCertificate(
        string memory _studentName,
        string memory _schoolName,
        string memory _schoolMajor,
        string memory _schoolDepartment,
        bytes32 _certificateHash
    ) public onlyOwner {
        require(!exists[_certificateHash], "Certificate already exists");
        exists[_certificateHash] = true;
        certificates[_certificateHash] = Certificate(
            _certificateHash, _studentName, _schoolName, _schoolMajor, _schoolDepartment, false
        );
        emit CertificateAdded(_certificateHash, _studentName, _schoolName, _schoolMajor, _schoolDepartment);
    }

    function verifyCertificate(bytes32 _certificateHash) public onlyOwner {
        require(exists[_certificateHash], "Certificate does not exist");
        require(certificates[_certificateHash].verified == false, "Certificate has already been verified");
        certificates[_certificateHash].verified = true;
        emit CertificateVerified(_certificateHash);
    }

    function getCertificateInfo(bytes32 _certificateHash)
        public
        view
        returns (bytes32, string memory, string memory, string memory, string memory, bool)
    {
        Certificate storage c = certificates[_certificateHash];
        return (c.certificateHash, c.studentName, c.schoolName, c.schoolMajor, c.schoolDepartment, c.verified);
    }
}
