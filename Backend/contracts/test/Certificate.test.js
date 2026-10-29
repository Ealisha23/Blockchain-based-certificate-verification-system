const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CertificateVerifier", function () {
  let contract, owner, other;
  const hash = ethers.utils.formatBytes32String("Certificate Hash");

  beforeEach(async function () {
    [owner, other] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("CertificateVerifier");
    contract = await Factory.deploy();
    await contract.deployed();
  });

  it("adds a certificate and emits CertificateAdded", async function () {
    await expect(contract.addCertificate("John Doe", "Hardhat University", "Computer Science", "Engineering", hash))
      .to.emit(contract, "CertificateAdded")
      .withArgs(hash, "John Doe", "Hardhat University", "Computer Science", "Engineering");
    const info = await contract.getCertificateInfo(hash);
    expect(info[1]).to.equal("John Doe");
    expect(info[5]).to.equal(false);
  });

  it("returns an empty certificate for an unknown hash", async function () {
    const info = await contract.getCertificateInfo(ethers.utils.formatBytes32String("Unknown"));
    expect(info[1]).to.equal("");
    expect(info[5]).to.equal(false);
  });

  it("verifies once and rejects a second verification", async function () {
    await contract.addCertificate("A", "B", "C", "D", hash);
    await expect(contract.verifyCertificate(hash)).to.emit(contract, "CertificateVerified").withArgs(hash);
    expect((await contract.getCertificateInfo(hash))[5]).to.equal(true);
    await expect(contract.verifyCertificate(hash)).to.be.revertedWith("Certificate has already been verified");
  });

  it("rejects verifying an unknown certificate", async function () {
    await expect(contract.verifyCertificate(hash)).to.be.revertedWith("Certificate does not exist");
  });

  it("does not allow overwriting an existing certificate", async function () {
    await contract.addCertificate("A", "B", "C", "D", hash);
    await expect(contract.addCertificate("X", "Y", "Z", "W", hash)).to.be.revertedWith("Certificate already exists");
  });

  it("only lets the owner write", async function () {
    await expect(contract.connect(other).addCertificate("A", "B", "C", "D", hash)).to.be.revertedWith("Only the owner can do this");
    await contract.addCertificate("A", "B", "C", "D", hash);
    await expect(contract.connect(other).verifyCertificate(hash)).to.be.revertedWith("Only the owner can do this");
  });
});
