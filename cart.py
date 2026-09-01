import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="3D 새망이 카트라이더", layout="wide")

st.title("🐤 3D 새마을금고 새망이 카트라이더: 리얼 서킷")
st.write("난이도를 선택한 후 **레이스 시작**을 누르세요! (방향키: 조향/가속, **Shift**: 브레이크/감속, **Space**: 부스터, **ESC**: 일시정지)")

game_html = """<!DOCTYPE html>
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
            pointer-events: auto; background: rgba(15, 15, 25, 0.85); padding: 25px 45px;
            border-radius: 20px; text-align: center; border: 3px solid #00B0FF;
            box-shadow: 0 0 25px rgba(0,176,255,0.4); backdrop-filter: blur(4px);
        }

        .diff-btn {
            padding: 10px 25px; margin: 0 5px; font-size: 18px; font-weight: bold;
            border: 2px solid #555; background: #222; color: white; border-radius: 8px; cursor: pointer;
        }
        .diff-btn.active { background: #00B0FF; color: black; border-color: #00B0FF; }
        
        #startBtn {
            margin-top: 20px; padding: 14px 38px; font-size: 24px; font-weight: bold;
            color: #111; background: #FFD700; border: none; border-radius: 50px;
            cursor: pointer; box-shadow: 0 6px 20px rgba(255,215,0,0.5); transition: 0.2s;
        }
        #startBtn:hover { transform: scale(1.05); background: #FFF066; }
        
        #countdown {
            font-size: 120px; font-weight: 900; text-shadow: 0 0 30px rgba(0,0,0,0.9);
            color: #00E5FF; display: none;
        }
        
        #hud {
            position: absolute; top: 20px; left: 20px; text-align: left;
            font-size: 18px; font-weight: bold; background: rgba(0,0,0,0.8);
            padding: 15px 25px; border-radius: 12px; border: 2px solid #00B0FF; display: none;
            pointer-events: auto;
        }

        .hud-btn {
            margin-top: 10px; padding: 6px 14px; font-size: 14px; font-weight: bold;
            background: #FF9800; color: white; border: none; border-radius: 6px; cursor: pointer;
        }
        
        .modal-popup {
            position: absolute; display: none; pointer-events: auto;
            background: rgba(15, 15, 25, 0.95); padding: 35px 55px;
            border-radius: 20px; text-align: center; border: 3px solid #00B0FF;
            box-shadow: 0 0 30px rgba(0,176,255,0.5); backdrop-filter: blur(5px);
        }

        .modal-btn {
            margin: 10px 8px 0 8px; padding: 12px 26px; font-size: 18px; font-weight: bold;
            color: white; border: none; border-radius: 10px; cursor: pointer; transition: 0.2s;
        }
        .modal-btn:hover { transform: scale(1.05); }
    </style>
</head>
<body>
    <div id="gameCanvas"></div>
    
    <div id="ui-overlay">
        <div id="startScreen">
            <h2 style="color:#00B0FF; margin-top:0;">🐤 새망이 레이스 난이도</h2>
            <div style="margin-bottom: 15px;">
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
            <div>🛑 브레이크: <span style="color:#FFD700;">Shift</span></div>
            <div>⚡ 부스터: <span id="boostText" style="color:#00FF00;">사용 가능 (Space)</span></div>
            <button class="hud-btn" onclick="pauseGame()">⏸️ 일시정지 (ESC)</button>
        </div>

        <div id="pauseModal" class="modal-popup">
            <h1 style="color:#00B0FF; margin:0 0 15px 0;">⏸️ 일시정지</h1>
            <p style="font-size:18px; margin-bottom:20px;">경기가 잠시 멈췄습니다.</p>
            <button class="modal-btn" style="background:#4CAF50;" onclick="resumeGame()">▶️ 다시시작</button>
            <button class="modal-btn" style="background:#E53935;" onclick="restartGame()">🔄 처음으로</button>
        </div>

        <div id="winnerModal" class="modal-popup">
            <h1 id="winnerText" style="color:#FFD700; margin:0 0 15px 0;">🎉 새망이 승리!</h1>
            <p id="winnerSubText" style="font-size:20px; margin:0;">3바퀴 완주 성공!</p>
            <button class="modal-btn" style="background:#1E90FF;" onclick="restartGame()">🔄 다시 경기하기</button>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        let scene, camera, renderer, trackCurve;
        let gameState = 'READY';
        let selectedDifficulty = 'MEDIUM';
        let rankCounter = 0;

        const CHARACTERS = [
            { id: "leader", name: "대장 새망이👑", bodyColor: 0x29B6F6, isPlayer: true },
            { id: "builder", name: "건설 새망이🔨", bodyColor: 0x29B6F6, isPlayer: false },
            { id: "scholar", name: "학자 새망이🎓", bodyColor: 0x29B6F6, isPlayer: false },
            { id: "artist", name: "화가 새망이🎨", bodyColor: 0x29B6F6, isPlayer: false },
            { id: "farmer", name: "농부 새망이🌾", bodyColor: 0x29B6F6, isPlayer: false },
            { id: "suit", name: "신사 새망이💼", bodyColor: 0x29B6F6, isPlayer: false },
            { id: "rocket", name: "우주 새망이🚀", bodyColor: 0x29B6F6, isPlayer: false }
        ];

        let karts = [];
        let playerKart;
        const totalLaps = 3;
        const totalCheckpoints = 12;
        let checkpoints = [];
        const trackWidth = 28;

        const keys = { forward: false, backward: false, left: false, right: false, boost: false, brake: false };

        init();
        animate();

        function init() {
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x81D4FA);

            camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 2500);
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById("gameCanvas").appendChild(renderer.domElement);

            const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
            scene.add(ambientLight);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
            dirLight.position.set(200, 400, 100);
            scene.add(dirLight);

            createCleanTrackAndWalls();
            createStartFinishLine();
            createEnvironment();
            spawnBirdKarts();

            updateCamera();

            window.addEventListener("keydown", (e) => handleKey(e, true));
            window.addEventListener("keyup", (e) => handleKey(e, false));
            window.addEventListener("resize", onWindowResize);
        }

        function selectDiff(diff, btn) {
            selectedDifficulty = diff;
            document.querySelectorAll('.diff-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        function createCleanTrackAndWalls() {
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
            const divisions = 400;
            const wallHeight = 2.0;

            const roadGeom = new THREE.BufferGeometry();
            const positions = [];
            const leftWallPos = [];
            const rightWallPos = [];

            for (let i = 0; i <= divisions; i++) {
                const t = i / divisions;
                const pt = trackCurve.getPointAt(t);
                const tan = trackCurve.getTangentAt(t);
                const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();

                const leftPt = pt.clone().add(norm.clone().multiplyScalar(trackWidth / 2));
                const rightPt = pt.clone().add(norm.clone().multiplyScalar(-trackWidth / 2));

                positions.push(leftPt.x, 0.25, leftPt.z);
                positions.push(rightPt.x, 0.25, rightPt.z);

                leftWallPos.push(leftPt.x, 0.25, leftPt.z);
                leftWallPos.push(leftPt.x, wallHeight + 0.25, leftPt.z);

                rightWallPos.push(rightPt.x, 0.25, rightPt.z);
                rightWallPos.push(rightPt.x, wallHeight + 0.25, rightPt.z);
            }

            const indices = [];
            for (let i = 0; i < divisions; i++) {
                const r1 = i * 2, r2 = (i + 1) * 2;
                indices.push(r1, r1 + 1, r2, r1 + 1, r2 + 1, r2);
            }

            roadGeom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
            roadGeom.setIndex(indices);
            roadGeom.computeVertexNormals();
            const roadMat = new THREE.MeshStandardMaterial({ color: 0x2A2A2A, side: THREE.DoubleSide, roughness: 0.8 });
            scene.add(new THREE.Mesh(roadGeom, roadMat));

            const wallMat = new THREE.MeshStandardMaterial({ color: 0x00B0FF, side: THREE.DoubleSide });

            const leftWallGeom = new THREE.BufferGeometry();
            leftWallGeom.setAttribute('position', new THREE.Float32BufferAttribute(leftWallPos, 3));
            leftWallGeom.setIndex(indices);
            leftWallGeom.computeVertexNormals();
            scene.add(new THREE.Mesh(leftWallGeom, wallMat));

            const rightWallGeom = new THREE.BufferGeometry();
            rightWallGeom.setAttribute('position', new THREE.Float32BufferAttribute(rightWallPos, 3));
            rightWallGeom.setIndex(indices);
            rightWallGeom.computeVertexNormals();
            scene.add(new THREE.Mesh(rightWallGeom, wallMat));

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
            const poleGeom = new THREE.CylinderGeometry(0.8, 0.8, 14);
            const poleMat = new THREE.MeshStandardMaterial({ color: 0x00B0FF });
            
            const p1 = new THREE.Mesh(poleGeom, poleMat); p1.position.set(-15, 7, 0);
            const p2 = new THREE.Mesh(poleGeom, poleMat); p2.position.set(15, 7, 0);
            
            const top = new THREE.Mesh(new THREE.BoxGeometry(32, 3, 2), new THREE.MeshStandardMaterial({ color: 0x0288D1 }));
            top.position.set(0, 13, 0);

            const signBoard = new THREE.Mesh(new THREE.BoxGeometry(20, 1.8, 2.2), new THREE.MeshStandardMaterial({ color: 0xFFD700 }));
            signBoard.position.set(0, 13, 0);

            archGroup.add(p1, p2, top, signBoard);
            archGroup.position.set(startPt.x, 0, startPt.z);
            archGroup.rotation.y = angle + Math.PI / 2;
            scene.add(archGroup);
        }

        function createEnvironment() {
            const grass = new THREE.Mesh(
                new THREE.PlaneGeometry(3000, 3000),
                new THREE.MeshStandardMaterial({ color: 0x4CAF50 })
            );
            grass.rotation.x = -Math.PI / 2;
            grass.position.y = 0;
            scene.add(grass);

            const buildingOffsets = [
                { t: 0.08, offset: 45, height: 45, width: 30, depth: 30, color: 0x0288D1 },
                { t: 0.22, offset: -50, height: 35, width: 25, depth: 25, color: 0x03A9F4 },
                { t: 0.38, offset: 52, height: 50, width: 32, depth: 28, color: 0x01579B },
                { t: 0.52, offset: -55, height: 38, width: 28, depth: 24, color: 0x0288D1 },
                { t: 0.70, offset: 48, height: 42, width: 26, depth: 26, color: 0x03A9F4 },
                { t: 0.88, offset: -50, height: 40, width: 30, depth: 30, color: 0x01579B }
            ];

            buildingOffsets.forEach(b => {
                const pt = trackCurve.getPointAt(b.t);
                const tan = trackCurve.getTangentAt(b.t);
                const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();
                const pos = pt.clone().add(norm.multiplyScalar(b.offset));

                const building = new THREE.Mesh(new THREE.BoxGeometry(b.width, b.height, b.depth), new THREE.MeshStandardMaterial({ color: 0xE0E0E0, roughness: 0.3 }));
                building.position.set(pos.x, b.height / 2, pos.z);

                const glass = new THREE.Mesh(new THREE.BoxGeometry(b.width * 0.9, b.height * 0.8, 0.5), new THREE.MeshStandardMaterial({ color: b.color, roughness: 0.1, metalness: 0.8 }));
                glass.position.set(0, 0, b.depth / 2 + 0.3);
                building.add(glass);

                const sign = new THREE.Mesh(new THREE.BoxGeometry(b.width * 0.8, 4, 2), new THREE.MeshStandardMaterial({ color: 0x00B0FF }));
                sign.position.set(0, b.height / 2 + 2, b.depth / 2);

                building.add(sign);
                scene.add(building);
            });

            for (let i = 0; i < 1.0; i += 0.02) {
                const pt = trackCurve.getPointAt(i);
                const tan = trackCurve.getTangentAt(i);
                const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();

                [-32, 32].forEach(offset => {
                    const pos = pt.clone().add(norm.clone().multiplyScalar(offset));
                    const treeGroup = new THREE.Group();
                    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.7, 4), new THREE.MeshStandardMaterial({ color: 0x5D4037 }));
                    trunk.position.y = 2;
                    const leaves = new THREE.Mesh(new THREE.ConeGeometry(3, 8, 8), new THREE.MeshStandardMaterial({ color: 0x2E7D32 }));
                    leaves.position.y = 7;
                    treeGroup.add(trunk, leaves);
                    treeGroup.position.set(pos.x, 0, pos.z);
                    scene.add(treeGroup);
                });
            }
        }

        function createBirdKartModel(p) {
            const group = new THREE.Group();

            const wheelGeom = new THREE.CylinderGeometry(0.5, 0.5, 0.4, 16);
            const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
            [[-1.2, 1.0], [1.2, 1.0], [-1.2, -1.0], [1.2, -1.0]].forEach(pos => {
                const w = new THREE.Mesh(wheelGeom, wheelMat);
                w.rotation.z = Math.PI / 2;
                w.position.set(pos[0], 0.25, pos[1]);
                group.add(w);
            });

            const baseMat = new THREE.MeshStandardMaterial({ color: 0x222222 });
            const base = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.3, 2.8), baseMat);
            base.position.y = 0.35;
            group.add(base);

            const birdBlueMat = new THREE.MeshStandardMaterial({ color: p.bodyColor, roughness: 0.2 });
            const body = new THREE.Mesh(new THREE.SphereGeometry(1.0, 16, 16), birdBlueMat);
            body.scale.set(1.0, 1.1, 1.0);
            body.position.set(0, 1.3, 0);
            group.add(body);

            const beakMat = new THREE.MeshStandardMaterial({ color: 0xFF8C00 });
            const beak = new THREE.Mesh(new THREE.ConeGeometry(0.35, 0.6, 8), beakMat);
            beak.rotation.x = Math.PI / 2;
            beak.position.set(0, 1.25, 0.9);
            group.add(beak);

            const eyeWhiteMat = new THREE.MeshStandardMaterial({ color: 0xFFFFFF });
            const eyeBlackMat = new THREE.MeshStandardMaterial({ color: 0x000000 });
            [-0.35, 0.35].forEach(x => {
                const eyeW = new THREE.Mesh(new THREE.SphereGeometry(0.22, 12, 12), eyeWhiteMat);
                eyeW.position.set(x, 1.45, 0.75);
                const eyeB = new THREE.Mesh(new THREE.SphereGeometry(0.12, 12, 12), eyeBlackMat);
                eyeB.position.set(x * 1.05, 1.45, 0.92);
                group.add(eyeW, eyeB);
            });

            if (p.id === "leader") {
                const crown = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.3, 0.5, 6), new THREE.MeshStandardMaterial({ color: 0xFFD700, metalness: 0.8 }));
                crown.position.set(0, 2.3, 0);
                const shirt = new THREE.Mesh(new THREE.CylinderGeometry(1.02, 1.02, 0.7, 16), new THREE.MeshStandardMaterial({ color: 0xFFD700 }));
                shirt.position.set(0, 0.95, 0);
                const cheekMat = new THREE.MeshStandardMaterial({ color: 0xFF5252 });
                const c1 = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 8), cheekMat); c1.position.set(-0.65, 1.2, 0.7);
                const c2 = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 8), cheekMat); c2.position.set(0.65, 1.2, 0.7);
                group.add(crown, shirt, c1, c2);

            } else if (p.id === "builder") {
                const helmet = new THREE.Mesh(new THREE.SphereGeometry(1.08, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xFFC107 }));
                helmet.position.set(0, 1.6, 0);
                const vest = new THREE.Mesh(new THREE.CylinderGeometry(1.02, 1.02, 0.6, 16), new THREE.MeshStandardMaterial({ color: 0xFF5722 }));
                vest.position.set(0, 0.9, 0);
                const hammer = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.8, 0.4), new THREE.MeshStandardMaterial({ color: 0x795548 }));
                hammer.position.set(1.1, 1.2, 0);
                group.add(helmet, vest, hammer);

            } else if (p.id === "scholar") {
                const hatTop = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.1, 1.5), new THREE.MeshStandardMaterial({ color: 0x212121 }));
                hatTop.position.set(0, 2.35, 0);
                const hatBase = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.3, 16), new THREE.MeshStandardMaterial({ color: 0x212121 }));
                hatBase.position.set(0, 2.15, 0);
                const glasses = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.05, 8, 16), new THREE.MeshStandardMaterial({ color: 0x111111 }));
                glasses.position.set(-0.35, 1.45, 0.85);
                const glasses2 = glasses.clone(); glasses2.position.set(0.35, 1.45, 0.85);
                const tie = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.6, 0.1), new THREE.MeshStandardMaterial({ color: 0xD32F2F }));
                tie.position.set(0, 0.8, 0.95);
                group.add(hatTop, hatBase, glasses, glasses2, tie);

            } else if (p.id === "artist") {
                const beret = new THREE.Mesh(new THREE.SphereGeometry(0.85, 16, 16), new THREE.MeshStandardMaterial({ color: 0xD32F2F }));
                beret.scale.set(1.2, 0.4, 1.2); beret.position.set(-0.2, 2.15, 0.1); beret.rotation.z = -0.3;
                const palette = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.8, 0.1), new THREE.MeshStandardMaterial({ color: 0x8D6E63 }));
                palette.position.set(-1.1, 1.2, 0.5); palette.rotation.y = 0.5;
                group.add(beret, palette);

            } else if (p.id === "farmer") {
                const strawHat = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 0.7, 0.2, 16), new THREE.MeshStandardMaterial({ color: 0xD7CCC8 }));
                strawHat.position.set(0, 2.15, 0);
                const overalls = new THREE.Mesh(new THREE.CylinderGeometry(1.02, 1.02, 0.7, 16), new THREE.MeshStandardMaterial({ color: 0x33691E }));
                overalls.position.set(0, 0.9, 0);
                group.add(strawHat, overalls);

            } else if (p.id === "suit") {
                const hat = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.9, 0.8, 16), new THREE.MeshStandardMaterial({ color: 0x1A237E }));
                hat.position.set(0, 2.2, 0);
                const suit = new THREE.Mesh(new THREE.CylinderGeometry(1.02, 1.02, 0.7, 16), new THREE.MeshStandardMaterial({ color: 0x1A237E }));
                suit.position.set(0, 0.9, 0);
                const briefcase = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.7, 0.9), new THREE.MeshStandardMaterial({ color: 0x3E2723 }));
                briefcase.position.set(1.1, 0.8, -0.2);
                group.add(hat, suit, briefcase);

            } else if (p.id === "rocket") {
                const helmet = new THREE.Mesh(new THREE.SphereGeometry(1.15, 16, 16), new THREE.MeshStandardMaterial({ color: 0xE0E0E0, transparent: true, opacity: 0.8 }));
                helmet.position.set(0, 1.45, 0);
                const rocket = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 1.4, 12), new THREE.MeshStandardMaterial({ color: 0xFF5722 }));
                rocket.rotation.x = Math.PI / 2; rocket.position.set(-0.6, 1.3, -1.1);
                const rocket2 = rocket.clone(); rocket2.position.set(0.6, 1.3, -1.1);
                group.add(helmet, rocket, rocket2);
            }

            return group;
        }

        function spawnBirdKarts() {
            const trackLen = trackCurve.getLength();

            CHARACTERS.forEach((p, i) => {
                const group = createBirdKartModel(p);

                group.info = p;
                group.lap = 1;
                group.nextCP = 1;
                group.finished = false;
                group.rank = 0;
                group.speed = 0;
                group.progressT = 0;
                group.laneOffset = (i % 2 === 0 ? 1 : -1) * (2.5 + Math.floor(i / 2) * 2.2);

                group.boosterCooldown = 0;
                group.boosterActive = 0;

                group.aiWobbleTimer = Math.random() * 100;
                group.aiTargetOffset = group.laneOffset;

                if (p.isPlayer) {
                    group.maxSpeed = 1.6;
                } else {
                    if (selectedDifficulty === 'EASY') group.maxSpeed = 1.1 + Math.random() * 0.15;
                    else if (selectedDifficulty === 'MEDIUM') group.maxSpeed = 1.45 + Math.random() * 0.15;
                    else if (selectedDifficulty === 'HARD') group.maxSpeed = 1.85 + Math.random() * 0.15;
                }

                const startT = (1 - (i * 12 / trackLen)) % 1;
                group.progressT = startT;

                const pt = trackCurve.getPointAt(startT);
                const tan = trackCurve.getTangentAt(startT);
                const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();

                group.position.copy(pt).add(norm.multiplyScalar(group.laneOffset));
                group.position.y = 0.25;
                group.rotation.y = Math.atan2(tan.x, tan.z);

                karts.push(group);
                scene.add(group);

                if (p.isPlayer) playerKart = group;
            });
        }

        function startCountdown() {
            document.getElementById("startScreen").style.display = "none";
            const cdEl = document.getElementById("countdown");
            cdEl.style.display = "block";

            karts.forEach(k => {
                if (!k.info.isPlayer) {
                    if (selectedDifficulty === 'EASY') k.maxSpeed = 1.1 + Math.random() * 0.15;
                    else if (selectedDifficulty === 'MEDIUM') k.maxSpeed = 1.45 + Math.random() * 0.15;
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

        function pauseGame() {
            if (gameState === 'RACING') {
                gameState = 'PAUSED';
                document.getElementById("pauseModal").style.display = "block";
            }
        }

        function resumeGame() {
            if (gameState === 'PAUSED') {
                gameState = 'RACING';
                document.getElementById("pauseModal").style.display = "none";
            }
        }

        function restartGame() {
            location.reload();
        }

        // [입력 키 설정: Shift 키를 브레이크로 바인딩]
        function handleKey(e, isDown) {
            if (e.code === "ArrowUp") keys.forward = isDown;
            if (e.code === "ArrowDown") keys.backward = isDown;
            if (e.code === "ArrowLeft") keys.left = isDown;
            if (e.code === "ArrowRight") keys.right = isDown;
            if (e.code === "Space") keys.boost = isDown;
            if (e.code === "ShiftLeft" || e.code === "ShiftRight") keys.brake = isDown; // Shift 키 브레이크

            if (isDown && e.code === "Escape") {
                if (gameState === 'RACING') pauseGame();
                else if (gameState === 'PAUSED') resumeGame();
            }

            if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space", "ShiftLeft", "ShiftRight"].includes(e.code)) e.preventDefault();
        }

        function syncProgressT(kart) {
            let bestT = kart.progressT;
            let minDist = 99999;
            for (let i = -8; i <= 8; i++) {
                let testT = (kart.progressT + i * 0.002 + 1) % 1;
                let p = trackCurve.getPointAt(testT);
                let d = kart.position.distanceTo(p);
                if (d < minDist) {
                    minDist = d;
                    bestT = testT;
                }
            }
            kart.progressT = bestT;
        }

        // 속도 비례 현실적 벽 충돌 물리
        function checkWallCollision(kart) {
            syncProgressT(kart);

            const pt = trackCurve.getPointAt(kart.progressT);
            const tan = trackCurve.getTangentAt(kart.progressT);
            const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();

            const toKart = new THREE.Vector3().subVectors(kart.position, pt);
            let offset = toKart.dot(norm);

            const maxOffset = (trackWidth / 2) - 1.2;

            if (Math.abs(offset) > maxOffset) {
                const currentSpeed = Math.abs(kart.speed);
                const isHighSpeed = currentSpeed > 0.85;

                if (isHighSpeed) {
                    // 고속 충돌: 물리 반발력으로 크게 튕겨남
                    const bounceDistance = Math.min(currentSpeed * 2.8, 4.2);
                    const clampedOffset = Math.sign(offset) * (maxOffset - bounceDistance);
                    kart.position.copy(pt).add(norm.multiplyScalar(clampedOffset));

                    kart.speed = Math.max(0.08, kart.speed * 0.15);
                    kart.rotation.y += (offset > 0 ? -0.4 : 0.4);
                } else {
                    // 저속 충돌: 튕김 없이 부드러운 감속
                    const clampedOffset = Math.sign(offset) * (maxOffset - 0.2);
                    kart.position.copy(pt).add(norm.multiplyScalar(clampedOffset));

                    kart.speed = Math.max(0.0, kart.speed * 0.45);
                }
                kart.position.y = 0.25;
            }
        }

        function checkKartToKartCollisions() {
            const collisionRadius = 2.6;

            for (let i = 0; i < karts.length; i++) {
                for (let j = i + 1; j < karts.length; j++) {
                    let k1 = karts[i];
                    let k2 = karts[j];

                    if (k1.finished || k2.finished) continue;

                    let dist = k1.position.distanceTo(k2.position);

                    if (dist < collisionRadius && dist > 0.01) {
                        let overlap = collisionRadius - dist;

                        let pushDir = new THREE.Vector3().subVectors(k1.position, k2.position).normalize();
                        pushDir.y = 0;

                        k1.position.add(pushDir.clone().multiplyScalar(overlap * 0.6));
                        k2.position.sub(pushDir.clone().multiplyScalar(overlap * 0.6));

                        k1.speed *= 0.55;
                        k2.speed *= 0.55;

                        k1.rotation.y += (Math.random() - 0.5) * 0.25;
                        k2.rotation.y += (Math.random() - 0.5) * 0.25;
                    }
                }
            }
        }

        function updatePhysics() {
            if (gameState !== 'RACING') return;

            karts.forEach((kart) => {
                if (kart.finished) return;

                if (kart.boosterActive > 0) {
                    kart.boosterActive--;
                } else if (kart.boosterCooldown > 0) {
                    kart.boosterCooldown--;
                }

                const currentMaxSpeed = kart.boosterActive > 0 ? kart.maxSpeed * 1.6 : kart.maxSpeed;

                if (kart.info.isPlayer) {
                    let isTurning = false;
                    if (keys.left) { kart.rotation.y += 0.028; isTurning = true; }
                    if (keys.right) { kart.rotation.y -= 0.028; isTurning = true; }

                    // [Shift 키 브레이크 물리]
                    if (keys.brake) {
                        if (kart.speed > 0) kart.speed = Math.max(0, kart.speed - 0.07);
                        else if (kart.speed < 0) kart.speed = Math.min(0, kart.speed + 0.07);
                    }

                    if (keys.forward) {
                        kart.speed = Math.min(kart.speed + 0.035, currentMaxSpeed);
                    } else if (keys.backward) {
                        kart.speed = Math.max(kart.speed - 0.03, -currentMaxSpeed / 2);
                    } else {
                        kart.speed *= 0.95;
                    }

                    // [현실적 코너링 마찰 감속] 고속으로 코너 조향 시 물리적 속도 감소
                    if (isTurning && Math.abs(kart.speed) > 0.4) {
                        let corneringDrag = 0.018 * (Math.abs(kart.speed) / currentMaxSpeed);
                        kart.speed *= (1.0 - corneringDrag);
                    }

                    if (keys.boost && kart.boosterCooldown === 0 && kart.boosterActive === 0) {
                        kart.boosterActive = 120;
                        kart.boosterCooldown = 600;
                        kart.speed = currentMaxSpeed;
                    }

                    kart.translateZ(kart.speed);
                    checkWallCollision(kart);

                } else {
                    // AI 조향 및 실수/코너링 감속 적용
                    kart.aiWobbleTimer++;
                    if (kart.aiWobbleTimer > 60 + Math.random() * 90) {
                        let errorMagnitude = selectedDifficulty === 'EASY' ? 12 : (selectedDifficulty === 'MEDIUM' ? 7.5 : 3.5);
                        kart.aiTargetOffset = kart.laneOffset + (Math.random() - 0.5) * errorMagnitude;
                        kart.aiWobbleTimer = 0;
                    }

                    if (kart.boosterCooldown === 0 && kart.boosterActive === 0 && Math.random() < 0.005) {
                        kart.boosterActive = 120;
                        kart.boosterCooldown = 600;
                    }

                    syncProgressT(kart);
                    
                    let lookAhead = selectedDifficulty === 'HARD' ? 0.018 : 0.011;
                    let targetT = (kart.progressT + lookAhead + 1) % 1;
                    let targetPt = trackCurve.getPointAt(targetT);
                    let tan = trackCurve.getTangentAt(targetT);
                    let norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();
                    let desiredPos = targetPt.clone().add(norm.multiplyScalar(kart.aiTargetOffset));

                    let dx = desiredPos.x - kart.position.x;
                    let dz = desiredPos.z - kart.position.z;
                    let targetAngle = Math.atan2(dx, dz);

                    let angleDiff = targetAngle - kart.rotation.y;
                    while (angleDiff > Math.PI) angleDiff -= Math.PI * 2;
                    while (angleDiff < -Math.PI) angleDiff += Math.PI * 2;

                    let maxTurnRate = 0.026;
                    let actualTurn = Math.max(-maxTurnRate, Math.min(maxTurnRate, angleDiff * 0.1));
                    kart.rotation.y += actualTurn;

                    // AI도 코너 조향 시 현실적인 가로 방향 감속 발생
                    if (Math.abs(actualTurn) > 0.015 && Math.abs(kart.speed) > 0.5) {
                        kart.speed *= 0.985;
                    }

                    kart.speed = Math.min(kart.speed + 0.03, currentMaxSpeed);
                    kart.translateZ(kart.speed);

                    checkWallCollision(kart);
                }

                const targetCP = checkpoints[kart.nextCP];
                if (kart.position.distanceTo(targetCP) < 40) {
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

            checkKartToKartCollisions();

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
                showWinnerModal(`🏆 ${finishedKart.info.name} 우승!`, `상대 라이벌이 먼저 완주했습니다.`);
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
            const offset = new THREE.Vector3(0, 6, -15);
            const cameraPos = offset.applyMatrix4(playerKart.matrixWorld);
            camera.position.lerp(cameraPos, 0.2);
            camera.lookAt(playerKart.position.x, playerKart.position.y + 1.8, playerKart.position.z);
        }

        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }

        function animate() {
            requestAnimationFrame(animate);
            updatePhysics();
            updateCamera();
            renderer.render(scene, camera);
        }
    </script>
</body>
</html>
"""

components.html(game_html, height=800, scrolling=False)
