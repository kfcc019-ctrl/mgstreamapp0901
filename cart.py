import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="3D 포켓몬 카트라이더", layout="wide")

st.title("⚡ 3D 포켓몬 카트라이더: 3랩 서킷 챔피언십")
st.write("방향키(↑↓←→)로 이동, **Space바**로 **백만볼트 부스터**를 사용하세요!")

game_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background-color: #0e1117; font-family: 'Malgun Gothic', sans-serif; }
        #gameCanvas { width: 100vw; height: 100vh; position: absolute; top: 0; left: 0; }
        
        /* UI 오버레이 */
        #ui-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; display: flex; flex-direction: column;
            justify-content: center; align-items: center; color: white; z-index: 10;
        }
        
        #startBtn {
            pointer-events: auto; padding: 18px 45px; font-size: 28px; font-weight: bold;
            color: #111; background: #FFD700; border: none; border-radius: 50px;
            cursor: pointer; box-shadow: 0 6px 20px rgba(255,215,0,0.6); transition: 0.2s;
        }
        #startBtn:hover { transform: scale(1.08); background: #FFF066; }
        
        #countdown {
            font-size: 110px; font-weight: 900; text-shadow: 0 0 25px rgba(0,0,0,0.8);
            color: #00E5FF; display: none;
        }
        
        #hud {
            position: absolute; top: 20px; left: 20px; text-align: left;
            font-size: 22px; font-weight: bold; background: rgba(0,0,0,0.65);
            padding: 15px 25px; border-radius: 12px; border: 2px solid #555; display: none;
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
        <button id="startBtn" onclick="startCountdown()">🎮 레이스 시작하기</button>
        <div id="countdown">3</div>
        <div id="hud">
            <div>🏁 순위: <span id="rankText" style="color:#FFD700;">1</span> / 7</div>
            <div>🔄 바퀴: <span id="lapText" style="color:#00E5FF;">1</span> / 3</div>
            <div>⚡ 부스터: <span id="boostText" style="color:#FF4500;">준비 완료</span></div>
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
        let gameState = 'READY'; // READY, COUNTDOWN, RACING, FINISHED
        let rankCounter = 0;

        const POKEMONS = [
            { name: "피카츄⚡", color: 0xFFD700, isPlayer: true },
            { name: "이상해씨🌱", color: 0x32CD32, isPlayer: false },
            { name: "파이리🔥", color: 0xFF4500, isPlayer: false },
            { name: "꼬북이💧", color: 0x1E90FF, isPlayer: false },
            { name: "야돈🌀", color: 0xFFB6C1, isPlayer: false },
            { name: "고오스👻", color: 0x800080, isPlayer: false },
            { name: "냐옹🐾", color: 0xFFA500, isPlayer: false }
        ];

        let karts = [];
        let playerKart;
        const totalLaps = 3;
        const totalCheckpoints = 12;
        let checkpoints = [];

        const keys = { forward: false, backward: false, left: false, right: false, boost: false };
        let boostTimer = 0;

        init();
        animate();

        function init() {
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x40B5AD);

            camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 2000);
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById("gameCanvas").appendChild(renderer.domElement);

            const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
            scene.add(ambientLight);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
            dirLight.position.set(200, 300, 100);
            scene.add(dirLight);

            createComplexTrack();
            createStartFinishLine();
            createEnvironment();
            spawnKarts();

            window.addEventListener("keydown", (e) => handleKey(e, true));
            window.addEventListener("keyup", (e) => handleKey(e, false));
            window.addEventListener("resize", onWindowResize);
        }

        // 복잡한 서킷 생성 (S자, 헤어핀 코너 포함)
        function createComplexTrack() {
            const controlPoints = [
                new THREE.Vector3(0, 0, 0),         // 출발선
                new THREE.Vector3(200, 0, 0),       // 직진
                new THREE.Vector3(350, 0, 150),     // 우회전
                new THREE.Vector3(300, 0, 350),     // 급커브
                new THREE.Vector3(100, 0, 250),     // S자 진입
                new THREE.Vector3(-50, 0, 450),     // S자 탈출
                new THREE.Vector3(-250, 0, 300),    // 헤어핀 진입
                new THREE.Vector3(-350, 0, 100),    // 헤어핀 코너
                new THREE.Vector3(-200, 0, -100),   // 대각선 직진
                new THREE.Vector3(-100, 0, -250),   // 하단 곡선
                new THREE.Vector3(100, 0, -250),    // 복귀 코너
                new THREE.Vector3(0, 0, -100)       // 직선 연결
            ];

            trackCurve = new THREE.CatmullRomCurve3(controlPoints, true);
            const trackWidth = 32;
            const divisions = 400;

            // 도로 지오메트리 동적 생성
            const geom = new THREE.BufferGeometry();
            const positions = [], uvs = [];

            for (let i = 0; i <= divisions; i++) {
                const t = i / divisions;
                const pt = trackCurve.getPointAt(t);
                const tan = trackCurve.getTangentAt(t);
                const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();

                const left = pt.clone().add(norm.clone().multiplyScalar(trackWidth / 2));
                const right = pt.clone().add(norm.clone().multiplyScalar(-trackWidth / 2));

                positions.push(left.x, left.y, left.z);
                positions.push(right.x, right.y, right.z);
                uvs.push(0, i * 5); uvs.push(1, i * 5);
            }

            const indices = [];
            for (let i = 0; i < divisions; i++) {
                const r1 = i * 2, r2 = (i + 1) * 2;
                indices.push(r1, r1 + 1, r2, r1 + 1, r2 + 1, r2);
            }

            geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
            geom.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
            geom.setIndex(indices);
            geom.computeVertexNormals();

            const roadMat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8 });
            scene.add(new THREE.Mesh(geom, roadMat));

            // 체크포인트 위치 저장
            checkpoints = [];
            for (let i = 0; i < totalCheckpoints; i++) {
                checkpoints.push(trackCurve.getPointAt(i / totalCheckpoints));
            }
        }

        // 출발 / 도착 아치 및 그리드 선 생성
        function createStartFinishLine() {
            const startPt = trackCurve.getPointAt(0);
            const tan = trackCurve.getTangentAt(0);
            const angle = Math.atan2(tan.x, tan.z);

            // 출발선 격자 바닥
            const lineGeom = new THREE.PlaneGeometry(32, 8);
            const canvas = document.createElement('canvas');
            canvas.width = 128; canvas.height = 32;
            const ctx = canvas.getContext('2d');
            for(let r=0; r<2; r++){
                for(let c=0; c<8; c++){
                    ctx.fillStyle = (r+c)%2===0 ? '#FFF' : '#000';
                    ctx.fillRect(c*16, r*16, 16, 16);
                }
            }
            const texture = new THREE.CanvasTexture(canvas);
            const lineMat = new THREE.MeshStandardMaterial({ map: texture, side: THREE.DoubleSide });
            const line = new THREE.Mesh(lineGeom, lineMat);
            line.rotation.x = -Math.PI / 2;
            line.rotation.z = angle + Math.PI / 2;
            line.position.set(startPt.x, 0.1, startPt.z);
            scene.add(line);

            // 출발선 아치 기둥
            const archGroup = new THREE.Group();
            const poleGeom = new THREE.CylinderGeometry(0.8, 0.8, 15);
            const poleMat = new THREE.MeshStandardMaterial({ color: 0xFFD700 });
            
            const p1 = new THREE.Mesh(poleGeom, poleMat); p1.position.set(-16, 7.5, 0);
            const p2 = new THREE.Mesh(poleGeom, poleMat); p2.position.set(16, 7.5, 0);
            const top = new THREE.Mesh(new THREE.BoxGeometry(34, 2, 2), poleMat); top.position.set(0, 14, 0);

            archGroup.add(p1, p2, top);
            archGroup.position.set(startPt.x, 0, startPt.z);
            archGroup.rotation.y = angle + Math.PI / 2;
            scene.add(archGroup);
        }

        function createEnvironment() {
            const grass = new THREE.Mesh(
                new THREE.PlaneGeometry(2000, 2000),
                new THREE.MeshStandardMaterial({ color: 0x2e8b57 })
            );
            grass.rotation.x = -Math.PI / 2;
            grass.position.y = -0.2;
            scene.add(grass);
        }

        function spawnKarts() {
            const trackLen = trackCurve.getLength();

            POKEMONS.forEach((p, i) => {
                const group = new THREE.Group();

                // 차체
                const body = new THREE.Mesh(
                    new THREE.BoxGeometry(2, 1.2, 3),
                    new THREE.MeshStandardMaterial({ color: p.color })
                );
                group.add(body);

                group.info = p;
                group.lap = 1;
                group.nextCP = 1;
                group.finished = false;
                group.rank = 0;
                group.speed = 0;
                group.maxSpeed = p.isPlayer ? 1.6 : 1.25 + Math.random() * 0.25;
                group.progressT = 0; // AI 위치 파라미터 (0~1)
                group.laneOffset = (i % 2 === 0 ? 1 : -1) * (4 + Math.floor(i / 2) * 3);

                // 출발점 뒤쪽 배열
                const startT = (1 - (i * 12 / trackLen)) % 1;
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
            document.getElementById("startBtn").style.display = "none";
            const cdEl = document.getElementById("countdown");
            cdEl.style.display = "block";
            
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

        function updatePhysics() {
            if (gameState !== 'RACING') return;

            karts.forEach((kart) => {
                if (kart.finished) return;

                if (kart.info.isPlayer) {
                    // 플레이어 물리 이동
                    if (keys.left) kart.rotation.y += 0.04 * (kart.speed >= 0 ? 1 : -1);
                    if (keys.right) kart.rotation.y -= 0.04 * (kart.speed >= 0 ? 1 : -1);

                    if (keys.forward) {
                        kart.speed = Math.min(kart.speed + 0.03, kart.maxSpeed);
                    } else if (keys.backward) {
                        kart.speed = Math.max(kart.speed - 0.03, -kart.maxSpeed / 2);
                    } else {
                        kart.speed *= 0.96;
                    }

                    // 부스터
                    if (keys.boost && boostTimer === 0) {
                        boostTimer = 90;
                        kart.speed = kart.maxSpeed * 1.7;
                        document.getElementById("boostText").innerText = "🔥 백만볼트 가속 중!";
                    }

                    kart.translateZ(kart.speed);
                } else {
                    // AI 자동 주행 경로 따라가기
                    kart.progressT = (kart.progressT + (kart.maxSpeed / trackCurve.getLength())) % 1;
                    const pt = trackCurve.getPointAt(kart.progressT);
                    const tan = trackCurve.getTangentAt(kart.progressT);
                    const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();

                    kart.position.copy(pt).add(norm.multiplyScalar(kart.laneOffset));
                    kart.rotation.y = Math.atan2(tan.x, tan.z);
                }

                // 체크포인트 및 바퀴(Lap) 수 체크
                const targetCP = checkpoints[kart.nextCP];
                if (kart.position.distanceTo(targetCP) < 40) {
                    kart.nextCP = (kart.nextCP + 1) % totalCheckpoints;
                    if (kart.nextCP === 1) { // 한 바퀴 완성
                        kart.lap++;
                        if (kart.info.isPlayer) {
                            document.getElementById("lapText").innerText = Math.min(kart.lap, totalLaps);
                        }
                        if (kart.lap > totalLaps) {
                            kart.finished = true;
                            rankCounter++;
                            kart.rank = rankCounter;

                            if (kart.info.isPlayer || rankCounter === 1) {
                                checkRaceEnd(kart);
                            }
                        }
                    }
                }
            });

            if (boostTimer > 0) {
                boostTimer--;
                if (boostTimer === 0) document.getElementById("boostText").innerText = "준비 완료";
            }

            updateRankings();
            updateCamera();
        }

        function updateRankings() {
            // 주행 거리에 따른 실시간 순위 계산
            karts.sort((a, b) => {
                if (a.lap !== b.lap) return b.lap - a.lap;
                return b.nextCP - a.nextCP;
            });

            const currentRank = karts.findIndex(k => k.info.isPlayer) + 1;
            document.getElementById("rankText").innerText = currentRank;
        }

        function checkRaceEnd(finishedKart) {
            if (finishedKart.info.isPlayer) {
                showWinnerModal(`🎉 ${finishedKart.info.name} ${finishedKart.rank}위 도착!`, `총 3바퀴 레이스를 완료했습니다!`);
            } else if (rankCounter === 1) {
                showWinnerModal(`🏆 ${finishedKart.info.name} 우승!`, `상대 포켓몬이 먼저 3바퀴를 완주했습니다.`);
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
            const offset = new THREE.Vector3(0, 7, -16);
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
