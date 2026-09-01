import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="포켓몬 카트라이더", layout="centered")

st.title("⚡ 포켓몬 카트라이더 (Streamlit Ver.)")
st.write("방향키(↑↓←→)로 이동하고, **Space바**를 눌러 **백만볼트 부스터**를 사용하세요!")

# HTML5 + Canvas + JS 기반 게임 코드
game_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; padding: 0; background-color: #0e1117; display: flex; justify-content: center; align-items: center; }
        canvas { border: 3px solid #ffffff; background-color: #228B22; border-radius: 8px; }
    </style>
</head>
<body>
    <canvas id="gameCanvas" width="800" height="600"></canvas>

    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");

        // 키 입력 이벤트 수신
        const keys = {};
        window.addEventListener("keydown", (e) => {
            keys[e.code] = true;
            if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(e.code)) {
                e.preventDefault(); // 스크롤 방지
            }
        });
        window.addEventListener("keyup", (e) => { keys[e.code] = false; });

        class Kart {
            constructor(x, y, color, name, isAI = false) {
                this.x = x;
                this.y = y;
                this.color = color;
                this.name = name;
                this.angle = 0;
                this.speed = 0;
                this.maxSpeed = isAI ? 3.5 : 6.0;
                this.accel = 0.15;
                this.friction = 0.05;
                this.turnSpeed = 0.06;
                this.boostTimer = 0;
                this.isAI = isAI;
            }

            update() {
                if (!this.isAI) {
                    if (keys["ArrowLeft"]) this.angle -= this.turnSpeed * (this.speed !== 0 ? Math.sign(this.speed) : 1);
                    if (keys["ArrowRight"]) this.angle += this.turnSpeed * (this.speed !== 0 ? Math.sign(this.speed) : 1);

                    if (keys["ArrowUp"]) {
                        this.speed = Math.min(this.speed + this.accel, this.maxSpeed);
                    } else if (keys["ArrowDown"]) {
                        this.speed = Math.max(this.speed - this.accel, -this.maxSpeed / 2);
                    } else {
                        if (this.speed > 0) this.speed = Math.max(0, this.speed - this.friction);
                        if (this.speed < 0) this.speed = Math.min(0, this.speed + this.friction);
                    }

                    if (keys["Space"] && this.boostTimer === 0) {
                        this.boostTimer = 40;
                        this.speed = this.maxSpeed * 1.6;
                    }
                } else {
                    // AI 꼬북이 원형 트랙 선회
                    this.angle += 0.015;
                    this.speed = this.maxSpeed;
                }

                if (this.boostTimer > 0) this.boostTimer--;

                this.x += this.speed * Math.cos(this.angle);
                this.y += this.speed * Math.sin(this.angle);
            }

            draw() {
                ctx.save();
                ctx.translate(this.x, this.y);
                ctx.rotate(this.angle);

                // 부스터 효과
                if (this.boostTimer > 0) {
                    ctx.beginPath();
                    ctx.arc(0, 0, 20, 0, Math.PI * 2);
                    ctx.strokeStyle = "#FFFF00";
                    ctx.lineWidth = 4;
                    ctx.stroke();
                }

                // 카트 모델링
                ctx.beginPath();
                ctx.moveTo(18, 0);
                ctx.lineTo(-12, -10);
                ctx.lineTo(-12, 10);
                ctx.closePath();
                ctx.fillStyle = this.color;
                ctx.fill();
                ctx.strokeStyle = "#000000";
                ctx.lineWidth = 2;
                ctx.stroke();

                ctx.restore();

                // 캐릭터 이름
                ctx.fillStyle = "#FFFFFF";
                ctx.font = "bold 13px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(this.name, this.x, this.y - 20);
            }
        }

        const player = new Kart(400, 520, "#FFD700", "피카츄⚡");
        const ai = new Kart(400, 550, "#1E90FF", "꼬북이🐢", true);

        function drawTrack() {
            ctx.fillStyle = "#646464";
            ctx.beginPath();
            ctx.ellipse(400, 300, 320, 220, 0, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = "#228B22";
            ctx.beginPath();
            ctx.ellipse(400, 300, 200, 120, 0, 0, Math.PI * 2);
            ctx.fill();

            ctx.strokeStyle = "#FFFFFF";
            ctx.lineWidth = 6;
            ctx.beginPath();
            ctx.moveTo(400, 420);
            ctx.lineTo(400, 520);
            ctx.stroke();
        }

        function gameLoop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            drawTrack();

            player.update();
            ai.update();

            player.draw();
            ai.draw();

            requestAnimationFrame(gameLoop);
        }

        gameLoop();
    </script>
</body>
</html>
"""

components.html(game_html, height=650)
