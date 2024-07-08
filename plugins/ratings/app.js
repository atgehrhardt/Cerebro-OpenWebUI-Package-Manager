function showModal() {
    document.getElementById('myModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('myModal').style.display = 'none';
}

// Close the modal if clicked outside of it
window.onclick = function(event) {
    var modal = document.getElementById('myModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// Log when the iframe is loaded
window.onload = function() {
    console.log("Ratings applet loaded. Origin:", window.location.origin);
}