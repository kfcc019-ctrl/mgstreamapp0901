import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="포켓몬 3D 카트라이더", layout="wide")

st.title("⚡ 3D 포켓몬 카트라이더 (Back View Ver.)")
st.write("방향키(↑↓←→)로 이동하고, **Space바**를 눌러 **백만볼트 부스터**를 사용하세요!")
st.write("당신의 포켓몬: **피카츄⚡**")
st.write("상대 포켓몬(6마리): **이상해씨🌱, 파이리🔥, 꼬북이💧, 야돈🌀, 고오스👻, 냐옹🐾**")

# Three.js 3D 엔진 기반 게임 코드
game_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background-color: #1a1a1a; display: flex; justify-content: center; align-items: center; height: 100vh;}
        #gameCanvas { width: 100%; height: 100%; border: 4px solid #fff; border-radius: 12px; }
    </style>
</head>
<body>
    <div id="gameCanvas"></div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        // --- 1. Three.js 기본 설정 ---
        let scene, camera, renderer;
        let container = document.getElementById("gameCanvas");

        // --- 2. 플레이어 및 상대 포켓몬 설정 ---
        const POKEMONS = [
            { name: "Pikachu", color: 0xFFD700 }, // ⚡ 플레이어
            { name: "Bulbasaur", color: 0x32CD32 }, // 🌱 AI 1
            { name: "Charmander", color: 0xFF4500 }, // 🔥 AI 2
            { name: "Squirtle", color: 0x1E90FF }, // 💧 AI 3
            { name: "Slowpoke", color: 0xFFB6C1 }, // 🌀 AI 4
            { name: "Gastly", color: 0x800080 }, // 👻 AI 5
            { name: "Meowth", color: 0xFFA500 } // 🐾 AI 6
        ];

        let karts = [];
        let playerKartIndex = 0;
        const kartSize = 1.5;

        // --- 3. 트랙 설정 ---
        const trackRadiusX = 150;
        const trackRadiusZ = 100;
        const trackWidth = 25;

        // --- 4. 키 입력 상태 ---
        const keys = { forward: false, backward: false, left: false, right: false, boost: false };
        let boostTimer = 0;
        const boostDuration = 100; // 프레임 단위

        init();
        animate();

        function init() {
            // 장면(Scene), 카메라(Camera), 렌더러(Renderer)
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x33CCFF); // 하늘색 배경
            
            camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            container.appendChild(renderer.domElement);

            // 조명
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(100, 100, 100);
            scene.add(directionalLight);

            // 트랙 및 잔디밭
            createTrack();

            // 포켓몬 카트 생성 및 배치
            for (let i = 0; i < POKEMONS.length; i++) {
                const kart = createKart(POKEMONS[i].color, i);
                karts.push(kart);
                scene.add(kart);
            }

            // 카메라 초기 위치 (플레이어 뒤)
            updateCameraPosition();

            // 이벤트 리스너
            window.addEventListener("keydown", onKeyDown);
            window.addEventListener("keyup", onKeyUp);
            window.addEventListener("resize", onWindowResize);
        }

        function createKart(color, index) {
            const group = new THREE.Group();
            
            // 카트 본체
            const bodyGeometry = new THREE.BoxGeometry(kartSize, 1, kartSize * 1.5);
            const bodyMaterial = new THREE.MeshStandardMaterial({ color: color });
            const bodyMesh = new THREE.Mesh(bodyGeometry, bodyMaterial);
            group.add(bodyMesh);

            // 바퀴 (간단한 실린더)
            const wheelGeometry = new THREE.CylinderGeometry(0.3, 0.3, 0.2, 16);
            const wheelMaterial = new THREE.MeshStandardMaterial({ color: 0x000000 });
            for (let i = 0; i < 4; i++) {
                const wheel = new THREE.Mesh(wheelGeometry, wheelMaterial);
                wheel.rotation.z = Math.PI / 2;
                wheel.position.x = (i < 2 ? 1.1 : -1.1) * kartSize / 2;
                wheel.position.z = (i % 2 === 0 ? 1 : -1) * kartSize;
                wheel.position.y = -0.5;
                group.add(wheel);
            }

            // 초기 위치 및 각도 설정
            group.speed = 0;
            group.maxSpeed = index === playerKartIndex ? 10 : 6 + Math.random() * 2; // AI 속도 랜덤
            group.accel = 0.25;
            group.friction = 0.08;
            group.turnSpeed = 0.05;
            group.targetAngle = (index / POKEMONS.length) * Math.PI * 2;
            group.currentPositionOnTrack = group.targetAngle;

            const radius = index % 2 === 0 ? trackRadiusX + trackWidth / 2 : trackRadiusX - trackWidth / 2;
            group.position.x = radius * Math.cos(group.currentPositionOnTrack);
            group.position.z = (index % 2 === 0 ? trackRadiusZ + trackWidth / 2 : trackRadiusZ - trackWidth / 2) * Math.sin(group.currentPositionOnTrack);
            group.rotation.y = -group.currentPositionOnTrack - Math.PI / 2; // 초기 회전

            return group;
        }

        function createTrack() {
            // 잔디밭
            const grassGeometry = new THREE.PlaneGeometry(1000, 1000);
            const grassMaterial = new THREE.MeshStandardMaterial({ color: 0x228B22, side: THREE.DoubleSide });
            const grass = new THREE.Mesh(grassGeometry, grassMaterial);
            grass.rotation.x = Math.PI / 2;
            grass.position.y = -0.6;
            scene.add(grass);

            // 타원형 도로 (카트라이더 트랙)
            const trackPath = new THREE.Shape();
            const seg = 100;
            for (let i = 0; i <= seg; i++) {
                const theta = (i / seg) * Math.PI * 2;
                trackPath.moveTo(trackRadiusX * Math.cos(theta), trackRadiusZ * Math.sin(theta));
                trackPath.lineTo((trackRadiusX + trackWidth) * Math.cos(theta), (trackRadiusZ + trackWidth) * Math.sin(theta));
            }
            
            const trackGeometry = new THREE.RingGeometry(trackRadiusZ, trackRadiusZ + trackWidth, seg, 1, 0, Math.PI * 2);
            // 3D 도로 질감 (실제 트랙 느낌)
            const trackTexture = new THREE.TextureLoader().load("https://threejs.org/examples/textures/crate.gif");
            trackTexture.wrapS = trackTexture.wrapT = THREE.RepeatWrapping;
            trackTexture.repeat.set(50, 4);
            const trackMaterial = new THREE.MeshStandardMaterial({ map: trackTexture, side: THREE.DoubleSide });
            const track = new THREE.Mesh(trackGeometry, trackMaterial);
            track.rotation.x = Math.PI / 2;
            track.position.y = -0.55;
            scene.add(track);
        }

        function updateKart(kart, isPlayer, index) {
            if (isPlayer) {
                // 플레이어 조종
                if (keys.left) kart.rotation.y += kart.turnSpeed * (kart.speed !== 0 ? Math.sign(kart.speed) : 1);
                if (keys.right) kart.rotation.y -= kart.turnSpeed * (kart.speed !== 0 ? Math.sign(kart.speed) : 1);

                if (keys.forward) {
                    kart.speed = Math.min(kart.speed + kart.accel, kart.maxSpeed);
                } else if (keys.backward) {
                    kart.speed = Math.max(kart.speed - kart.accel, -kart.maxSpeed / 2);
                } else {
                    if (kart.speed > 0) kart.speed = Math.max(0, kart.speed - kart.friction);
                    if (kart.speed < 0) kart.speed = Math.min(0, kart.speed + kart.friction);
                }

                // 부스터 효과
                if (keys.boost && boostTimer === 0) {
                    boostTimer = boostDuration;
                    kart.speed = kart.maxSpeed * 1.6;
                }
                
            } else {
                // AI 조종 (간단한 타원 경로 따라가기)
                const radiusX = index % 2 === 0 ? trackRadiusX + trackWidth / 2 : trackRadiusX - trackWidth / 2;
                const radiusZ = index % 2 === 0 ? trackRadiusZ + trackWidth / 2 : trackRadiusZ - trackWidth / 2;
                kart.currentPositionOnTrack += kart.maxSpeed * 0.0001; // AI 속도에 비례
                kart.position.x = radiusX * Math.cos(kart.currentPositionOnTrack);
                kart.position.z = radiusZ * Math.sin(kart.currentPositionOnTrack);
                kart.rotation.y = -kart.currentPositionOnTrack - Math.PI / 2;
            }

            if (boostTimer > 0) boostTimer--;

            if (isPlayer) {
                // 플레이어 이동 (3D 좌표계)
                kart.translateZ(kart.speed * 0.1);
            }
        }

        function updateCameraPosition() {
            const player = karts[playerKartIndex];
            if (!player) return;

            // 플레이어 뒤 + 위 시점 (카트라이더 백뷰)
            const offset = new THREE.Vector3(0, 8, -20); // x=0, y=높이, z=거리 (플레이어 기준)
            const cameraPosition = offset.applyMatrix4(player.matrixWorld);
            camera.position.lerp(cameraPosition, 0.2); // 부드러운 카메라 팔로잉
            camera.lookAt(player.position.x, player.position.y + 2, player.position.z);
        }

        function onKeyDown(e) {
            if (e.code === "ArrowUp") keys.forward = true;
            if (e.code === "ArrowDown") keys.backward = true;
            if (e.code === "ArrowLeft") keys.left = true;
            if (e.code === "ArrowRight") keys.right = true;
            if (e.code === "Space") keys.boost = true;
            if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(e.code)) e.preventDefault();
        }

        function onKeyUp(e) {
            if (e.code === "ArrowUp") keys.forward = false;
            if (e.code === "ArrowDown") keys.backward = false;
            if (e.code === "ArrowLeft") keys.left = false;
            if (e.code === "ArrowRight") keys.right = false;
            if (e.code === "Space") keys.boost = false;
        }

        function onWindowResize() {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }

        function animate() {
            requestAnimationFrame(animate);

            for (let i = 0; i < karts.length; i++) {
                updateKart(karts[i], i === playerKartIndex, i);
            }

            // 카메라 위치 업데이트 (플레이어 뒤)
            updateCameraPosition();

            renderer.render(scene, camera);
        }
    </script>
</body>
</html>
"""

components.html(game_html, height=750, scrolling=False)
