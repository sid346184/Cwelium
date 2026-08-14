// Credentials and State Management
let tokens = [];
let proxies = [];
let currentAction = 'spammer';
let runningRequest = null;
let reader = null; // streaming reader

// DOM Elements
const inputTokens = document.getElementById('input-tokens');
const inputProxies = document.getElementById('input-proxies');
const countTokens = document.getElementById('count-tokens');
const countProxies = document.getElementById('count-proxies');
const actionCards = document.querySelectorAll('.action-card');
const paramsTitle = document.getElementById('params-title');
const paramsInputs = document.getElementById('params-inputs');
const btnExecute = document.getElementById('btn-execute-action');
const btnClearTerminal = document.getElementById('btn-clear-terminal');
const terminalOutput = document.getElementById('terminal-output');

// Config mapping for inputs required by each action
const actionFields = {
    spammer: [
        { id: 'param-channel-link', label: 'Channel Link / ID', type: 'text', placeholder: 'https://discord.com/channels/123/456 or 456', required: true },
        { id: 'param-message', label: 'Message Content', type: 'text', placeholder: 'Spam text here...', required: true },
        { id: 'param-massping', label: 'Massping Scraped Members', type: 'checkbox' },
        { id: 'param-pings-amount', label: 'Pings per message', type: 'number', val: 5, placeholder: '5' },
        { id: 'param-random-string', label: 'Append Random String', type: 'checkbox' },
        { id: 'param-delay', label: 'Delay (Seconds)', type: 'number', step: '0.1', val: 0, placeholder: '0' },
        { id: 'param-spammer-count', label: 'Spam Message Count Limit', type: 'number', val: 5, placeholder: '5' }
    ],
    checker: [],
    joiner: [
        { id: 'param-invite', label: 'Invite Link / Code', type: 'text', placeholder: 'https://discord.gg/abc or abc', required: true }
    ],
    leaver: [
        { id: 'param-guild-id', label: 'Guild ID', type: 'text', placeholder: 'Guild Server ID', required: true }
    ],
    reactor: [
        { id: 'param-message-link', label: 'Message Link', type: 'text', placeholder: 'https://discord.com/channels/guild/channel/msg', required: true },
        { id: 'param-emoji', label: 'Reaction Emoji', type: 'text', placeholder: '🔥 or emoji_name:id', required: true }
    ],
    button: [
        { id: 'param-message-link', label: 'Message Link', type: 'text', placeholder: 'https://discord.com/channels/guild/channel/msg', required: true }
    ],
    accept: [
        { id: 'param-guild-id', label: 'Guild ID', type: 'text', placeholder: 'Guild Server ID', required: true }
    ],
    guild: [
        { id: 'param-guild-id', label: 'Guild ID', type: 'text', placeholder: 'Guild Server ID', required: true }
    ],
    bio: [
        { id: 'param-bio', label: 'Bio Text', type: 'text', placeholder: 'New custom bio description...', required: true }
    ],
    nick_changer: [
        { id: 'param-guild-id', label: 'Guild ID', type: 'text', placeholder: 'Guild Server ID', required: true },
        { id: 'param-nickname', label: 'New Nickname', type: 'text', placeholder: 'Enter new nickname', required: true }
    ],
    voice_joiner: [
        { id: 'param-channel-link', label: 'Voice Channel Link / ID', type: 'text', placeholder: 'Channel URL or Channel ID', required: true },
        { id: 'param-guild-id', label: 'Guild ID (Optional if link is used)', type: 'text', placeholder: 'Guild ID' }
    ],
    onboard: [
        { id: 'param-guild-id', label: 'Guild ID', type: 'text', placeholder: 'Guild Server ID', required: true }
    ],
    dm_spam: [
        { id: 'param-user-id', label: 'Target User ID', type: 'text', placeholder: 'User Account ID', required: true },
        { id: 'param-message', label: 'Message Content', type: 'text', placeholder: 'Spam DM content...', required: true }
    ],
    caller: [
        { id: 'param-user-id', label: 'Target User ID', type: 'text', placeholder: 'User Account ID', required: true }
    ],
    typer: [
        { id: 'param-channel-link', label: 'Channel Link / ID', type: 'text', placeholder: 'Channel Link or ID', required: true }
    ],
    thread_spammer: [
        { id: 'param-channel-link', label: 'Channel Link / ID', type: 'text', placeholder: 'Channel Link or ID', required: true },
        { id: 'param-thread-name', label: 'Thread Name', type: 'text', placeholder: 'New Thread Title', required: true }
    ],
    onliner: [],
    friender: [
        { id: 'param-nickname', label: 'Username to add', type: 'text', placeholder: 'username#0000 or username', required: true }
    ]
};

// Initialize Application
function init() {
    loadTheme();
    loadCredentials();
    setupEventListeners();
    renderFields('spammer');
}

// LocalStorage loaders/savers
function loadTheme() {
    const savedTheme = localStorage.getItem('cwelium_theme') || 'cyan';
    document.body.className = `theme-${savedTheme}`;
    document.querySelectorAll('.theme-dot').forEach(dot => {
        dot.classList.toggle('active', dot.dataset.theme === savedTheme);
    });
}

function loadCredentials() {
    const savedTokens = localStorage.getItem('cwelium_tokens') || '';
    const savedProxies = localStorage.getItem('cwelium_proxies') || '';
    inputTokens.value = savedTokens;
    inputProxies.value = savedProxies;
    updateCounts();
}

function updateCounts() {
    tokens = inputTokens.value.split('\n').map(t => t.trim()).filter(t => t.length > 0);
    proxies = inputProxies.value.split('\n').map(p => p.trim()).filter(p => p.length > 0);
    
    countTokens.textContent = `${tokens.length} token${tokens.length === 1 ? '' : 's'} loaded`;
    countProxies.textContent = `${proxies.length} prox${proxies.length === 1 ? 'y' : 'ies'} loaded`;
    
    localStorage.setItem('cwelium_tokens', inputTokens.value);
    localStorage.setItem('cwelium_proxies', inputProxies.value);
}

// Render dynamic configuration fields
function renderFields(action) {
    currentAction = action;
    paramsTitle.textContent = `${action.replace('_', ' ')} Configuration`;
    paramsInputs.innerHTML = '';
    
    const fields = actionFields[action] || [];
    
    if (fields.length === 0) {
        paramsInputs.innerHTML = '<div class="no-params-msg" style="grid-column: 1/-1; color: var(--text-muted); font-size: 0.85rem;">No parameters required for this operation. Click run to execute.</div>';
        return;
    }
    
    fields.forEach(field => {
        const inputDiv = document.createElement('div');
        
        if (field.type === 'checkbox') {
            inputDiv.className = 'checkbox-group';
            inputDiv.innerHTML = `
                <input type="checkbox" id="${field.id}" ${field.val ? 'checked' : ''}>
                <label for="${field.id}">${field.label}</label>
            `;
        } else {
            inputDiv.className = 'input-group';
            inputDiv.innerHTML = `
                <label for="${field.id}">${field.label}</label>
                <input type="${field.type}" id="${field.id}" placeholder="${field.placeholder || ''}" ${field.required ? 'required' : ''} ${field.step ? `step="${field.step}"` : ''} value="${field.val !== undefined ? field.val : ''}">
            `;
        }
        
        paramsInputs.appendChild(inputDiv);
    });
}

// Terminal helpers
function appendTerminalLine(text, type = 'system') {
    const line = document.createElement('div');
    line.className = `terminal-line log-${type.toLowerCase()}`;
    line.textContent = text;
    terminalOutput.appendChild(line);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

function clearTerminal() {
    terminalOutput.innerHTML = '';
    appendTerminalLine('[SYSTEM] Terminal cleared.', 'system');
}

// Setup listeners
function setupEventListeners() {
    inputTokens.addEventListener('input', updateCounts);
    inputProxies.addEventListener('input', updateCounts);
    
    // Theme Dot switcher
    document.querySelectorAll('.theme-dot').forEach(dot => {
        dot.addEventListener('click', () => {
            const theme = dot.dataset.theme;
            localStorage.setItem('cwelium_theme', theme);
            loadTheme();
            appendTerminalLine(`[SYSTEM] Switched theme to ${theme}.`, 'info');
        });
    });

    // Action Cards Selection
    actionCards.forEach(card => {
        card.addEventListener('click', () => {
            actionCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            renderFields(card.dataset.action);
        });
    });

    btnClearTerminal.addEventListener('click', clearTerminal);
    btnExecute.addEventListener('click', handleExecute);
}

// Trigger running action to API
async function handleExecute() {
    // 1. Validation
    if (tokens.length === 0) {
        appendTerminalLine('[ERROR] No discord tokens loaded. Please enter tokens in the left panel.', 'error');
        return;
    }
    
    // If already running, cancel the stream
    if (runningRequest) {
        if (reader) {
            await reader.cancel();
        }
        appendTerminalLine('[SYSTEM] Run cancelled by user.', 'system');
        setLoadingState(false);
        return;
    }
    
    // Gather dynamic parameters
    const payload = {
        action: currentAction,
        tokens: tokens,
        proxies: proxies
    };
    
    // Validate inputs inside parameters grid
    let isValid = true;
    const fields = actionFields[currentAction] || [];
    fields.forEach(field => {
        const inputElement = document.getElementById(field.id);
        if (!inputElement) return;
        
        let value;
        if (field.type === 'checkbox') {
            value = inputElement.checked;
        } else if (field.type === 'number') {
            value = inputElement.value !== '' ? parseFloat(inputElement.value) : null;
        } else {
            value = inputElement.value.trim();
        }
        
        if (field.required && (value === '' || value === null)) {
            inputElement.focus();
            isValid = false;
        }
        
        // Map parameter keys matching the ActionRequest schema
        const schemaKey = field.id.replace('param-', '').replace(/-/g, '_');
        payload[schemaKey] = value;
    });
    
    if (!isValid) {
        appendTerminalLine('[ERROR] Please fill out all required fields marked for this operation.', 'error');
        return;
    }
    
    // Setup UI execution state
    setLoadingState(true);
    appendTerminalLine(`[SYSTEM] Initiating action: ${currentAction.toUpperCase()} on ${tokens.length} token(s)...`, 'info');
    
    try {
        const response = await fetch('/api/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
        }
        
        // Handle streaming reader
        reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        runningRequest = true;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            
            // Retain last partial chunk in buffer
            buffer = lines.pop();
            
            for (const line of lines) {
                if (line.trim().startsWith('data: ')) {
                    const rawJson = line.substring(6).trim();
                    if (!rawJson) continue;
                    
                    try {
                        const logData = JSON.parse(rawJson);
                        if (logData.ping) {
                            continue; // keep alive check
                        }
                        if (logData.done) {
                            appendTerminalLine('[SYSTEM] Action finished execution.', 'info');
                            break;
                        }
                        
                        if (logData.raw) {
                            appendTerminalLine(logData.raw, logData.type || 'system');
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE JSON:', e, line);
                    }
                }
            }
        }
    } catch (err) {
        appendTerminalLine(`[ERROR] Connection failed: ${err.message}`, 'error');
    } finally {
        setLoadingState(false);
    }
}

function setLoadingState(isLoading) {
    const btnText = btnExecute.querySelector('.btn-text');
    const spinner = btnExecute.querySelector('.loader-spinner');
    
    if (isLoading) {
        btnText.textContent = 'CANCEL OPERATION';
        spinner.classList.remove('hidden');
        btnExecute.style.backgroundColor = '#ff2a2a';
        btnExecute.style.boxShadow = '0 0 12px rgba(255, 42, 42, 0.4)';
        runningRequest = true;
    } else {
        btnText.textContent = 'INITIALIZE RUN';
        spinner.classList.add('hidden');
        btnExecute.style.backgroundColor = '';
        btnExecute.style.boxShadow = '';
        runningRequest = null;
        reader = null;
    }
}

// Run App
window.addEventListener('DOMContentLoaded', init);
