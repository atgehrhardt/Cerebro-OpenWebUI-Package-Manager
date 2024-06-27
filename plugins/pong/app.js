const canvas = document.getElementById('pong-board');
const ctx = canvas.getContext('2d');
const playerScoreElement = document.getElementById('player-score');
const aiScoreElement = document.getElementById('ai-score');
const newGameBtn = document.getElementById('new-game-btn');

const PADDLE_WIDTH = 10;
const PADDLE_HEIGHT = 80;
const BALL_SIZE = 10;
const BALL_SPEED = 6;
const AI_SPEED = 3;

canvas.width = 600;
canvas.height = 400;

let playerPaddle = { x: 10, y: canvas.height / 2 - PADDLE_HEIGHT / 2 };
let aiPaddle = { x: canvas.width - PADDLE_WIDTH - 10, y: canvas.height / 2 - PADDLE_HEIGHT / 2 };
let ball = { x: canvas.width / 2, y: canvas.height / 2, dx: BALL_SPEED, dy: BALL_SPEED };
let playerScore = 0;
let aiScore = 0;
let gameInterval = null;
let gameRunning = false;

function drawRect(x, y, width, height, color) {
    ctx.fillStyle = color;
    ctx.fillRect(x, y, width, height);
}

function drawCircle(x, y, radius, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2, false);
    ctx.fill();
}

function drawNet() {
    for (let i = 0; i <= canvas.height; i += 20) {
        drawRect(canvas.width / 2 - 1, i, 2, 15, '#ecf0f1');
    }
}

function draw() {
    drawRect(0, 0, canvas.width, canvas.height, '#000');
    drawNet();
    drawRect(playerPaddle.x, playerPaddle.y, PADDLE_WIDTH, PADDLE_HEIGHT, '#ecf0f1');
    drawRect(aiPaddle.x, aiPaddle.y, PADDLE_WIDTH, PADDLE_HEIGHT, '#ecf0f1');
    drawCircle(ball.x, ball.y, BALL_SIZE / 2, '#ecf0f1');
}

function movePaddle(paddle, y) {
    paddle.y = Math.max(0, Math.min(canvas.height - PADDLE_HEIGHT, y));
}

function updateAI() {
    const paddleCenter = aiPaddle.y + PADDLE_HEIGHT / 2;
    if (paddleCenter < ball.y - 35) {
        aiPaddle.y += AI_SPEED;
    } else if (paddleCenter > ball.y + 35) {
        aiPaddle.y -= AI_SPEED;
    }
}

function updateBall() {
    ball.x += ball.dx;
    ball.y += ball.dy;

    if (ball.y - BALL_SIZE / 2 < 0 || ball.y + BALL_SIZE / 2 > canvas.height) {
        ball.dy *= -1;
    }

    if (
        (ball.dx < 0 && ball.x - BALL_SIZE / 2 < playerPaddle.x + PADDLE_WIDTH && ball.y > playerPaddle.y && ball.y < playerPaddle.y + PADDLE_HEIGHT) ||
        (ball.dx > 0 && ball.x + BALL_SIZE / 2 > aiPaddle.x && ball.y > aiPaddle.y && ball.y < aiPaddle.y + PADDLE_HEIGHT)
    ) {
        ball.dx *= -1;
        const paddleCenter = (ball.dx < 0 ? playerPaddle.y : aiPaddle.y) + PADDLE_HEIGHT / 2;
        const relativeIntersectY = (ball.y - paddleCenter) / (PADDLE_HEIGHT / 2);
        ball.dy = BALL_SPEED * relativeIntersectY;
    }

    if (ball.x - BALL_SIZE / 2 < 0) {
        aiScore++;
        aiScoreElement.textContent = aiScore;
        resetBall();
    } else if (ball.x + BALL_SIZE / 2 > canvas.width) {
        playerScore++;
        playerScoreElement.textContent = playerScore;
        resetBall();
    }
}

function resetBall() {
    ball.x = canvas.width / 2;
    ball.y = canvas.height / 2;
    ball.dx = -ball.dx;
    ball.dy = Math.random() * BALL_SPEED * 2 - BALL_SPEED;
}

function gameLoop() {
    updateAI();
    updateBall();
    draw();
}

function stopGame() {
    clearInterval(gameInterval);
    gameRunning = false;
    newGameBtn.textContent = "New Game";
}

function startGame() {
    if (gameRunning) {
        stopGame();
    }
    resetGame();
    gameRunning = true;
    gameInterval = setInterval(gameLoop, 1000 / 60);
    newGameBtn.textContent = "Restart Game";
}

function resetGame() {
    stopGame();
    playerPaddle = { x: 10, y: canvas.height / 2 - PADDLE_HEIGHT / 2 };
    aiPaddle = { x: canvas.width - PADDLE_WIDTH - 10, y: canvas.height / 2 - PADDLE_HEIGHT / 2 };
    ball = { x: canvas.width / 2, y: canvas.height / 2, dx: BALL_SPEED, dy: BALL_SPEED };
    playerScore = 0;
    aiScore = 0;
    playerScoreElement.textContent = playerScore;
    aiScoreElement.textContent = aiScore;
}

function handleMouseMove(event) {
    if (!gameRunning) return;
    const rect = canvas.getBoundingClientRect();
    const mouseY = event.clientY - rect.top;
    movePaddle(playerPaddle, mouseY - PADDLE_HEIGHT / 2);
}

canvas.addEventListener('mousemove', handleMouseMove);
newGameBtn.addEventListener('click', startGame);

canvas.addEventListener('mouseenter', () => {
    canvas.style.cursor = 'none';
});

canvas.addEventListener('mouseleave', () => {
    canvas.style.cursor = 'default';
});

draw();