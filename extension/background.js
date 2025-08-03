// Function to get all data and send it to the server
async function saveSessionData() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (!tab || !tab.url || !tab.url.startsWith('https://chat.qwen.ai')) {
    return { status: 'error', message: 'Not on a chat.qwen.ai tab.' };
  }

  try {
    // 1. Get cookies for the current domain
    const cookies = await chrome.cookies.getAll({ domain: "chat.qwen.ai" });

    // 2. Get localStorage and sessionStorage by injecting a script
    const scriptResult = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const local = window.localStorage;
        const session = window.sessionStorage;
        return {
          localStorage: Object.entries(local).map(([name, value]) => ({ name, value })),
          sessionStorage: Object.entries(session).map(([name, value]) => ({ name, value }))
        };
      }
    });

    const storage = scriptResult[0].result;

    // 3. Structure the data like Playwright's storage_state.json
    const storageState = {
      cookies: cookies,
      origins: [
        {
          origin: "https://chat.qwen.ai",
          localStorage: storage.localStorage,
          sessionStorage: storage.sessionStorage
        }
      ]
    };

    // 4. Send the data to the local Python server
    const serverResponse = await fetch('http://127.0.0.1:8000/save_auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(storageState)
    });

    if (!serverResponse.ok) {
      throw new Error(`Server responded with status: ${serverResponse.status}`);
    }

    return { status: 'success' };
  } catch (error) {
    console.error('Error in saveSessionData:', error);
    return { status: 'error', message: error.message };
  }
}

// Listen for the message from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "saveSession") {
    saveSessionData().then(sendResponse);
    return true; // Indicates that the response is sent asynchronously
  }
});