document.getElementById('saveBtn').addEventListener('click', () => {
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = 'Saving...';
  
  // Send a message to the background script to start the process
  chrome.runtime.sendMessage({ action: "saveSession" }, (response) => {
    if (chrome.runtime.lastError) {
      statusDiv.textContent = `Error: ${chrome.runtime.lastError.message}`;
    } else if (response && response.status === 'success') {
      statusDiv.textContent = 'Session saved successfully!';
    } else if (response && response.status === 'error') {
      statusDiv.textContent = `Error: ${response.message}`;
    } else {
      statusDiv.textContent = 'An unknown error occurred.';
    }
  });
});