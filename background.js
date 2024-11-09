console.log("Background script loaded111");

chrome.action.onClicked.addListener((tab) => {
    console.log('Action clicked for tab:', tab.id);
    chrome.sidePanel.open({ tabId: tab.id });
  });
  
  chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .then(() => console.log('Panel behavior set successfully'))
    .catch((error) => console.error('Error setting panel behavior:', error));

chrome.tabs.onActivated.addListener(function(activeInfo) {
    chrome.tabs.get(activeInfo.tabId, function(tab) {
        console.log("Tab switched to:", tab.url);
        console.log("Detected with tabs.onActivated")
        chrome.runtime.sendMessage({
            action: "newActivity",
            url: tab.url
        }, response => {
            if (chrome.runtime.lastError) {
                console.error("Error sending message:", chrome.runtime.lastError);
            } else {
                console.log("Message sent to sidepanel, response:", response);
            }
        });
    });
});