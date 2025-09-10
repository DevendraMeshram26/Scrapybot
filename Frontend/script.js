async function sendMessage() {
    let userInput = document.getElementById("user-input").value;
    let chatBox = document.getElementById("chat-box");
    
    if (!userInput.trim()) return;
    
    chatBox.innerHTML += `<div class="user-message">${userInput}</div>`;
    document.getElementById("user-input").value = '';

    try {
        let response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({ query: userInput })
        });
        
        let data = await response.json();
        chatBox.innerHTML += `<div class="${data.error ? 'error-message' : 'bot-message'}">${data.error || data.answer}</div>`;
    } catch (error) {
        chatBox.innerHTML += `<div class="error-message">Network error: ${error.message}</div>`;
    }
    
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function scrapeWebsite() {
    const urlInput = document.getElementById("url-input").value;
    const chatBox = document.getElementById("chat-box");
    
    if (!urlInput.trim()) {
        chatBox.innerHTML += `<div class="error-message">Please enter a URL</div>`;
        return;
    }

    try {
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'bot-message';
        loadingMessage.textContent = 'Scraping website, please wait...';
        chatBox.appendChild(loadingMessage);
        
        const response = await fetch('/scrape', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({ url: urlInput })
        });
        
        loadingMessage.remove();
        const data = await response.json();
        
        chatBox.innerHTML += `<div class="${data.error ? 'error-message' : 'bot-message'}">${data.error || 'Website scraped successfully!'}</div>`;
        if (data.summary) {
            chatBox.innerHTML += `<div class="bot-message">Summary: ${data.summary}</div>`;
        }
    } catch (error) {
        chatBox.innerHTML += `<div class="error-message">Network error: ${error.message}</div>`;
    }
    
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById("user-input");
    const urlInput = document.getElementById("url-input");
    
    // Enter key handler for chat input
    userInput.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });
    
    // Enter key handler for URL input
    urlInput.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            scrapeWebsite();
        }
    });
});
