/**
 * TriAI Browser Client JavaScript
 * Handles all client-side functionality for the multi-agent AI interface
 */

class TriAIClient {
    constructor() {
        this.currentUser = null;
        this.selectedAgent = null;
        this.agents = [];
        this.messages = [];
        this.isLoading = false;
        this.messageRefreshInterval = null;
        this.appConfig = null;
        
        // Initialize the application
        this.init();
    }
    
    async init() {
        try {
            this.showLoading(true);
            await this.loadAppConfig();
            await this.loadCurrentUser();
            await this.loadAgents();
            this.setupEventListeners();
            this.updateConnectionStatus('connected');
            this.showLoading(false);
        } catch (error) {
            console.error('Initialization failed:', error);
            this.showError('Failed to initialize application');
            this.updateConnectionStatus('disconnected');
            this.showLoading(false);
        }
    }
    
    // API Communication Methods
    
    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(endpoint, finalOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API call failed for ${endpoint}:`, error);
            throw error;
        }
    }
    
    async loadAppConfig() {
        try {
            this.appConfig = await this.apiCall('/api/config');
            this.updateAppTitle();
        } catch (error) {
            console.error('Failed to load app config:', error);
            // Use defaults if config loading fails
            this.appConfig = {
                application: {
                    name: "TriAI",
                    display_name: "TriAI Analytics Platform",
                    description: "Multi-agent AI framework with database integration"
                }
            };
            this.updateAppTitle();
        }
    }
    
    updateAppTitle() {
        const app = this.appConfig.application;
        document.title = `${app.name} - Multi-Agent AI Interface`;
        
        // Update header
        const headerTitle = document.querySelector('.header h1');
        if (headerTitle) {
            headerTitle.textContent = `${app.name} Multi-Agent Interface`;
        }
        
        // Update footer
        const footer = document.querySelector('.footer p');
        if (footer) {
            footer.innerHTML = `${app.display_name} | 
               <a href="/docs" target="_blank">API Docs</a> | 
               <span id="server-info">Server: Connected</span>`;
        }
    }
    
    async loadCurrentUser() {
        try {
            const userData = await this.apiCall('/api/user');
            this.currentUser = userData.username;
            document.getElementById('current-user').textContent = `User: ${this.currentUser}`;
        } catch (error) {
            console.error('Failed to load user:', error);
            document.getElementById('current-user').textContent = 'User: Unknown';
        }
    }
    
    async loadAgents() {
        try {
            this.agents = await this.apiCall('/api/agents');
            this.populateAgentSelect();
        } catch (error) {
            console.error('Failed to load agents:', error);
            this.showError('Failed to load AI agents');
        }
    }
    
    async sendMessage(message) {
        if (!this.selectedAgent || !message.trim()) {
            return;
        }
        
        try {
            this.setLoading(true);
            
            const result = await this.apiCall('/api/message', {
                method: 'POST',
                body: JSON.stringify({
                    user_to: this.selectedAgent,
                    message: message.trim()
                })
            });
            
            if (result.success) {
                // Add user message to chat immediately
                this.addMessageToChat({
                    user_from: this.currentUser,
                    user_to: this.selectedAgent,
                    message: message.trim(),
                    posted: new Date().toISOString()
                });
                
                // Clear input
                document.getElementById('message-input').value = '';
                
                // Refresh messages to get any immediate responses
                setTimeout(() => this.loadMessages(), 1000);
            } else {
                throw new Error('Failed to send message');
            }
        } catch (error) {
            console.error('Send message failed:', error);
            this.showError('Failed to send message');
        } finally {
            this.setLoading(false);
        }
    }
    
    async loadMessages() {
        if (!this.selectedAgent) return;
        
        try {
            const messages = await this.apiCall(`/api/messages/${this.selectedAgent}`);
            this.messages = messages;
            this.displayMessages();
        } catch (error) {
            console.error('Failed to load messages:', error);
            this.showError('Failed to load conversation history');
        }
    }
    
    async loadAgentMemories() {
        if (!this.selectedAgent) return;
        
        try {
            const memories = await this.apiCall(`/api/agents/${this.selectedAgent}/memories`);
            this.displayMemories(memories);
        } catch (error) {
            console.error('Failed to load memories:', error);
            console.log('Memories not available for this agent');
        }
    }
    
    // UI Management Methods
    
    populateAgentSelect() {
        const select = document.getElementById('agent-select');
        select.innerHTML = '<option value="">Select an AI agent...</option>';
        
        this.agents.forEach(agent => {
            const option = document.createElement('option');
            option.value = agent.agent;
            option.textContent = `${agent.agent} - ${agent.description}`;
            select.appendChild(option);
        });
        
        select.disabled = false;
    }
    
    onAgentSelected(agentName) {
        if (!agentName) {
            this.selectedAgent = null;
            this.updateAgentInfo(null);
            this.updateChatHeader('Select an Agent');
            this.clearChat();
            this.disableMessageInput();
            return;
        }
        
        this.selectedAgent = agentName;
        const agent = this.agents.find(a => a.agent === agentName);
        
        if (agent) {
            this.updateAgentInfo(agent);
            this.updateChatHeader(agent.agent);
            this.enableMessageInput();
            this.loadMessages();
            this.loadAgentMemories();
            
            // Start auto-refresh for messages
            this.startMessageRefresh();
        }
    }
    
    updateAgentInfo(agent) {
        if (!agent) {
            document.getElementById('agent-description').textContent = 'Select an agent to view details';
            document.getElementById('agent-model').textContent = '-';
            document.getElementById('agent-api').textContent = '-';
            return;
        }
        
        document.getElementById('agent-description').textContent = agent.description;
        document.getElementById('agent-model').textContent = agent.model;
        document.getElementById('agent-api').textContent = agent.model_api;
    }
    
    updateChatHeader(agentName) {
        document.getElementById('chat-agent-name').textContent = agentName;
    }
    
    displayMessages() {
        const chatContainer = document.getElementById('chat-messages');
        chatContainer.innerHTML = '';
        
        if (this.messages.length === 0) {
            chatContainer.innerHTML = `
                <div class="welcome-message">
                    <p>💬 Start a conversation with ${this.selectedAgent}!</p>
                    <p>Try asking about data analysis, database queries, or generating reports.</p>
                </div>
            `;
            return;
        }
        
        // Sort messages by posted time (oldest first)
        const sortedMessages = [...this.messages].sort((a, b) => 
            new Date(a.posted) - new Date(b.posted)
        );
        
        sortedMessages.forEach(message => {
            this.addMessageToChat(message, false);
        });
        
        // Scroll to bottom
        this.scrollChatToBottom();
    }
    
    addMessageToChat(message, animate = true) {
        const chatContainer = document.getElementById('chat-messages');
        
        // Remove welcome message if present
        const welcomeMsg = chatContainer.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        const isFromUser = message.user_from === this.currentUser;
        const messageEl = document.createElement('div');
        messageEl.className = `message ${isFromUser ? 'user' : 'agent'}`;
        
        if (animate) {
            messageEl.classList.add('fade-in');
        }
        
        const avatar = this.getAvatarInitials(isFromUser ? this.currentUser : message.user_from);
        const time = this.formatTime(message.posted);
        
        messageEl.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${this.formatMessageText(message.message)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        chatContainer.appendChild(messageEl);
        
        if (animate) {
            this.scrollChatToBottom();
        }
    }
    
    formatMessageText(text) {
        // Basic text formatting - escape HTML and handle line breaks
        const escaped = text.replace(/&/g, '&amp;')
                           .replace(/</g, '&lt;')
                           .replace(/>/g, '&gt;')
                           .replace(/\n/g, '<br>');
        
        // Check if the message contains tabular data (basic detection)
        if (this.containsTabularData(text)) {
            this.showQueryResults(text);
        }
        
        return escaped;
    }
    
    containsTabularData(text) {
        // Simple heuristic to detect if message contains structured data
        const lines = text.split('\n');
        if (lines.length < 3) return false;
        
        // Look for patterns like CSV or pipe-separated data
        const hasSeparators = lines.some(line => 
            line.includes('|') || line.includes(',') || line.includes('\t')
        );
        
        return hasSeparators;
    }
    
    showQueryResults(data) {
        // This would be called when an agent returns query results
        const resultsSection = document.getElementById('results-section');
        const resultsContent = document.getElementById('results-content');
        
        try {
            // Try to parse as JSON first
            const parsedData = JSON.parse(data);
            if (Array.isArray(parsedData)) {
                resultsContent.innerHTML = this.createDataTable(parsedData);
                resultsSection.style.display = 'block';
                return;
            }
        } catch (e) {
            // Not JSON, try to parse as CSV-like data
            const table = this.parseTextToTable(data);
            if (table) {
                resultsContent.innerHTML = table;
                resultsSection.style.display = 'block';
            }
        }
    }
    
    createDataTable(data) {
        if (!data || data.length === 0) {
            return '<p>No data to display</p>';
        }
        
        const columns = Object.keys(data[0]);
        
        let html = '<table class="data-table"><thead><tr>';
        columns.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const value = row[col];
                html += `<td>${value !== null && value !== undefined ? value : ''}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    parseTextToTable(text) {
        const lines = text.split('\n').filter(line => line.trim());
        if (lines.length < 2) return null;
        
        // Detect delimiter
        const delimiters = ['|', ',', '\t'];
        let delimiter = null;
        
        for (const del of delimiters) {
            if (lines[0].includes(del)) {
                delimiter = del;
                break;
            }
        }
        
        if (!delimiter) return null;
        
        let html = '<table class="data-table"><thead><tr>';
        const headers = lines[0].split(delimiter).map(h => h.trim());
        
        headers.forEach(header => {
            html += `<th>${header}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        lines.slice(1).forEach(line => {
            const cells = line.split(delimiter).map(c => c.trim());
            html += '<tr>';
            cells.forEach(cell => {
                html += `<td>${cell}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    displayMemories(memories) {
        const memoryList = document.getElementById('memory-list');
        
        if (!memories || memories.length === 0) {
            memoryList.innerHTML = '<p class="no-memories">No memories available for this agent</p>';
            return;
        }
        
        memoryList.innerHTML = '';
        
        memories.forEach(memory => {
            const memoryEl = document.createElement('div');
            memoryEl.className = 'memory-item';
            
            const tags = memory.Related_To ? memory.Related_To.split(' ') : [];
            const tagHtml = tags.map(tag => `<span class="memory-tag">${tag}</span>`).join('');
            
            memoryEl.innerHTML = `
                <div class="memory-label">${memory.Memory_Label}</div>
                <div class="memory-text">${memory.Memory}</div>
                <div class="memory-tags">${tagHtml}</div>
                <div class="memory-time text-muted">
                    Recalled ${memory.Times_Recalled} times | 
                    Last: ${memory.Last_Recalled ? this.formatTime(memory.Last_Recalled) : 'Never'}
                </div>
            `;
            
            memoryList.appendChild(memoryEl);
        });
    }
    
    getAvatarInitials(name) {
        return name ? name.substring(0, 2).toUpperCase() : 'AI';
    }
    
    formatTime(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return 'Now';
        }
    }
    
    // UI State Management
    
    enableMessageInput() {
        const input = document.getElementById('message-input');
        const button = document.getElementById('send-button');
        
        input.disabled = false;
        button.disabled = false;
        input.placeholder = `Type your message to ${this.selectedAgent}...`;
    }
    
    disableMessageInput() {
        const input = document.getElementById('message-input');
        const button = document.getElementById('send-button');
        
        input.disabled = true;
        button.disabled = true;
        input.placeholder = 'Select an agent to start messaging...';
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        const button = document.getElementById('send-button');
        const spinner = button.querySelector('.btn-spinner');
        const text = button.querySelector('.btn-text');
        
        if (loading) {
            spinner.style.display = 'inline';
            text.textContent = 'Sending...';
            button.disabled = true;
        } else {
            spinner.style.display = 'none';
            text.textContent = 'Send';
            button.disabled = !this.selectedAgent;
        }
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = show ? 'flex' : 'none';
    }
    
    updateConnectionStatus(status) {
        const statusEl = document.getElementById('connection-status');
        const dot = statusEl.querySelector('.status-dot');
        const text = statusEl.querySelector('.status-text');
        
        if (status === 'connected') {
            dot.classList.remove('disconnected');
            text.textContent = 'Connected';
        } else {
            dot.classList.add('disconnected');
            text.textContent = 'Disconnected';
        }
    }
    
    clearChat() {
        const chatContainer = document.getElementById('chat-messages');
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <p>👋 Welcome to TriAI! Select an AI agent above to start chatting.</p>
                <p>Your AI agents can help with data analysis, database queries, and report generation.</p>
            </div>
        `;
    }
    
    scrollChatToBottom() {
        const chatContainer = document.getElementById('chat-messages');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    showError(message) {
        // Simple error display - could be enhanced with a toast system
        console.error(message);
        alert(message);
    }
    
    // Auto-refresh functionality
    
    startMessageRefresh() {
        this.stopMessageRefresh();
        this.messageRefreshInterval = setInterval(() => {
            if (this.selectedAgent && !this.isLoading) {
                this.loadMessages();
            }
        }, 5000); // Refresh every 5 seconds
    }
    
    stopMessageRefresh() {
        if (this.messageRefreshInterval) {
            clearInterval(this.messageRefreshInterval);
            this.messageRefreshInterval = null;
        }
    }
    
    // Event Listeners Setup
    
    setupEventListeners() {
        // Agent selection
        document.getElementById('agent-select').addEventListener('change', (e) => {
            this.onAgentSelected(e.target.value);
        });
        
        // Refresh agents
        document.getElementById('refresh-agents').addEventListener('click', () => {
            this.loadAgents();
        });
        
        // Send message
        document.getElementById('send-button').addEventListener('click', () => {
            const input = document.getElementById('message-input');
            this.sendMessage(input.value);
        });
        
        // Send message on Ctrl+Enter
        document.getElementById('message-input').addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.sendMessage(e.target.value);
            }
        });
        
        // Clear chat
        document.getElementById('clear-chat').addEventListener('click', () => {
            this.clearChat();
        });
        
        // Refresh messages
        document.getElementById('refresh-messages').addEventListener('click', () => {
            this.loadMessages();
        });
        
        // Close results
        document.getElementById('close-results').addEventListener('click', () => {
            document.getElementById('results-section').style.display = 'none';
        });
        
        // Toggle memory panel
        document.getElementById('toggle-memory').addEventListener('click', (e) => {
            const content = document.getElementById('memory-content');
            const button = e.target;
            
            if (content.style.display === 'none' || !content.style.display) {
                content.style.display = 'block';
                button.textContent = 'Hide';
                if (this.selectedAgent) {
                    this.loadAgentMemories();
                }
            } else {
                content.style.display = 'none';
                button.textContent = 'Show';
            }
        });
        
        // Handle window beforeunload
        window.addEventListener('beforeunload', () => {
            this.stopMessageRefresh();
        });
        
        // Handle visibility change (pause refresh when tab not visible)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopMessageRefresh();
            } else if (this.selectedAgent) {
                this.startMessageRefresh();
            }
        });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.triaiClient = new TriAIClient();
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
});