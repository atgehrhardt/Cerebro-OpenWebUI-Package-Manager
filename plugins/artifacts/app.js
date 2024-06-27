function renderArtifact(content) {
    document.getElementById('artifactContent').textContent = content;
}

function fetchArtifactContent(fileId) {
    console.log(`Attempting to fetch content for file ID: ${fileId}`);
    fetch(`/api/v1/files/${fileId}/content`)
        .then(response => {
            console.log(`Received response with status: ${response.status}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(content => {
            console.log("Fetched content:", content);
            if (content.trim() === '') {
                console.warn("Fetched content is empty");
                renderArtifact('Fetched content is empty');
            } else {
                renderArtifact(content);
            }
        })
        .catch(error => {
            console.error('Error fetching artifact content:', error);
            renderArtifact(`Error loading artifact content: ${error.message}`);
        });
}

window.onload = function() {
    console.log("Artifacts renderer iframe loaded. Origin:", window.location.origin);
    console.log("Full URL:", window.location.href);
    const urlParams = new URLSearchParams(window.location.search);
    const fileId = urlParams.get('file');
    if (fileId) {
        console.log("File ID found:", fileId);
        fetchArtifactContent(fileId);
    } else {
        console.log("No file ID provided");
        renderArtifact('No artifact content available');
    }
}