document.addEventListener('DOMContentLoaded', () => {
    console.log("Qwen Clone UI script loaded.");

    // --- DOM Elements ---
    const chatContainer = document.getElementById('chat-container');
    const welcomeView = document.getElementById('welcome-view');
    const promptForm = document.getElementById('prompt-form');
    const promptInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const newChatButton = document.getElementById('sidebar-new-chat-button');
    const chatHistoryList = document.getElementById('chat-history-list');
    const modelNameEl = document.getElementById('model-name');
    const modelNameDisplay = document.getElementById('model-name-display');
    const attachmentButton = document.getElementById('attachment-button');
    const fileUploadInput = document.getElementById('file-upload');
    const fileListContainer = document.getElementById('file-list-container');
    const actionButtonsContainer = document.getElementById('action-buttons-container');
    const webSearchButton = document.getElementById('web-search-button');
    const modelSelectorButton = document.getElementById('model-selector-button');
    const modelSelectorDropdown = document.getElementById('model-selector-dropdown');

    // --- State ---
    let currentChatId = null;
    let isWaitingForResponse = false;
    let selectedFiles = [];
    let currentAgent = null; // For Mission 2
    let selectedModel = null; // For Mission 3
    let useWebSearch = false; // For Mission 3

    // --- Constants ---
    // In preview mode, API calls should go to /api endpoints on the same domain
    const API_BASE_URL = '/api'; // Use /api prefix for Kubernetes ingress routing
    const sendButtonIcon = `<i class="iconfont leading-none icon-line-waveform !text-20 text-[#ffffff]" style=""></i>`;
    const loadingSpinner = `<div class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>`;

    // --- UI Functions ---
    function addMessage(sender, content, isImage = false) {
        if (welcomeView) {
            welcomeView.style.display = 'none';
        }

        const messageWrapper = document.createElement('div');
        messageWrapper.className = `response-meesage-container ${sender === 'user' ? 'user' : 'ai'}`;
        
        const messageContent = `
            <div class="m-auto w-full max-w-4xl px-2 xl:px-5">
                <div class="response-message-content">
                    <div class="flex items-start gap-3">
                        <img alt="profile" draggable="false" class="size-8 -translate-y-[1px] rounded-full object-cover" src="${sender === 'user' ? 'https://www.gravatar.com/avatar/?d=mp' : 'https://assets.alicdn.com/g/qwenweb/qwen-webui-fe/0.0.169/static/qwen_icon_light_84.png'}">
                        <div class="flex w-full flex-col">
                            <div class="font-semibold text-gray-800 dark:text-gray-100">${sender === 'user' ? 'You' : 'Qwen'}</div>
                            <div class="markdown-content-container">
                                <div class="markdown-body">
                                    ${isImage ? `<img src="${content}" style="max-width: 400px; border-radius: 10px;" />` : `<pre>${content}</pre>`}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        messageWrapper.innerHTML = messageContent;
        chatContainer.appendChild(messageWrapper);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function toggleLoading(isLoading) {
        isWaitingForResponse = isLoading;
        sendButton.disabled = isLoading;
        promptInput.disabled = isLoading;
        sendButton.innerHTML = isLoading ? loadingSpinner : sendButtonIcon;
    }

    function updateActiveHistoryItem() {
        document.querySelectorAll('.chat-history-item').forEach(item => {
            if (item.dataset.chatId === currentChatId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    function updateInputPlaceholder() {
        if (currentAgent) {
            promptInput.placeholder = `Message ${currentAgent}...`;
        } else {
            promptInput.placeholder = 'Message Qwen...';
        }
    }

    function renderActionButtons(container) {
        const actions = [
            { name: 'Web Dev', img: 'https://img.alicdn.com/imgextra/i4/O1CN01K49Cpa28SueDV7tjF_!!6000000007932-2-tps-80-80.png' },
            { name: 'Deep Research', img: 'https://img.alicdn.com/imgextra/i3/O1CN01Cq8uhd23V8UCJZ0fh_!!6000000007260-2-tps-135-135.png' },
            { name: 'Image Generation', img: 'https://img.alicdn.com/imgextra/i2/O1CN01phdKoS1MEAJmHK3c5_!!6000000001402-2-tps-135-135.png' }
        ];

        if (!container) return;
        container.innerHTML = '';
        actions.forEach(action => {
            const button = document.createElement('button');
            button.className = 'chat-prompt-suggest-button normal';
            button.innerHTML = `
                <img alt="" class="chat-prompt-suggest-button-img" src="${action.img}">
                <div>${action.name}</div>
            `;
            button.addEventListener('click', () => {
                currentAgent = action.name;
                updateInputPlaceholder();
                promptInput.focus();
                console.log(`Agent activated: ${currentAgent}`);
            });
            container.appendChild(button);
        });
    }

    async function loadAvailableModels() {
        try {
            const response = await fetch(`${API_BASE_URL}/models`);
            const data = await response.json();
            if (data.status === 'success' && data.models) {
                const dropdown = modelSelectorDropdown.querySelector('div[role="none"]');
                dropdown.innerHTML = ''; // Clear placeholders
                data.models.forEach(modelName => {
                    const modelLink = document.createElement('a');
                    modelLink.href = '#';
                    modelLink.className = 'text-gray-700 block px-4 py-2 text-sm';
                    modelLink.setAttribute('role', 'menuitem');
                    modelLink.textContent = modelName;
                    modelLink.addEventListener('click', (e) => {
                        e.preventDefault();
                        selectedModel = modelName;
                        modelNameDisplay.textContent = modelName;
                        modelSelectorDropdown.classList.add('hidden');
                        console.log(`Model selected: ${selectedModel}`);
                    });
                    dropdown.appendChild(modelLink);
                });
            }
        } catch (error) {
            console.error('Failed to load available models:', error);
        }
    }

    // --- API Functions ---
    async function loadChatHistory() {
        try {
            const response = await fetch(`${API_BASE_URL}/history`);
            const data = await response.json();
            if (data.status === 'success') {
                chatHistoryList.innerHTML = ''; // Clear existing list
                data.history.forEach(chat => {
                    const li = document.createElement('li');
                    li.className = 'chat-history-item';
                    li.textContent = chat.title || 'Untitled Chat';
                    li.dataset.chatId = chat.id;
                    
                    li.addEventListener('click', () => {
                        if (isWaitingForResponse) return;
                        currentChatId = chat.id;
                        chatContainer.innerHTML = '';
                        addMessage('system', `Loading chat: "${li.textContent}"...`);
                        console.log(`Switched to chat: ${currentChatId}`);
                        updateActiveHistoryItem();
                    });

                    chatHistoryList.appendChild(li);
                });
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    async function loadModelInfo() {
        try {
            const response = await fetch(`${API_BASE_URL}/model`);
            const data = await response.json();
            const modelName = data.status === 'success' ? data.model_name : 'Unknown';
            if (modelNameEl) modelNameEl.textContent = modelName;
            if (modelNameDisplay) modelNameDisplay.textContent = modelName;
        } catch (error) {
            console.error('Failed to load model info:', error);
            modelNameEl.textContent = 'Error';
        }
    }

    // --- Event Listeners ---
    newChatButton.addEventListener('click', () => {
        if (isWaitingForResponse) return;
        window.location.reload(); // Simple way to start a new chat for now
    });

    promptForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const prompt = promptInput.value.trim();
        if ((!prompt && selectedFiles.length === 0) || isWaitingForResponse) return;

        let userMessageContent = prompt;
        if (selectedFiles.length > 0) {
            const fileNames = selectedFiles.map(f => f.name).join(', ');
            userMessageContent += (prompt ? '\n' : '') + `[Attached: ${fileNames}]`;
        }
        const userMessage = { sender: 'user', content: userMessageContent, isImage: false };
        addMessage(userMessage.sender, userMessage.content, userMessage.isImage);

        promptInput.value = '';
        toggleLoading(true);

        try {
            let response;
            const payload = { 
                prompt, 
                chat_id: currentChatId,
                agent_name: currentAgent, // Mission 2: Send agent name
                use_web_search: useWebSearch, // Mission 3: Send web search state
                model_name: selectedModel // Mission 3: Send selected model
            };

            if (selectedFiles.length > 0) {
                const formData = new FormData();
                for (const key in payload) {
                    if (payload[key] !== null) formData.append(key, payload[key]);
                }
                selectedFiles.forEach(file => formData.append('files', file));
                response = await fetch(`${API_BASE_URL}/chat`, { method: 'POST', body: formData });
            } else {
                response = await fetch(`${API_BASE_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);
            const data = await response.json();

            if (data.status === 'success') {
                const wasNewChat = !currentChatId && data.chat_id;
                const newChatId = data.chat_id;
                const aiMessage = { sender: 'ai', content: data.response, isImage: false };
                addMessage(aiMessage.sender, aiMessage.content, aiMessage.isImage);

                currentChatId = newChatId;
                if (wasNewChat) {
                    await loadChatHistory();
                    currentAgent = null; // Reset agent after first use in a new chat
                    updateInputPlaceholder();
                }
                updateActiveHistoryItem();
                selectedFiles = [];
                fileUploadInput.value = '';
                // renderFilePills(); // TODO: Implement if needed
            } else {
                addMessage('error', data.message);
            }
        } catch (error) {
            addMessage('error', `Failed to get response: ${error.message}`);
        } finally {
            toggleLoading(false);
        }
    });

    modelSelectorButton.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent the document click listener from firing immediately
        modelSelectorDropdown.classList.toggle('hidden');
    });

    webSearchButton.addEventListener('click', () => {
        useWebSearch = !useWebSearch; // Toggle the state
        webSearchButton.classList.toggle('active', useWebSearch); // Toggle visual style
        console.log(`Web Search toggled: ${useWebSearch}`);
    });

    // --- Initialization ---
    // Close dropdown if clicked outside
    document.addEventListener('click', () => {
        if (!modelSelectorDropdown.classList.contains('hidden')) {
            modelSelectorDropdown.classList.add('hidden');
        }
    });

    function initializeApp() {
        loadChatHistory();
        loadModelInfo();
        loadAvailableModels();
        renderActionButtons(actionButtonsContainer);
        // Ensure button style reflects initial state
        webSearchButton.classList.toggle('active', useWebSearch);
    }
    initializeApp();
});