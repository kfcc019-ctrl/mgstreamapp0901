import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="3D 포켓몬 카트라이더", layout="wide")

st.title("⚡ 3D 포켓몬 카트라이더: 챔피언십")
st.write("난이도를 선택한 후 **레이스 시작**을 누르세요! (방향키: 조향/가속, **Space바**: 백만볼트 부스터)")

game_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background-color: #0e1117; font-family: 'Malgun Gothic', sans-serif; }
        #gameCanvas { width: 100vw; height: 100vh; position: absolute; top: 0; left: 0; }
        
        #ui-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; display: flex; flex-direction: column;
            justify-content: center; align-items: center; color: white; z-index: 10;
        }

        #startScreen {
            pointer-events: auto; background: rgba(15, 15, 25, 0.9); padding: 30px 50px;
            border-radius: 20px; text-align: center; border: 3px solid #FFD700;
            box-shadow: 0 0 25px rgba(255,215,0,0.4);
        }

        .diff-btn {
            padding: 10px 25px; margin: 0 5px; font-size: 18px; font-weight: bold;
            border: 2px solid #555; background: #222; color: white; border-radius: 8px; cursor: pointer;
        }
        .diff-btn.active { background: #FFD700; color: black; border-color: #FFD700; }
        
        #startBtn {
            margin-top: 25px; padding: 15px 40px; font-size: 26px; font-weight: bold;
            color: #111; background: #00E5FF; border: none; border-radius: 50px;
            cursor: pointer; box-shadow: 0 6px 20px rgba(0,229,255,0.5); transition: 0.2s;
        }
        #startBtn:hover { transform: scale(1.05); background: #80F4FF; }
        
        #countdown {
            font-size: 120px; font-weight: 900; text-shadow: 0 0 30px rgba(0,0,0,0.9);
            color: #00E5FF; display: none;
        }
        
        #hud {
            position: absolute; top: 20px; left: 20px; text-align: left;
            font-size: 20px; font-weight: bold; background: rgba(0,0,0,0.8);
            padding: 15px 25px; border-radius: 12px; border: 2px solid #666; display: none;
        }
        
        #winnerModal {
            position: absolute; display: none; pointer-events: auto;
            background: rgba(15, 15, 25, 0.95); padding: 40px 60px;
            border-radius: 20px; text-align: center; border: 3px solid #FFD700;
            box-shadow: 0 0 30px rgba(255,215,0,0.5);
        }
        #restartBtn {
            margin-top: 20px; padding: 12px 30px; font-size: 20px; font-weight: bold;
            background: #1E90FF; color: white; border: none; border-radius: 10px; cursor: pointer;
        }
    </style>
</head>
<body>
    <div id="gameCanvas"></div>
    
    <div id="ui-overlay">
        <div id="startScreen">
            <h2 style="color:#FFD700; margin-top:0;">🎮 AI 난이도 선택</h2>
            <div style="margin-bottom: 20px;">
                <button class="diff-btn" onclick="selectDiff('EASY', this)">하 (쉬움)</button>
                <button class="diff-btn active" onclick="selectDiff('MEDIUM', this)">중 (보통)</button>
                <button class="diff-btn" onclick="selectDiff('HARD', this)">상 (매우 잘함)</button>
            </div>
            <button id="startBtn" onclick="startCountdown()">🚀 레이스 시작</button>
        </div>

        <div id="countdown">3</div>

        <div id="hud">
            <div>🏁 순위: <span id="rankText" style="color:#FFD700;">1</span> / 7</div>
            <div>🔄 바퀴: <span id="lapText" style="color:#00E5FF;">1</span> / 3</div>
            <div>⚡ 부스터: <span id="boostText" style="color:#00FF00;">사용 가능 (Space)</span></div>
        </div>

        <div id="winnerModal">
            <h1 id="winnerText" style="color:#FFD700; margin:0 0 15px 0;">🎉 피카츄 승리!</h1>
            <p id="winnerSubText" style="font-size:20px; margin:0;">3바퀴 완주 성공!</p>
            <button id="restartBtn" onclick="location.reload()">다시 경기하기</button>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        let scene, camera, renderer, trackCurve;
        let gameState = 'READY';
        let selectedDifficulty = 'MEDIUM';
        let rankCounter = 0;

        const POKEMONS = [
            { id: "pikachu", name: "피카츄⚡", color: 0xFFD700, isPlayer: true },
            { id: "bulbasaur", name: "이상해씨🌱", color: 0x30A727, isPlayer: false },
            { id: "charmander", name: "파이리🔥", color: 0xFF5722, isPlayer: false },
            { id: "squirtle", name: "꼬북이💧", color: 0x29B6F6, isPlayer: false },
            { id: "slowpoke", name: "야돈🌀", color: 0xF48FB1, isPlayer: false },
            { id: "gastly", name: "고오스👻", color: 0x7E57C2, isPlayer: false },
            { id: "meowth", name: "냐옹🐾", color: 0xFFE082, isPlayer: false }
        ];

        let karts = [];
        let playerKart;
        const totalLaps = 3;
        const totalCheckpoints = 12;
        let checkpoints = [];
        const trackHalfWidth = 16.5; // 트랙 반폭 (벽 판정 기준)

        const keys = { forward: false, backward: false, left: false, right: false, boost: false };

        init();
        animate();

        function init() {
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x5c94fc);

            camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 2000);
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById("gameCanvas").appendChild(renderer.domElement);

            const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
            scene.add(ambientLight);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
            dirLight.position.set(200, 400, 100);
            scene.add(dirLight);

            createTrackAndWalls();
            createStartFinishLine();
            createEnvironment();
            spawnPokemonKarts();

            window.addEventListener("keydown", (e) => handleKey(e, true));
            window.addEventListener("keyup", (e) => handleKey(e, false));
            window.addEventListener("resize", onWindowResize);
        }

        function selectDiff(diff, btn) {
            selectedDifficulty = diff;
            document.querySelectorAll('.diff-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        // 트랙 및 외곽 가드레일(벽) 생성
        function createTrackAndWalls() {
            const controlPoints = [
                new THREE.Vector3(0, 0, 0),
                new THREE.Vector3(220, 0, 0),
                new THREE.Vector3(380, 0, 180),
                new THREE.Vector3(320, 0, 380),
                new THREE.Vector3(120, 0, 280),
                new THREE.Vector3(-60, 0, 480),
                new THREE.Vector3(-280, 0, 320),
                new THREE.Vector3(-380, 0, 100),
                new THREE.Vector3(-220, 0, -120),
                new THREE.Vector3(-120, 0, -280),
                new THREE.Vector3(120, 0, -280),
                new THREE.Vector3(0, 0, -100)
            ];

            trackCurve = new THREE.CatmullRomCurve3(controlPoints, true);
            
            // 도로
            const tubeGeom = new THREE.TubeGeometry(trackCurve, 300, 18, 12, true);
            const roadMat = new THREE.MeshStandardMaterial({ color: 0x333333, side: THREE.DoubleSide });
            const trackMesh = new THREE.Mesh(tubeGeom, roadMat);
            trackMesh.scale.set(1, 0.04, 1);
            trackMesh.position.y = 0.2;
            scene.add(trackMesh);

            // 외곽 가드레일 벽 (양쪽)
            const wallMat = new THREE.MeshStandardMaterial({ color: 0xDD2C00 }); // 선명한 주황-빨강 가드레일
            
            const outerWallGeom = new THREE.TubeGeometry(trackCurve, 300, 19.5, 8, true);
            const outerWall = new THREE.Mesh(outerWallGeom, wallMat);
            outerWall.scale.set(1, 0.3, 1);
            outerWall.position.y = 1.2;
            scene.add(outerWall);

            const innerWallGeom = new THREE.TubeGeometry(trackCurve, 300, 16.5, 8, true);
            const innerWall = new THREE.Mesh(innerWallGeom, wallMat);
            innerWall.scale.set(1, 0.3, 1);
            innerWall.position.y = 1.2;
            scene.add(innerWall);

            checkpoints = [];
            for (let i = 0; i < totalCheckpoints; i++) {
                checkpoints.push(trackCurve.getPointAt(i / totalCheckpoints));
            }
        }

        function createStartFinishLine() {
            const startPt = trackCurve.getPointAt(0);
            const tan = trackCurve.getTangentAt(0);
            const angle = Math.atan2(tan.x, tan.z);

            const archGroup = new THREE.Group();
            const poleGeom = new THREE.CylinderGeometry(1, 1, 16);
            const poleMat = new THREE.MeshStandardMaterial({ color: 0xFFD700 });
            
            const p1 = new THREE.Mesh(poleGeom, poleMat); p1.position.set(-18, 8, 0);
            const p2 = new THREE.Mesh(poleGeom, poleMat); p2.position.set(18, 8, 0);
            const top = new THREE.Mesh(new THREE.BoxGeometry(38, 3, 3), poleMat); top.position.set(0, 15, 0);

            archGroup.add(p1, p2, top);
            archGroup.position.set(startPt.x, 0, startPt.z);
            archGroup.rotation.y = angle + Math.PI / 2;
            scene.add(archGroup);
        }

        function createEnvironment() {
            const grass = new THREE.Mesh(
                new THREE.PlaneGeometry(2500, 2500),
                new THREE.MeshStandardMaterial({ color: 0x388E3C })
            );
            grass.rotation.x = -Math.PI / 2;
            grass.position.y = -0.1;
            scene.add(grass);
        }

        function createPokemonModel(p) {
            const group = new THREE.Group();

            const wheelGeom = new THREE.CylinderGeometry(0.6, 0.6, 0.4, 16);
            const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
            [[-1.4, 1.2], [1.4, 1.2], [-1.4, -1.2], [1.4, -1.2]].forEach(pos => {
                const w = new THREE.Mesh(wheelGeom, wheelMat);
                w.rotation.z = Math.PI / 2;
                w.position.set(pos[0], 0.2, pos[1]);
                group.add(w);
            });

            const bodyMat = new THREE.MeshStandardMaterial({ color: p.color });
            const body = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.2, 3), bodyMat);
            body.position.y = 0.8;
            group.add(body);

            if (p.id === "pikachu") {
                const earGeom = new THREE.ConeGeometry(0.3, 1.8, 8);
                const earMat = new THREE.MeshStandardMaterial({ color: 0xFFD700 });
                const ear1 = new THREE.Mesh(earGeom, earMat); ear1.position.set(-0.7, 2.2, 0.5); ear1.rotation.z = -0.3;
                const ear2 = new THREE.Mesh(earGeom, earMat); ear2.position.set(0.7, 2.2, 0.5); ear2.rotation.z = 0.3;

                const cheekGeom = new THREE.SphereGeometry(0.3, 8, 8);
                const cheekMat = new THREE.MeshStandardMaterial({ color: 0xFF0000 });
                const c1 = new THREE.Mesh(cheekGeom, cheekMat); c1.position.set(-1.15, 1.0, 1.1);
                const c2 = new THREE.Mesh(cheekGeom, cheekMat); c2.position.set(1.15, 1.0, 1.1);

                const tail = new THREE.Mesh(new THREE.BoxGeometry(0.3, 1.8, 0.6), earMat);
                tail.position.set(0, 2.0, -1.6); tail.rotation.x = -0.4;

                group.add(ear1, ear2, c1, c2, tail);
            } else if (p.id === "charmander") {
                const flame = new THREE.Mesh(new THREE.ConeGeometry(0.5, 1.2, 8), new THREE.MeshStandardMaterial({ color: 0xFF1100, emissive: 0xFF4400 }));
                flame.position.set(0, 1.5, -1.8); flame.rotation.x = -0.8;
                group.add(flame);
            } else if (p.id === "squirtle") {
                const shell = new THREE.Mesh(new THREE.SphereGeometry(1.2, 16, 8), new THREE.MeshStandardMaterial({ color: 0x8D6E63 }));
                shell.scale.set(1, 0.5, 1.2); shell.position.set(0, 1.5, -0.2);
                group.add(shell);
            } else if (p.id === "bulbasaur") {
                const bulb = new THREE.Mesh(new THREE.SphereGeometry(1.0, 8, 8), new THREE.MeshStandardMaterial({ color: 0x1B5E20 }));
                bulb.position.set(0, 1.6, -0.3);
                group.add(bulb);
            }

            return group;
        }

        function spawnPokemonKarts() {
            const trackLen = trackCurve.getLength();

            POKEMONS.forEach((p, i) => {
                const group = createPokemonModel(p);

                group.info = p;
                group.lap = 1;
                group.nextCP = 1;
                group.finished = false;
                group.rank = 0;
                group.speed = 0;
                group.progressT = 0;
                group.laneOffset = (i % 2 === 0 ? 1 : -1) * (3 + Math.floor(i / 2) * 2.5);

                // 부스터 시스템 속성 (모든 플레이어 & AI 공통)
                group.boosterCooldown = 0; // 쿨다운 프레임 (600프레임 = 10초)
                group.boosterActive = 0;    // 활성화 프레임 (120프레임 = 2초)

                // 난이도별 AI 속도 설정
                if (p.isPlayer) {
                    group.maxSpeed = 1.6;
                } else {
                    if (selectedDifficulty === 'EASY') group.maxSpeed = 1.0 + Math.random() * 0.15;
                    else if (selectedDifficulty === 'MEDIUM') group.maxSpeed = 1.4 + Math.random() * 0.15;
                    else if (selectedDifficulty === 'HARD') group.maxSpeed = 1.85 + Math.random() * 0.15; // 상: 매우 빠름
                }

                const startT = (1 - (i * 14 / trackLen)) % 1;
                group.progressT = startT;

                const pt = trackCurve.getPointAt(startT);
                const tan = trackCurve.getTangentAt(startT);
                const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();

                group.position.copy(pt).add(norm.multiplyScalar(group.laneOffset));
                group.rotation.y = Math.atan2(tan.x, tan.z);

                karts.push(group);
                scene.add(group);

                if (p.isPlayer) playerKart = group;
            });

            updateCamera();
        }

        function startCountdown() {
            document.getElementById("startScreen").style.display = "none";
            const cdEl = document.getElementById("countdown");
            cdEl.style.display = "block";
            
            // 재설정 (난이도 변경 반영)
            karts.forEach(k => {
                if (!k.info.isPlayer) {
                    if (selectedDifficulty === 'EASY') k.maxSpeed = 1.0 + Math.random() * 0.15;
                    else if (selectedDifficulty === 'MEDIUM') k.maxSpeed = 1.4 + Math.random() * 0.15;
                    else if (selectedDifficulty === 'HARD') k.maxSpeed = 1.85 + Math.random() * 0.15;
                }
            });

            let count = 3;
            cdEl.innerText = count;

            const timer = setInterval(() => {
                count--;
                if (count > 0) {
                    cdEl.innerText = count;
                } else if (count === 0) {
                    cdEl.innerText = "GO!!";
                    gameState = 'RACING';
                    document.getElementById("hud").style.display = "block";
                } else {
                    clearInterval(timer);
                    cdEl.style.display = "none";
                }
            }, 1000);
        }

        function handleKey(e, isDown) {
            if (e.code === "ArrowUp") keys.forward = isDown;
            if (e.code === "ArrowDown") keys.backward = isDown;
            if (e.code === "ArrowLeft") keys.left = isDown;
            if (e.code === "ArrowRight") keys.right = isDown;
            if (e.code === "Space") keys.boost = isDown;
            if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(e.code)) e.preventDefault();
        }

        // 트랙과의 거리 및 벽 충돌 검사
        function checkWallCollision(kart) {
            // 가장 가까운 트랙 포인트 탐색
            let closestPt = trackCurve.getPointAt(kart.progressT || 0);
            let dist = kart.position.distanceTo(closestPt);

            // 벽 충돌 (도로 이탈 시)
            if (dist > trackHalfWidth) {
                // 반튀어나가기 물리 및 속도 급감
                const pushDir = new THREE.Vector3().subVectors(closestPt, kart.position).normalize();
                kart.position.add(pushDir.multiplyScalar(1.2)); // 트랙 안쪽으로 튕겨냄
                kart.speed = -kart.speed * 0.4; // 충돌 충격으로 속도 반전 및 감속
            }
        }

        function updatePhysics() {
            if (gameState !== 'RACING') return;

            karts.forEach((kart) => {
                if (kart.finished) return;

                // --- 1. 부스터 쿨다운 & 타이머 처리 ---
                if (kart.boosterActive > 0) {
                    kart.boosterActive--;
                } else if (kart.boosterCooldown > 0) {
                    kart.boosterCooldown--;
                }

                const currentMaxSpeed = kart.boosterActive > 0 ? kart.maxSpeed * 1.6 : kart.maxSpeed;

                // --- 2. 주행 처리 ---
                if (kart.info.isPlayer) {
                    // 조향각 속도 조정 (0.045 -> 0.024로 부드럽고 정교하게 조정)
                    if (keys.left) kart.rotation.y += 0.024 * (kart.speed >= 0 ? 1 : -1);
                    if (keys.right) kart.rotation.y -= 0.024 * (kart.speed >= 0 ? 1 : -1);

                    if (keys.forward) {
                        kart.speed = Math.min(kart.speed + 0.035, currentMaxSpeed);
                    } else if (keys.backward) {
                        kart.speed = Math.max(kart.speed - 0.03, -currentMaxSpeed / 2);
                    } else {
                        kart.speed *= 0.96;
                    }

                    // 플레이어 부스터 사용 (10초 쿨다운 = 600프레임, 2초 지속 = 120프레임)
                    if (keys.boost && kart.boosterCooldown === 0 && kart.boosterActive === 0) {
                        kart.boosterActive = 120; // 2초
                        kart.boosterCooldown = 600; // 10초
                        kart.speed = currentMaxSpeed;
                    }

                    kart.translateZ(kart.speed);
                    checkWallCollision(kart);

                } else {
                    // AI 주행 및 AI 부스터 자동 사용
                    if (kart.boosterCooldown === 0 && kart.boosterActive === 0) {
                        // AI도 10초마다 부스터 사용
                        kart.boosterActive = 120;
                        kart.boosterCooldown = 600;
                    }

                    kart.progressT = (kart.progressT + (currentMaxSpeed / trackCurve.getLength())) % 1;
                    const pt = trackCurve.getPointAt(kart.progressT);
                    const tan = trackCurve.getTangentAt(kart.progressT);
                    const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();

                    kart.position.copy(pt).add(norm.multiplyScalar(kart.laneOffset));
                    kart.rotation.y = Math.atan2(tan.x, tan.z);
                }

                // --- 3. 체크포인트 판정 ---
                const targetCP = checkpoints[kart.nextCP];
                if (kart.position.distanceTo(targetCP) < 45) {
                    kart.nextCP = (kart.nextCP + 1) % totalCheckpoints;
                    if (kart.nextCP === 1) {
                        kart.lap++;
                        if (kart.info.isPlayer) {
                            document.getElementById("lapText").innerText = Math.min(kart.lap, totalLaps);
                        }
                        if (kart.lap > totalLaps) {
                            kart.finished = true;
                            rankCounter++;
                            kart.rank = rankCounter;
                            checkRaceEnd(kart);
                        }
                    }
                }
            });

            // HUD 부스터 상태 업데이트
            const bText = document.getElementById("boostText");
            if (playerKart.boosterActive > 0) {
                bText.innerText = `🔥 부스터 가속 중! (${(playerKart.boosterActive / 60).toFixed(1)}s)`;
                bText.style.color = "#FF4500";
            } else if (playerKart.boosterCooldown > 0) {
                bText.innerText = `⏳ 쿨다운 중... (${(playerKart.boosterCooldown / 60).toFixed(1)}s)`;
                bText.style.color = "#AAAAAA";
            } else {
                bText.innerText = "사용 가능 (Space)";
                bText.style.color = "#00FF00";
            }

            updateRankings();
            updateCamera();
        }

        function updateRankings() {
            karts.sort((a, b) => {
                if (a.lap !== b.lap) return b.lap - a.lap;
                return b.nextCP - a.nextCP;
            });
            const currentRank = karts.findIndex(k => k.info.isPlayer) + 1;
            document.getElementById("rankText").innerText = currentRank;
        }

        function checkRaceEnd(finishedKart) {
            if (finishedKart.info.isPlayer) {
                showWinnerModal(`🎉 ${finishedKart.info.name} ${finishedKart.rank}위 도착!`, `3바퀴 완주 성공!`);
            } else if (rankCounter === 1) {
                showWinnerModal(`🏆 ${finishedKart.info.name} 우승!`, `상대 포켓몬이 먼저 완주했습니다.`);
            }
        }

        function showWinnerModal(title, sub) {
            gameState = 'FINISHED';
            document.getElementById("winnerText").innerText = title;
            document.getElementById("winnerSubText").innerText = sub;
            document.getElementById("winnerModal").style.display = "block";
        }

        function updateCamera() {
            if (!playerKart) return;
            const offset = new THREE.Vector3(0, 8, -18);
            const cameraPos = offset.applyMatrix4(playerKart.matrixWorld);
            camera.position.lerp(cameraPos, 0.2);
            camera.lookAt(playerKart.position.x, playerKart.position.y + 2, playerKart.position.z);
        }

        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }

        function animate() {
            requestAnimationFrame(animate);
            updatePhysics();
            renderer.render(scene, camera);
        }
    </script>
</body>
</html>
"""

components.html(game_html, height=800, scrolling=False)
