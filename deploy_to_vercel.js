#!/usr/bin/env node

/**
 * Vercel Deployment Script for NextJS MOE Application
 * --------------------------------------------------
 * This script guides you through deploying the NextJS application to Vercel.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Text styling for console
const styles = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m'
};

/**
 * Print a styled header
 */
function printHeader(title) {
  console.log('\n' + '='.repeat(80));
  console.log(`${styles.bright}${styles.cyan} ${title} ${styles.reset}`.padStart(40 + title.length/2).padEnd(80));
  console.log('='.repeat(80));
}

/**
 * Execute a command and return the output
 */
function execCommand(command, options = {}) {
  try {
    return execSync(command, { 
      encoding: 'utf8', 
      stdio: options.silent ? 'pipe' : 'inherit',
      ...options 
    });
  } catch (error) {
    if (options.ignoreError) {
      return null;
    }
    console.error(`${styles.red}Error executing command: ${command}${styles.reset}`);
    console.error(error.message);
    if (options.exit) {
      process.exit(1);
    }
    return null;
  }
}

/**
 * Check if Vercel CLI is installed
 */
function checkVercelCLI() {
  try {
    execSync('vercel --version', { stdio: 'pipe' });
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Check if the user is logged in to Vercel
 */
function checkVercelLogin() {
  try {
    const output = execSync('vercel whoami', { stdio: 'pipe', encoding: 'utf8' });
    return !output.includes('Error');
  } catch (error) {
    return false;
  }
}

/**
 * Check if the required environment files exist
 */
function checkEnvironmentFiles() {
  const requiredFiles = ['.env.local'];
  const missingFiles = requiredFiles.filter(file => !fs.existsSync(file));
  
  if (missingFiles.length > 0) {
    console.log(`${styles.yellow}The following environment files are missing:${styles.reset}`);
    missingFiles.forEach(file => console.log(`- ${file}`));
    return false;
  }
  
  return true;
}

/**
 * Create a Vercel environment variables file from .env.local
 */
function createVercelEnvFile() {
  console.log(`\nCreating Vercel environment variables file...`);
  
  try {
    const envContent = fs.readFileSync('.env.local', 'utf8');
    const envVars = {};
    
    envContent.split('\n').forEach(line => {
      if (line.trim() && !line.startsWith('#')) {
        const parts = line.split('=');
        if (parts.length >= 2) {
          const key = parts[0].trim();
          const value = parts.slice(1).join('=').trim();
          envVars[key] = value;
        }
      }
    });
    
    const vercelJson = {
      env: envVars
    };
    
    fs.writeFileSync('vercel.env.json', JSON.stringify(vercelJson, null, 2));
    console.log(`${styles.green}✓ Created vercel.env.json${styles.reset}`);
    return true;
  } catch (error) {
    console.error(`${styles.red}Error creating Vercel environment file:${styles.reset}`, error.message);
    return false;
  }
}

/**
 * Prompt user for confirmation
 */
function confirmAction(question) {
  return new Promise(resolve => {
    rl.question(`${question} (y/n): `, answer => {
      resolve(answer.toLowerCase() === 'y');
    });
  });
}

/**
 * Deploy to Vercel
 */
async function deployToVercel() {
  console.log(`\n${styles.bright}Deploying to Vercel...${styles.reset}`);
  
  // First, check if we should use a specific project name
  const useCustomUrl = await confirmAction('Do you want to use the custom URL https://nextjs-boilerplate-pi-rose-86.vercel.app/?');
  
  let deployCommand = 'vercel --prod';
  
  if (useCustomUrl) {
    deployCommand += ' --name nextjs-boilerplate-pi-rose-86';
  }
  
  console.log(`\nRunning: ${deployCommand}`);
  execCommand(deployCommand);
  
  return true;
}

/**
 * Verify deployment was successful
 */
async function verifyDeployment() {
  console.log(`\n${styles.bright}Verifying deployment...${styles.reset}`);
  
  // Get the deployed URL from Vercel
  try {
    const deployedUrl = execSync('vercel ls --prod -l 1 --output=url', { 
      encoding: 'utf8',
      stdio: 'pipe'
    }).trim();
    
    if (deployedUrl) {
      console.log(`\n${styles.green}Deployment successful!${styles.reset}`);
      console.log(`Deployed URL: ${styles.cyan}${deployedUrl}${styles.reset}`);
      
      // Ask if user wants to open the URL
      const openUrl = await confirmAction('Do you want to open the deployed site in your browser?');
      if (openUrl) {
        const openCommand = process.platform === 'win32' ? 'start' : 
                           process.platform === 'darwin' ? 'open' : 'xdg-open';
        execCommand(`${openCommand} ${deployedUrl}`);
      }
      
      return true;
    } else {
      console.log(`${styles.yellow}Could not automatically verify deployment.${styles.reset}`);
      console.log('Please check your Vercel dashboard for deployment status.');
      return false;
    }
  } catch (error) {
    console.log(`${styles.yellow}Could not automatically verify deployment: ${error.message}${styles.reset}`);
    console.log('Please check your Vercel dashboard for deployment status.');
    return false;
  }
}

/**
 * Ensure the MOE API URL is set correctly
 */
async function checkMoeApiUrl() {
  let moeApiUrl = '';
  
  // Try to read from .env.local
  try {
    const envContent = fs.readFileSync('.env.local', 'utf8');
    const match = envContent.match(/MOE_API_URL=(.+)/);
    if (match && match[1]) {
      moeApiUrl = match[1];
    }
  } catch (error) {
    // Ignore error
  }
  
  if (!moeApiUrl) {
    console.log(`${styles.yellow}MOE_API_URL is not set in .env.local${styles.reset}`);
    
    // Prompt user for MOE API URL
    moeApiUrl = await new Promise(resolve => {
      rl.question('Enter the URL for your MOE API service: ', answer => {
        resolve(answer.trim());
      });
    });
    
    // Update .env.local
    try {
      let envContent = '';
      try {
        envContent = fs.readFileSync('.env.local', 'utf8');
      } catch (error) {
        // File doesn't exist, create it
      }
      
      // Add or update MOE_API_URL
      if (envContent.includes('MOE_API_URL=')) {
        envContent = envContent.replace(/MOE_API_URL=.+/, `MOE_API_URL=${moeApiUrl}`);
      } else {
        envContent += `\nMOE_API_URL=${moeApiUrl}`;
      }
      
      fs.writeFileSync('.env.local', envContent);
      console.log(`${styles.green}✓ Updated MOE_API_URL in .env.local${styles.reset}`);
    } catch (error) {
      console.error(`${styles.red}Error updating .env.local:${styles.reset}`, error.message);
    }
  } else {
    console.log(`${styles.green}✓ MOE_API_URL is set to ${moeApiUrl}${styles.reset}`);
  }
  
  return moeApiUrl;
}

/**
 * Main deployment function
 */
async function main() {
  printHeader('NEXTJS MOE APPLICATION VERCEL DEPLOYMENT');
  
  console.log(`\n${styles.bright}This script will guide you through deploying the NextJS MOE application to Vercel.${styles.reset}`);
  console.log('Make sure your MOE service is already deployed and accessible.');
  
  // Check Vercel CLI
  console.log('\nChecking Vercel CLI installation...');
  const vercelCliInstalled = checkVercelCLI();
  if (!vercelCliInstalled) {
    console.log(`${styles.red}Vercel CLI is not installed.${styles.reset}`);
    console.log('Please install it with: npm install -g vercel');
    process.exit(1);
  }
  console.log(`${styles.green}✓ Vercel CLI is installed${styles.reset}`);
  
  // Check Vercel login
  console.log('\nChecking Vercel login status...');
  const vercelLoggedIn = checkVercelLogin();
  if (!vercelLoggedIn) {
    console.log(`${styles.yellow}You are not logged in to Vercel.${styles.reset}`);
    console.log('Please login with: vercel login');
    
    const proceed = await confirmAction('Do you want to login now?');
    if (proceed) {
      execCommand('vercel login');
    } else {
      process.exit(1);
    }
  } else {
    console.log(`${styles.green}✓ You are logged in to Vercel${styles.reset}`);
  }
  
  // Check environment files
  console.log('\nChecking environment files...');
  const envFilesExist = checkEnvironmentFiles();
  if (!envFilesExist) {
    const proceed = await confirmAction('Some environment files are missing. Do you want to create them?');
    if (proceed) {
      // Create .env.local if it doesn't exist
      if (!fs.existsSync('.env.local')) {
        const sampleEnv = `# Authentication settings
AUTH_SECRET=replace_with_random_string
MOE_API_URL=https://your-moe-service-url
MOE_TIMEOUT_MS=30000
BLOB_READ_WRITE_TOKEN=your_blob_token
POSTGRES_URL=your_postgres_url
XAI_API_KEY=your_xai_key_here
`;
        fs.writeFileSync('.env.local', sampleEnv);
        console.log(`${styles.green}✓ Created .env.local with sample values${styles.reset}`);
        console.log(`${styles.yellow}Please edit .env.local to set the correct values${styles.reset}`);
        
        const edit = await confirmAction('Do you want to edit .env.local now?');
        if (edit) {
          const editor = process.env.EDITOR || process.env.VISUAL || 'notepad';
          execCommand(`${editor} .env.local`, { ignoreError: true });
        } else {
          process.exit(1);
        }
      }
    } else {
      process.exit(1);
    }
  } else {
    console.log(`${styles.green}✓ Environment files exist${styles.reset}`);
  }
  
  // Check MOE API URL
  await checkMoeApiUrl();
  
  // Create Vercel environment variables file
  createVercelEnvFile();
  
  // Running tests before deployment
  console.log('\nWould you like to run tests before deployment?');
  const runTests = await confirmAction('Run tests?');
  if (runTests) {
    console.log('\nRunning tests...');
    execCommand('npm test', { ignoreError: true });
  }
  
  // Confirm deployment
  const proceed = await confirmAction('\nReady to deploy to Vercel. Proceed?');
  if (!proceed) {
    console.log('Deployment cancelled.');
    process.exit(0);
  }
  
  // Deploy to Vercel
  await deployToVercel();
  
  // Verify deployment
  await verifyDeployment();
  
  // Clean up
  console.log('\nCleaning up...');
  if (fs.existsSync('vercel.env.json')) {
    fs.unlinkSync('vercel.env.json');
  }
  
  printHeader('DEPLOYMENT COMPLETE');
  console.log(`\n${styles.green}The NextJS MOE application has been successfully deployed to Vercel!${styles.reset}`);
  console.log('\nNext steps:');
  console.log('1. Test the chat interface with MOE models');
  console.log('2. Verify that fallback mechanisms work if needed');
  console.log('3. Set up monitoring for the MOE service');
  
  rl.close();
}

// Run the main function
main().catch(error => {
  console.error(`${styles.red}Deployment failed:${styles.reset}`, error);
  process.exit(1);
});