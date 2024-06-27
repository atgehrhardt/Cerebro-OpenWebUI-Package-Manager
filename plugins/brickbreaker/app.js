const canvas = document.getElementById('brickbreaker-board');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score');
const livesElement = document.getElementById('lives');
const newGameBtn = document.getElementById('new-game-btn');

const PADDLE_WIDTH = 100;
const PADDLE_HEIGHT = 10;
const BALL_RADIUS = 8;
const BRICK_ROWS = 5;
const BRICK_COLS = 8;
const BRICK_WIDTH = 60;
const BRICK_HEIGHT = 20;
const BRICK_PADDING = 10;
const BRICK_OFFSET_TOP = 30;
const BRICK_OFFSET_LEFT = 30;

canvas.width = 600;
canvas.height = 400;

let paddle = { x: canvas.width / 2 - PADDLE_WIDTH / 2, y: canvas.height - PADDLE_HEIGHT - 10 };
let ball = { x: canvas.width / 2, y: canvas.height - 30, dx: 4, dy: -4 };
let bricks = [];
let score = 0;
let lives = 3;
let gameInterval = null;
let gameRunning = false;

const neonColors = ['#ff00ff', '#00ffff', '#ffff00', '#ff3300', '#33ff00'];

function createBricks() {
    for (let c = 0; c < BRICK_COLS; c++) {
        bricks[c] = [];
        for (let r = 0; r < BRICK_ROWS; r++) {
            bricks[c][r] = { x: 0, y: 0, status: 1, color: neonColors[Math.floor(Math.random() * neonColors.length)] };
        }
    }
}

function drawBricks() {
    for (let c = 0; c < BRICK_COLS; c++) {
        for (let r = 0; r < BRICK_ROWS; r++) {
            if (bricks[c][r].status === 1) {
                const brickX = c * (BRICK_WIDTH + BRICK_PADDING) + BRICK_OFFSET_LEFT;
                const brickY = r * (BRICK_HEIGHT + BRICK_PADDING) + BRICK_OFFSET_TOP;
                bricks[c][r].x = brickX;
                bricks[c][r].y = brickY;
                ctx.fillStyle = bricks[c][r].color;
                ctx.fillRect(brickX, brickY, BRICK_WIDTH, BRICK_HEIGHT);
                ctx.shadowBlur = 10;
                ctx.shadowColor = bricks[c][r].color;
                ctx.strokeStyle = '#fff';
                ctx.strokeRect(brickX, brickY, BRICK_WIDTH, BRICK_HEIGHT);
            }
        }
    }
    ctx.shadowBlur = 0;
}

function drawPaddle() {
    ctx.fillStyle = '#00ffff';
    ctx.fillRect(paddle.x, paddle.y, PADDLE_WIDTH, PADDLE_HEIGHT);
    ctx.shadowBlur = 10;
    ctx.shadowColor = '#00ffff';
    ctx.strokeStyle = '#fff';
    ctx.strokeRect(paddle.x, paddle.y, PADDLE_WIDTH, PADDLE_HEIGHT);
    ctx.shadowBlur = 0;
}

function drawBall() {
    ctx.beginPath();
    ctx.arc(ball.x, ball.y, BALL_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.shadowBlur = 10;
    ctx.shadowColor = '#ffffff';
    ctx.strokeStyle = '#00ffff';
    ctx.stroke();
    ctx.closePath();
    ctx.shadowBlur = 0;
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawBricks();
    drawPaddle();
    drawBall();
}

function movePaddle(x) {
    paddle.x = Math.max(0, Math.min(canvas.width - PADDLE_WIDTH, x - PADDLE_WIDTH / 2));
}

function collisionDetection() {
    for (let c = 0; c < BRICK_COLS; c++) {
        for (let r = 0; r < BRICK_ROWS; r++) {
            const b = bricks[c][r];
            if (b.status === 1) {
                if (ball.x > b.x && ball.x < b.x + BRICK_WIDTH && ball.y > b.y && ball.y < b.y + BRICK_HEIGHT) {
                    ball.dy = -ball.dy;
                    b.status = 0;
                    score++;
                    scoreElement.textContent = score;
                    if (score === BRICK_ROWS * BRICK_COLS) {
                        alert('Congratulations! You win!');
                        stopGame();
                    }
                }
            }
        }
    }
}

function updateBall() {
    ball.x += ball.dx;
    ball.y += ball.dy;

    // Wall collision
    if (ball.x - BALL_RADIUS < 0 || ball.x + BALL_RADIUS > canvas.width) {
        ball.dx = -ball.dx;
    }
    if (ball.y - BALL_RADIUS < 0) {
        ball.dy = -ball.dy;
    }

    // Paddle collision
    if (ball.y + BALL_RADIUS > paddle.y && ball.y - BALL_RADIUS < paddle.y + PADDLE_HEIGHT &&
        ball.x > paddle.x && ball.x < paddle.x + PADDLE_WIDTH) {
        let hitPos = (ball.x - paddle.x) / PADDLE_WIDTH;
        ball.dx = 8 * (hitPos - 0.5);
        ball.dy = -Math.abs(ball.dy); // Ensure the ball always goes up after hitting the paddle
        ball.y = paddle.y - BALL_RADIUS; // Adjust ball position to prevent it from going through the paddle
    }

    // Ball out of bounds
    if (ball.y + BALL_RADIUS > canvas.height) {
        lives--;
        livesElement.textContent = lives;
        if (lives === 0) {
            alert('Game Over');
            stopGame();
        } else {
            ball.x = canvas.width / 2;
            ball.y = canvas.height - 30;
            ball.dx = 4;
            ball.dy = -4;
            paddle.x = (canvas.width - PADDLE_WIDTH) / 2;
        }
    }
}

function gameLoop() {
    draw();
    updateBall();
    collisionDetection();
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
    paddle = { x: canvas.width / 2 - PADDLE_WIDTH / 2, y: canvas.height - PADDLE_HEIGHT - 10 };
    ball = { x: canvas.width / 2, y: canvas.height - 30, dx: 4, dy: -4 };
    createBricks();
    score = 0;
    lives = 3;
    scoreElement.textContent = score;
    livesElement.textContent = lives;
}

function handleMouseMove(event) {
    if (!gameRunning) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    movePaddle(mouseX);
}

canvas.addEventListener('mousemove', handleMouseMove);
newGameBtn.addEventListener('click', startGame);

canvas.addEventListener('mouseenter', () => {
    canvas.style.cursor = 'none';
});

canvas.addEventListener('mouseleave', () => {
    canvas.style.cursor = 'default';
});

createBricks();
draw();