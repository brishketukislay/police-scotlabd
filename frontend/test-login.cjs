const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

// Read the built index.html
const indexPath = path.join(__dirname, 'dist', 'index.html');
let html = fs.readFileSync(indexPath, 'utf8');

// Create a JSDOM instance with a base URL so that relative paths resolve correctly
const dom = new JSDOM(html, {
  url: 'http://localhost',
  runScripts: "dangerously", // Allow scripts to run
  resources: "usable",       // Enable resource loading (for scripts, etc.)
  pretendToBeVisual: true,   // Trick the page into thinking it's visible
});

// Get the window and document
const { window } = dom;
const { document } = window;

// We'll need to wait for the page to load and for React to hydrate.
// We'll wait for the login form to appear.
function waitForElement(selector) {
  return new Promise((resolve) => {
    const check = () => {
      const el = document.querySelector(selector);
      if (el) resolve(el);
      else setTimeout(check, 50);
    };
    check();
  });
}

// We'll also capture console.log to see if our mockRequest log appears
const originalLog = console.log;
console.log = (...args) => {
  originalLog.apply(console, args);
  // Also send to our test output
  process.stdout.write(`[LOG] ${args.map(a => String(a)).join(' ')}\n`);
}

waitForElement('input[placeholder="admin / youthworker / player01"]')
  .then((usernameInput) => {
    console.log('Found username input');
    // Fill in the form
    usernameInput.value = 'admin';
    const passwordInput = document.querySelector('input[type="password"]');
    passwordInput.value = 'password';
    // Click the login button
    const loginButton = document.querySelector('button:contains("Sign in")');
    if (!loginButton) {
      // fallback: find button with text "Sign in"
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        if (btn.textContent.includes('Sign in')) {
          loginButton = btn;
          break;
        }
      }
    }
    if (loginButton) {
      console.log('Found login button, clicking...');
      loginButton.click();
    } else {
      console.log('Login button not found');
    }
    // Wait a bit to see if any logs appear
    setTimeout(() => {
      console.log('Test finished.');
      process.exit(0);
    }, 2000);
  })
  .catch((err) => {
    console.error('Error during test:', err);
    process.exit(1);
  });
