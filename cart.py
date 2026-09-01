import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="3D 포켓몬 카트라이더", layout="wide")

st.title("⚡ 3D 포켓몬 카트라이더: 캐릭터 서킷")
st.write("방향키(↑↓←→)로 조향/가속, **Space바**로 **백만볼트 부스터**를 사용하세요!")

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
            font-size: 22px; font-weight: bold; background: rgba(0,0,0,0.75);
            padding: 15px 25px; border-radius: 12px; border: 2px solid #777; display: none;
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
        let gameState = 'READY';
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

        const keys = { forward: false, backward: false, left: false, right: false, boost: false };
        let boostTimer = 0;

        init();
        animate();

        function init() {
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x64B5F6); // 선명한 하늘색

            camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 2000);
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById("gameCanvas").appendChild(renderer.domElement);

            const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
            scene.add(ambientLight);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
            dirLight.position.set(200, 400, 100);
            scene.add(dirLight);

            createHighVisibilityTrack();
            createStartFinishLine();
            createEnvironment();
            spawnPokemonKarts();

            window.addEventListener("keydown", (e) => handleKey(e, true));
            window.addEventListener("keyup", (e) => handleKey(e, false));
            window.addEventListener("resize", onWindowResize);
        }

        // 선명한 고대비 도로 및 서킷 생성
        function createHighVisibilityTrack() {
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
            
            // 1. 메인 도로 (아스팔트)
            const tubeGeom = new THREE.TubeGeometry(trackCurve, 300, 18, 12, true);
            const roadMat = new THREE.MeshStandardMaterial({ color: 0x333333, side: THREE.DoubleSide });
            const trackMesh = new THREE.Mesh(tubeGeom, roadMat);
            trackMesh.scale.set(1, 0.04, 1); // 도로로 납작하게 평면화
            trackMesh.position.y = 0.2;
            scene.add(trackMesh);

            // 2. 도로 가장자리 빨간색/흰색 억제턱 (커브 가시성)
            const curbGeom = new THREE.TubeGeometry(trackCurve, 300, 19.5, 12, true);
            const curbMat = new THREE.MeshStandardMaterial({ color: 0xCC1111, side: THREE.DoubleSide });
            const curbMesh = new THREE.Mesh(curbGeom, curbMat);
            curbMesh.scale.set(1, 0.035, 1);
            curbMesh.position.y = 0.1;
            scene.add(curbMesh);

            // 3. 체크포인트 계산
            checkpoints = [];
            for (let i = 0; i < totalCheckpoints; i++) {
                checkpoints.push(trackCurve.getPointAt(i / totalCheckpoints));
            }
        }

        function createStartFinishLine() {
            const startPt = trackCurve.getPointAt(0);
            const tan = trackCurve.getTangentAt(0);
            const angle = Math.atan2(tan.x, tan.z);

            // 아치
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
                new THREE.MeshStandardMaterial({ color: 0x4CAF50 }) // 선명한 녹색 잔디
            );
            grass.rotation.x = -Math.PI / 2;
            grass.position.y = -0.1;
            scene.add(grass);
        }

        // 입체적인 포켓몬 카트 제작
        function createPokemonModel(p) {
            const group = new THREE.Group();

            // 바퀴 4개
            const wheelGeom = new THREE.CylinderGeometry(0.6, 0.6, 0.4, 16);
            const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
            [[-1.4, 1.2], [1.4, 1.2], [-1.4, -1.2], [1.4, -1.2]].forEach(pos => {
                const w = new THREE.Mesh(wheelGeom, wheelMat);
                w.rotation.z = Math.PI / 2;
                w.position.set(pos[0], 0.2, pos[1]);
                group.add(w);
            });

            // 포켓몬 몸통 (베이스 카트)
            const bodyMat = new THREE.MeshStandardMaterial({ color: p.color });
            const body = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.2, 3), bodyMat);
            body.position.y = 0.8;
            group.add(body);

            // 포켓몬 개별 캐릭터 디테일
            if (p.id === "pikachu") {
                // 피카츄 귀 2개
                const earGeom = new THREE.ConeGeometry(0.3, 1.8, 8);
                const earMat = new THREE.MeshStandardMaterial({ color: 0xFFD700 });
                const ear1 = new THREE.Mesh(earGeom, earMat);
                ear1.position.set(-0.7, 2.2, 0.5);
                ear1.rotation.z = -0.3;
                const ear2 = new THREE.Mesh(earGeom, earMat);
                ear2.position.set(0.7, 2.2, 0.5);
                ear2.rotation.z = 0.3;

                // 빨간 볼 볼따구
                const cheekGeom = new THREE.SphereGeometry(0.3, 8, 8);
                const cheekMat = new THREE.MeshStandardMaterial({ color: 0xFF0000 });
                const c1 = new THREE.Mesh(cheekGeom, cheekMat); c1.position.set(-1.15, 1.0, 1.1);
                const c2 = new THREE.Mesh(cheekGeom, cheekMat); c2.position.set(1.15, 1.0, 1.1);

                // 번개 꼬리
                const tailGeom = new THREE.BoxGeometry(0.3, 1.8, 0.6);
                const tail = new THREE.Mesh(tailGeom, earMat);
                tail.position.set(0, 2.0, -1.6);
                tail.rotation.x = -0.4;

                group.add(ear1, ear2, c1, c2, tail);
            } else if (p.id === "charmander") {
                // 파이리 꼬리 불꽃
                const flameGeom = new THREE.ConeGeometry(0.5, 1.2, 8);
                const flameMat = new THREE.MeshStandardMaterial({ color: 0xFF1100, emissive: 0xFF4400 });
                const flame = new THREE.Mesh(flameGeom, flameMat);
                flame.position.set(0, 1.5, -1.8);
                flame.rotation.x = -0.8;
                group.add(flame);
            } else if (p.id === "squirtle") {
                // 꼬북이 등껍질
                const shellGeom = new THREE.SphereGeometry(1.2, 16, 8);
                const shellMat = new THREE.MeshStandardMaterial({ color: 0x8D6E63 });
                const shell = new THREE.Mesh(shellGeom, shellMat);
                shell.scale.set(1, 0.5, 1.2);
                shell.position.set(0, 1.5, -0.2);
                group.add(shell);
            } else if (p.id === "bulbasaur") {
                // 이상해씨 등 봉오리
                const bulbGeom = new THREE.SphereGeometry(1.0, 8, 8);
                const bulbMat = new THREE.MeshStandardMaterial({ color: 0x1B5E20 });
                const bulb = new THREE.Mesh(bulbGeom, bulbMat);
                bulb.position.set(0, 1.6, -0.3);
                group.add(bulb);
            } else if (p.id === "meowth") {
                // 냐옹이 금화
                const coinGeom = new THREE.CylinderGeometry(0.4, 0.4, 0.1, 12);
                const coinMat = new THREE.MeshStandardMaterial({ color: 0xFFD700 });
                const coin = new THREE.Mesh(coinGeom, coinMat);
                coin.rotation.x = Math.PI / 2;
                coin.position.set(0, 1.8, 1.3);
                group.add(coin);
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
                group.maxSpeed = p.isPlayer ? 1.65 : 1.3 + Math.random() * 0.2;
                group.progressT = 0;
                group.laneOffset = (i % 2 === 0 ? 1 : -1) * (4 + Math.floor(i / 2) * 3);

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
                    if (keys.left) kart.rotation.y += 0.045 * (kart.speed >= 0 ? 1 : -1);
                    if (keys.right) kart.rotation.y -= 0.045 * (kart.speed >= 0 ? 1 : -1);

                    if (keys.forward) {
                        kart.speed = Math.min(kart.speed + 0.035, kart.maxSpeed);
                    } else if (keys.backward) {
                        kart.speed = Math.max(kart.speed - 0.03, -kart.maxSpeed / 2);
                    } else {
                        kart.speed *= 0.96;
                    }

                    if (keys.boost && boostTimer === 0) {
                        boostTimer = 90;
                        kart.speed = kart.maxSpeed * 1.7;
                        document.getElementById("boostText").innerText = "🔥 백만볼트 가속 중!";
                    }

                    kart.translateZ(kart.speed);
                } else {
                    kart.progressT = (kart.progressT + (kart.maxSpeed / trackCurve.getLength())) % 1;
                    const pt = trackCurve.getPointAt(kart.progressT);
                    const tan = trackCurve.getTangentAt(kart.progressT);
                    const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();

                    kart.position.copy(pt).add(norm.multiplyScalar(kart.laneOffset));
                    kart.rotation.y = Math.atan2(tan.x, tan.z);
                }

                // 체크포인트 판정
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

            if (boostTimer > 0) {
                boostTimer--;
                if (boostTimer === 0) document.getElementById("boostText").innerText = "준비 완료";
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
