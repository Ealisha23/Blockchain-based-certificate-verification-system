const { ethers } = require("hardhat");

async function main() {
  const Certificate = await ethers.getContractFactory("CertificateVerifier");
  const certificate = await Certificate.deploy();
  await certificate.deployed();
  const [deployer] = await ethers.getSigners();
  console.log("Certificate contract deployed to:", certificate.address);
  console.log("Owner (deployer):", deployer.address);
  console.log("Set BCV_CONTRACT_ADDRESS=" + certificate.address + " in Backend/.env");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
