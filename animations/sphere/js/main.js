import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const viewport = document.querySelector("#viewport");
const azimuthOutput = document.querySelector("#azimuth");
const elevationOutput = document.querySelector("#elevation");
const rotateButton = document.querySelector("#rotate-toggle");
const gridButton = document.querySelector("#grid-toggle");
const resetButton = document.querySelector("#reset-view");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const HOME_POSITION = new THREE.Vector3(0, 0.6, 3.9);
const SPHERE_RADIUS = 1;
const GRID_RADIUS = SPHERE_RADIUS * 1.0025;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
camera.position.copy(HOME_POSITION);

const renderer = createRenderer();
viewport.append(renderer.domElement);
renderer.domElement.setAttribute("aria-hidden", "true");

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.enablePan = false;
controls.minDistance = 1.75;
controls.maxDistance = 6;
controls.rotateSpeed = 0.7;
controls.zoomSpeed = 0.75;
controls.autoRotateSpeed = 0.55;

const globe = new THREE.Group();
globe.rotation.y = -0.38;
scene.add(globe);

const sphere = new THREE.Mesh(
  new THREE.SphereGeometry(SPHERE_RADIUS, 128, 96),
  new THREE.MeshPhysicalMaterial({
    color: 0x3d6fe0,
    roughness: 0.36,
    metalness: 0.04,
    clearcoat: 0.75,
    clearcoatRoughness: 0.28,
    emissive: 0x071a3c,
    emissiveIntensity: 0.55,
  }),
);
sphere.name = "sphere";
globe.add(sphere);

const graticule = createGraticule(GRID_RADIUS);
graticule.renderOrder = 1;
globe.add(graticule);

addLights(scene);

let autoRotate = !reduceMotion.matches;
setAutoRotate(autoRotate);

rotateButton.addEventListener("click", () => {
  setAutoRotate(!autoRotate);
});

gridButton.addEventListener("click", () => {
  const visible = !graticule.visible;
  graticule.visible = visible;
  gridButton.setAttribute("aria-pressed", String(visible));
});

resetButton.addEventListener("click", () => {
  camera.position
    .copy(HOME_POSITION)
    .normalize()
    .multiplyScalar(homeDistance);
  controls.target.set(0, 0, 0);
  controls.update();
});

// Dragging or zooming hands control to the viewer; they can restart the
// rotation from the toolbar.
controls.addEventListener("start", () => {
  if (autoRotate) setAutoRotate(false);
});

const canvas = renderer.domElement;
canvas.addEventListener("pointerdown", (event) => {
  if (event.button === 0) viewport.classList.add("is-dragging");
});
window.addEventListener("pointerup", () => viewport.classList.remove("is-dragging"));
window.addEventListener("pointercancel", () => {
  viewport.classList.remove("is-dragging");
});

reduceMotion.addEventListener("change", (event) => {
  if (event.matches) setAutoRotate(false);
});

let homeDistance = HOME_POSITION.length();
let lastReadoutUpdate = -Infinity;

const resizeObserver = new ResizeObserver(resize);
resizeObserver.observe(viewport);
resize();

renderer.setAnimationLoop((time) => {
  controls.update();
  updateReadout(time);
  renderer.render(scene, camera);
});

function createRenderer() {
  try {
    const instance = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    instance.setClearColor(0x000000, 0);
    instance.outputColorSpace = THREE.SRGBColorSpace;
    instance.toneMapping = THREE.ACESFilmicToneMapping;
    instance.toneMappingExposure = 1.05;
    return instance;
  } catch (error) {
    const message = document.createElement("p");
    message.className = "webgl-error";
    message.textContent =
      "无法创建 WebGL 上下文。请确认浏览器已启用硬件加速，或更换支持 WebGL 的浏览器。";
    viewport.append(message);
    throw error;
  }
}

function addLights(root) {
  const sky = new THREE.HemisphereLight(0xb8d3ff, 0x050815, 1.05);
  root.add(sky);

  const key = new THREE.DirectionalLight(0xfff1dd, 3.4);
  key.position.set(-3.6, 4.2, 4.6);
  root.add(key);

  const fill = new THREE.DirectionalLight(0x3f7dff, 1.35);
  fill.position.set(4.4, -1.4, 2.2);
  root.add(fill);

  const rim = new THREE.DirectionalLight(0x72dcff, 2.6);
  rim.position.set(0.8, 1.4, -4.8);
  root.add(rim);
}

/**
 * Latitude rings and longitude arcs slightly outside the sphere surface.
 * They give the otherwise uniform ball a visible frame of reference.
 */
function createGraticule(radius) {
  const group = new THREE.Group();
  const minorMaterial = new THREE.LineBasicMaterial({
    color: 0xa8c3ff,
    transparent: true,
    opacity: 0.26,
    depthWrite: false,
  });
  const equatorMaterial = new THREE.LineBasicMaterial({
    color: 0xffc97d,
    transparent: true,
    opacity: 0.68,
    depthWrite: false,
  });

  const circleSegments = 192;

  for (let latitude = -60; latitude <= 60; latitude += 30) {
    const phi = THREE.MathUtils.degToRad(latitude);
    const ringRadius = Math.cos(phi) * radius;
    const y = Math.sin(phi) * radius;
    const points = [];

    for (let i = 0; i < circleSegments; i += 1) {
      const theta = (i / circleSegments) * Math.PI * 2;
      points.push(
        new THREE.Vector3(
          Math.cos(theta) * ringRadius,
          y,
          Math.sin(theta) * ringRadius,
        ),
      );
    }

    group.add(
      new THREE.LineLoop(
        new THREE.BufferGeometry().setFromPoints(points),
        latitude === 0 ? equatorMaterial : minorMaterial,
      ),
    );
  }

  const meridianCount = 12;
  const meridianSegments = 96;

  for (let i = 0; i < meridianCount; i += 1) {
    const longitude = (i / meridianCount) * Math.PI * 2;
    const points = [];

    for (let j = 0; j <= meridianSegments; j += 1) {
      const latitude = -Math.PI / 2 + (j / meridianSegments) * Math.PI;
      const ringRadius = Math.cos(latitude) * radius;
      points.push(
        new THREE.Vector3(
          Math.cos(longitude) * ringRadius,
          Math.sin(latitude) * radius,
          Math.sin(longitude) * ringRadius,
        ),
      );
    }

    group.add(
      new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(points),
        minorMaterial,
      ),
    );
  }

  return group;
}

function setAutoRotate(enabled) {
  autoRotate = enabled;
  controls.autoRotate = enabled;
  rotateButton.setAttribute("aria-pressed", String(enabled));
}

function updateReadout(time) {
  if (time - lastReadoutUpdate < 80) return;
  lastReadoutUpdate = time;

  const azimuth = Math.round(
    THREE.MathUtils.radToDeg(controls.getAzimuthalAngle()),
  );
  const elevation = Math.round(
    90 - THREE.MathUtils.radToDeg(controls.getPolarAngle()),
  );

  azimuthOutput.textContent = `${azimuth}°`;
  elevationOutput.textContent = `${elevation}°`;
}

function resize() {
  const width = viewport.clientWidth;
  const height = viewport.clientHeight;

  if (width === 0 || height === 0) return;

  camera.aspect = width / height;
  camera.updateProjectionMatrix();

  const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  renderer.setPixelRatio(pixelRatio);
  renderer.setSize(width, height, false);

  // Keep the sphere comfortably inside the viewport on both wide and tall
  // screens, leaving room for the title and the toolbar.
  const aspect = width / height;
  const diameter =
    aspect < 0.85
      ? Math.min(width * 0.86, height * 0.5)
      : Math.min(width * 0.42, height * 0.68);
  const halfFovTangent = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
  const angularRadius = Math.atan((diameter / height) * halfFovTangent);

  homeDistance = SPHERE_RADIUS / Math.sin(angularRadius);
  controls.minDistance = Math.max(1.6, homeDistance * 0.55);
  controls.maxDistance = Math.max(8, homeDistance * 2.2);

  // Resize the viewing distance without changing the current orbit angle.
  const direction = camera.position.clone().sub(controls.target);
  if (direction.lengthSq() < 1e-8) direction.copy(HOME_POSITION);
  direction.normalize();
  camera.position
    .copy(controls.target)
    .addScaledVector(direction, homeDistance);
  controls.update();
}
