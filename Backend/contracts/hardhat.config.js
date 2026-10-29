require("@nomicfoundation/hardhat-toolbox");

// Optional: compile with the pure-JS solc package instead of downloading a native
// compiler (useful behind restrictive firewalls). Enable with HARDHAT_USE_SOLCJS=1
if (process.env.HARDHAT_USE_SOLCJS === "1") {
  const { subtask } = require("hardhat/config");
  const { TASK_COMPILE_SOLIDITY_GET_SOLC_BUILD } = require("hardhat/builtin-tasks/task-names");
  subtask(TASK_COMPILE_SOLIDITY_GET_SOLC_BUILD, async (args, hre, runSuper) => {
    if (args.solcVersion === "0.8.17") {
      const solc = require("solc");
      return {
        compilerPath: require.resolve("solc/soljson.js"),
        isSolcJs: true,
        version: "0.8.17",
        longVersion: solc.version(),
      };
    }
    return runSuper();
  });
}

/** @type import('hardhat/config').HardhatUserConfig */
const networks = {};
// Optional public testnet (e.g. Sepolia). Set these in contracts/.env or your shell.
if (process.env.DEPLOY_RPC_URL && process.env.DEPLOY_PRIVATE_KEY) {
  networks.remote = {
    url: process.env.DEPLOY_RPC_URL,
    accounts: [process.env.DEPLOY_PRIVATE_KEY],
  };
}

module.exports = {
  solidity: "0.8.17",
  networks,
};
