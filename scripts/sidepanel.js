document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    let conversationHistory = [];

    function addMessage(message, isUser) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(isUser ? 'user-message' : 'ai-message');
        
        const paragraphElement = document.createElement('p');
        paragraphElement.textContent = message;
        
        messageElement.appendChild(paragraphElement);
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Add message to conversation history
        conversationHistory.push({
            role: isUser ? 'user' : 'assistant',
            content: message
        });
    }

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            addMessage(message, true);
            messageInput.value = '';

            // Prepare the request body
            const requestBody = {
                message: message,
                conversation_history: conversationHistory
            };

            // Make the API call
            fetch('http://localhost:3000/chat_api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Change 'data.response' to 'data.reply'
                addMessage(data.reply, false);
            })
            .catch(error => {
                console.error('Error:', error);
                let errorMessage = 'Sorry, there was an error processing your request.';
                
                if (error.message.includes('HTTP error! status: 404')) {
                    errorMessage = 'Sorry, the chat service is not available right now. Please try again later.';
                } else if (error.message.includes('Failed to fetch')) {
                    errorMessage = 'Unable to connect to the chat service. Please check your internet connection and try again.';
                } else if (error instanceof SyntaxError) {
                    errorMessage = 'Received an invalid response from the server. Please try again later.';
                }
                
                addMessage(errorMessage, false);
            });
        }
    }

    function sendActivityAlert(activity) {
        console.log("Sending activity alert:", activity);
        const alertMessage = `<ACTIVITY ALERT: ${activity}>`;
        
        // Prepare the request body
        const requestBody = {
            message: alertMessage,
            conversation_history: conversationHistory
        };

        // Make the API call
        fetch('http://localhost:3000/chat_api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Activity alert response:", data);
            addMessage(data.reply, false);
        })
        .catch(error => {
            console.error('Error:', error);
            // Handle error (you can reuse the error handling from sendMessage function)
        });
    }

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Add this at the end of the DOMContentLoaded event listener
    let activityTimer = null;
    let lastActivity = null;
    let lastActivityTime = null;
    let currActivityTime = null;

    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        console.log("Message received in sidepanel:", request);
        if (lastActivityTime == null) {
            lastActivityTime = Date.now() - 10000; // set it to 10 seconds ago because we don't want to skip the first alert
        }
        if (request.action === "newActivity") {
            clearTimeout(activityTimer);
            lastActivity = request.url;
            currActivityTime = Date.now();
            activityTimer = setTimeout(() => {
                if (Date.now() - lastActivityTime >= 10000) {
                    sendActivityAlert(lastActivity);
                    lastActivityTime = currActivityTime;
                }
            }, 10000); // 10 seconds
        }
        sendResponse({received: true}); // Send a response back to the background script
    });

    console.log("Sidepanel script loaded");
});