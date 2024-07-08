function consumeEvent(event) {
    event.preventDefault();
    event.stopPropagation();
    console.log('Key captured: ' + event.key);
}

window.addEventListener('keydown', consumeEvent, true);
window.addEventListener('keyup', consumeEvent, true);