const canvas = document.getElementById('snake-board');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score-value');
const levelElement = document.getElementById('level-value');
const newGameBtn = document.getElementById('new-game-btn');

const ROWS = 20;
const COLS = 20;
const BLOCK_SIZE = 20;

canvas.width = COLS * BLOCK_SIZE;
canvas.height = ROWS * BLOCK_SIZE;

let snake = [{x: 10, y: 10}];
let food = null;
let direction = {x: 1, y: 0};
let score = 0;
let level = 1;
let gameInterval = null;
let gameSpeed = 200;
let gameRunning = false;

function drawBlock(x, y, color) {
    ctx.fillStyle = color;
    ctx.fillRect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.strokeRect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
}

function drawSnake() {
    snake.forEach((segment, index) => {
        const color = index === 0 ? '#00ff00' : '#008000';
        drawBlock(segment.x, segment.y, color);
    });
}

function drawFood() {
    if (food) {
        drawBlock(food.x, food.y, '#ff0000');
    }
}

function drawGrid() {
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

function spawnFood() {
    food = {
        x: Math.floor(Math.random() * COLS),
        y: Math.floor(Math.random() * ROWS)
    };
    while (snake.some(segment => segment.x === food.x && segment.y === food.y)) {
        food = {
            x: Math.floor(Math.random() * COLS),
            y: Math.floor(Math.random() * ROWS)
        };
    }
}

function moveSnake() {
    const head = {x: snake[0].x + direction.x, y: snake[0].y + direction.y};
    
    // Wrap around the board
    head.x = (head.x + COLS) % COLS;
    head.y = (head.y + ROWS) % ROWS;
    
    snake.unshift(head);

    if (head.x === food.x && head.y === food.y) {
        score += 10;
        scoreElement.textContent = score;
        if (score >= level * 100) {
            level++;
            levelElement.textContent = level;
            gameSpeed = Math.max(50, 200 - (level - 1) * 10);
            clearInterval(gameInterval);
            gameInterval = setInterval(gameLoop, gameSpeed);
        }
        spawnFood();
    } else {
        snake.pop();
    }
}

function checkCollision() {
    const head = snake[0];
    for (let i = 1; i < snake.length; i++) {
        if (snake[i].x === head.x && snake[i].y === head.y) {
            return true;
        }
    }
    return false;
}

function gameLoop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawGrid();
    moveSnake();
    if (checkCollision()) {
        endGame();
        return;
    }
    drawSnake();
    drawFood();
}

function resetGame() {
    snake = [{x: 10, y: 10}];
    direction = {x: 1, y: 0};
    score = 0;
    level = 1;
    gameSpeed = 200;
    scoreElement.textContent = score;
    levelElement.textContent = level;
    spawnFood();
}

function startGame() {
    if (gameRunning) return;
    resetGame();
    gameRunning = true;
    gameInterval = setInterval(gameLoop, gameSpeed);
    newGameBtn.textContent = "Restart Game";
}

function endGame() {
    clearInterval(gameInterval);
    gameRunning = false;
    alert('Game Over! Your score: ' + score);
    newGameBtn.textContent = "New Game";
}

function handleKeyPress(event) {
    if (!gameRunning) return;
    
    // Prevent default behavior only for arrow keys
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
        event.preventDefault();
    }

    switch (event.key) {
        case 'ArrowLeft':
            if (direction.x === 0) direction = {x: -1, y: 0};
            break;
        case 'ArrowRight':
            if (direction.x === 0) direction = {x: 1, y: 0};
            break;
        case 'ArrowUp':
            if (direction.y === 0) direction = {x: 0, y: -1};
            break;
        case 'ArrowDown':
            if (direction.y === 0) direction = {x: 0, y: 1};
            break;
    }
}

// Use capturing phase to intercept events before they reach the parent document
document.addEventListener('keydown', handleKeyPress, true);
newGameBtn.addEventListener('click', startGame);

// Initial draw
drawGrid();