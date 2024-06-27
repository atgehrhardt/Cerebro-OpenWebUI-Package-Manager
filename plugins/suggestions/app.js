function sendPrompt() {
    const promptText = document.getElementById('promptInput').value;
    console.log("Sending prompt:", promptText);
    
    window.parent.postMessage({
        type: 'input:prompt',
        text: promptText
    }, window.location.origin);
}

function submitPrompt() {
    console.log("Submitting prompt");
    
    window.parent.postMessage({
        type: 'action:submit',
        text: 'Submitting prompt'
    }, window.location.origin);
}

function sendAndSubmitPrompt() {
    sendPrompt();
    setTimeout(submitPrompt, 100); // Small delay to ensure the prompt is set before submitting
}

// Log when the iframe is loaded
window.onload = function() {
    console.log("Iframe loaded. Origin:", window.location.origin);
}