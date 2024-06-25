const canvas = document.getElementById('tetris-board');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score-value');
const levelElement = document.getElementById('level-value');

const ROWS = 20;
const COLS = 10;
const BLOCK_SIZE = 15;

canvas.width = COLS * BLOCK_SIZE;
canvas.height = ROWS * BLOCK_SIZE;

const COLORS = [
    '#ff00ff', '#00ffff', '#ffff00', '#ff0000', '#00ff00', '#0000ff', '#ff8000'
];

let board = Array(ROWS).fill().map(() => Array(COLS).fill(0));
let currentPiece = null;
let score = 0;
let level = 1;
let dropCounter = 0;
let dropInterval = 1000;

const SHAPES = [
    [[1, 1, 1, 1]],
    [[1, 1], [1, 1]],
    [[1, 1, 1], [0, 1, 0]],
    [[1, 1, 1], [1, 0, 0]],
    [[1, 1, 1], [0, 0, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]]
];

function createPiece() {
    const shape = SHAPES[Math.floor(Math.random() * SHAPES.length)];
    const color = COLORS[Math.floor(Math.random() * COLORS.length)];
    return {
        shape,
        color,
        x: Math.floor(COLS / 2) - Math.floor(shape[0].length / 2),
        y: 0
    };
}

function drawBlock(x, y, color) {
    ctx.fillStyle = color;
    ctx.fillRect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.strokeRect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
    
    // Add glow effect
    ctx.shadowColor = color;
    ctx.shadowBlur = 5;
    ctx.fillRect(x * BLOCK_SIZE + 1, y * BLOCK_SIZE + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2);
    ctx.shadowBlur = 0;
}

function drawBoard() {
    for (let y = 0; y < ROWS; y++) {
        for (let x = 0; x < COLS; x++) {
            if (board[y][x]) {
                drawBlock(x, y, board[y][x]);
            }
        }
    }
}

function drawGridlines() {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 0.5;
    for (let y = 0; y <= ROWS; y++) {
        ctx.beginPath();
        ctx.moveTo(0, y * BLOCK_SIZE);
        ctx.lineTo(COLS * BLOCK_SIZE, y * BLOCK_SIZE);
        ctx.stroke();
    }
    for (let x = 0; x <= COLS; x++) {
        ctx.beginPath();
        ctx.moveTo(x * BLOCK_SIZE, 0);
        ctx.lineTo(x * BLOCK_SIZE, ROWS * BLOCK_SIZE);
        ctx.stroke();
    }
}

function drawPiece() {
    currentPiece.shape.forEach((row, y) => {
        row.forEach((value, x) => {
            if (value) {
                drawBlock(currentPiece.x + x, currentPiece.y + y, currentPiece.color);
            }
        });
    });
}

function collision() {
    return currentPiece.shape.some((row, y) => {
        return row.some((value, x) => {
            const boardX = currentPiece.x + x;
            const boardY = currentPiece.y + y;
            return value && (boardY >= ROWS || boardX < 0 || boardX >= COLS || board[boardY][boardX]);
        });
    });
}

function mergePiece() {
    currentPiece.shape.forEach((row, y) => {
        row.forEach((value, x) => {
            if (value) {
                board[currentPiece.y + y][currentPiece.x + x] = currentPiece.color;
            }
        });
    });
}

function removeRows() {
    let rowsCleared = 0;
    for (let y = ROWS - 1; y >= 0; y--) {
        if (board[y].every(cell => cell !== 0)) {
            board.splice(y, 1);
            board.unshift(Array(COLS).fill(0));
            rowsCleared++;
            y++;
        }
    }
    if (rowsCleared > 0) {
        score += rowsCleared * 100 * level;
        scoreElement.textContent = score;
        if (score >= level * 500) {
            level++;
            levelElement.textContent = level;
            dropInterval = Math.max(100, 1000 - (level - 1) * 100);
        }
    }
}

function rotate() {
    const rotated = currentPiece.shape[0].map((_, i) =>
        currentPiece.shape.map(row => row[i]).reverse()
    );
    const previousShape = currentPiece.shape;
    currentPiece.shape = rotated;
    if (collision()) {
        currentPiece.shape = previousShape;
    }
}

function moveDown() {
    currentPiece.y++;
    if (collision()) {
        currentPiece.y--;
        mergePiece();
        removeRows();
        currentPiece = createPiece();
        if (collision()) {
            alert('Game Over! Your score: ' + score);
            board = Array(ROWS).fill().map(() => Array(COLS).fill(0));
            score = 0;
            level = 1;
            dropInterval = 1000;
            scoreElement.textContent = score;
            levelElement.textContent = level;
        }
    }
    dropCounter = 0;
}

function moveToBottom() {
    while (!collision()) {
        currentPiece.y++;
    }
    currentPiece.y--;
    mergePiece();
    removeRows();
    currentPiece = createPiece();
    if (collision()) {
        alert('Game Over! Your score: ' + score);
        board = Array(ROWS).fill().map(() => Array(COLS).fill(0));
        score = 0;
        level = 1;
        dropInterval = 1000;
        scoreElement.textContent = score;
        levelElement.textContent = level;
    }
}

function moveLeft() {
    currentPiece.x--;
    if (collision()) {
        currentPiece.x++;
    }
}

function moveRight() {
    currentPiece.x++;
    if (collision()) {
        currentPiece.x--;
    }
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawGridlines();
    drawBoard();
    drawPiece();
}

let lastTime = 0;
function gameLoop(time = 0) {
    const deltaTime = time - lastTime;
    lastTime = time;

    dropCounter += deltaTime;
    if (dropCounter > dropInterval) {
        moveDown();
    }

    draw();
    requestAnimationFrame(gameLoop);
}

function handleKeyPress(event) {
    event.preventDefault();
    event.stopPropagation();
    console.log('Key captured: ' + event.key);

    switch (event.key) {
        case 'ArrowLeft':
            moveLeft();
            break;
        case 'ArrowRight':
            moveRight();
            break;
        case 'ArrowDown':
            moveDown();
            break;
        case 'ArrowUp':
            moveToBottom();
            break;
        case ' ':
            rotate();
            break;
    }
}

window.addEventListener('keydown', handleKeyPress, true);
window.addEventListener('keyup', (event) => {
    event.preventDefault();
    event.stopPropagation();
}, true);

currentPiece = createPiece();
gameLoop();