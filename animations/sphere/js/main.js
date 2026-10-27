import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const viewport = document.querySelector("#viewport");
const rotateButton = document.querySelector("#rotate-toggle");
const resetButton = document.querySelector("#reset-view");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const SPHERE_RADIUS = 1;
const SPHERE_CENTER = new THREE.Vector3(0, SPHERE_RADIUS, 0);
const INITIAL_SPIN = -0.4;
const HOME_SPHERICAL = new THREE.Spherical(
  1,
  THREE.MathUtils.degToRad(67),
  THREE.MathUtils.degToRad(24),
);
const HOME_DIRECTION = new THREE.Vector3().setFromSpherical(HOME_SPHERICAL);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
camera.position
  .copy(SPHERE_CENTER)
  .addScaledVector(HOME_DIRECTION, 5);

const renderer = createRenderer();
viewport.append(renderer.domElement);
renderer.domElement.setAttribute("aria-hidden", "true");

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.copy(SPHERE_CENTER);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.enablePan = false;
controls.rotateSpeed = 0.55;
controls.zoomSpeed = 0.65;
controls.minPolarAngle = THREE.MathUtils.degToRad(20);
controls.maxPolarAngle = THREE.MathUtils.degToRad(86);

const globe = new THREE.Group();
globe.position.copy(SPHERE_CENTER);
globe.rotation.y = INITIAL_SPIN;
scene.add(globe);

const textures = createHandmadeTextures(renderer);
const sphere = new THREE.Mesh(
  new THREE.SphereGeometry(SPHERE_RADIUS, 128, 96),
  new THREE.MeshStandardMaterial({
    map: textures.map,
    bumpMap: textures.bumpMap,
    bumpScale: 0.009,
    roughness: 0.93,
    metalness: 0,
  }),
);
sphere.castShadow = true;
globe.add(sphere);

const shadowCatcher = new THREE.Mesh(
  new THREE.PlaneGeometry(16, 16),
  new THREE.ShadowMaterial({
    color: 0x4f4436,
    opacity: 0.18,
    depthWrite: false,
  }),
);
shadowCatcher.rotation.x = -Math.PI / 2;
shadowCatcher.receiveShadow = true;
scene.add(shadowCatcher);

addLights();

let autoRotate = !reduceMotion.matches;
setAutoRotate(autoRotate);

rotateButton.addEventListener("click", () => {
  setAutoRotate(!autoRotate);
});

resetButton.addEventListener("click", () => {
  globe.rotation.set(0, INITIAL_SPIN, 0);
  camera.position
    .copy(SPHERE_CENTER)
    .addScaledVector(HOME_DIRECTION, homeDistance);
  controls.target.copy(SPHERE_CENTER);
  controls.update();
});

// Taking control stops the spin so the current side can be studied.
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

let homeDistance = 5;
const resizeObserver = new ResizeObserver(resize);
resizeObserver.observe(viewport);
resize();

const clock = new THREE.Clock();

renderer.setAnimationLoop(() => {
  const delta = Math.min(clock.getDelta(), 0.05);

  if (autoRotate) {
    globe.rotation.y += delta * 0.16;
  }

  controls.update();
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
    instance.toneMappingExposure = 1.12;
    instance.shadowMap.enabled = true;
    instance.shadowMap.type = THREE.PCFSoftShadowMap;
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

function addLights() {
  const sky = new THREE.HemisphereLight(0xfff8e8, 0xc8b79f, 0.95);
  scene.add(sky);

  const key = new THREE.DirectionalLight(0xfff0d8, 2.9);
  key.position.set(-2, 11, 3);
  key.target.position.set(0, 0.9, 0);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.left = -3;
  key.shadow.camera.right = 3;
  key.shadow.camera.top = 3;
  key.shadow.camera.bottom = -3;
  key.shadow.camera.near = 1;
  key.shadow.camera.far = 20;
  key.shadow.bias = -0.0003;
  key.shadow.normalBias = 0.02;
  key.shadow.radius = 6;
  scene.add(key, key.target);

  const fill = new THREE.DirectionalLight(0xd5e3dd, 0.45);
  fill.position.set(5, 3, 4);
  scene.add(fill);

  const rim = new THREE.DirectionalLight(0xffe4bf, 0.75);
  rim.position.set(2, 4, -5);
  scene.add(rim);
}

/**
 * Soft, hand-worked surface: low-contrast mottling plus fine clay-like flecks.
 * The pattern is drawn with a small horizontal wrap so the UV seam stays hidden.
 */
function createHandmadeTextures(renderer) {
  const random = mulberry32(20261027);
  const map = createSpeckledTexture(1024, 512, {
    base: "#789789",
    light: "166,183,165",
    dark: "94,118,106",
    fleckLight: "238,228,206",
    fleckDark: "68,85,75",
    blobs: 28,
    flecks: 1900,
  }, random);

  const bumpMap = createSpeckledTexture(512, 256, {
    base: "#808080",
    light: "156,156,156",
    dark: "103,103,103",
    fleckLight: "190,190,190",
    fleckDark: "65,65,65",
    blobs: 22,
    flecks: 1200,
  }, random, THREE.NoColorSpace);

  const anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  for (const texture of [map, bumpMap]) {
    texture.anisotropy = anisotropy;
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
  }

  map.colorSpace = THREE.SRGBColorSpace;
  bumpMap.colorSpace = THREE.NoColorSpace;

  return { map, bumpMap };
}

function createSpeckledTexture(width, height, palette, random, colorSpace) {
  const surface = document.createElement("canvas");
  surface.width = width;
  surface.height = height;

  const ctx = surface.getContext("2d");
  ctx.fillStyle = palette.base;
  ctx.fillRect(0, 0, width, height);

  for (let i = 0; i < palette.blobs; i += 1) {
    const x = random() * width;
    const y = random() * height;
    const radius = 35 + random() * 150;
    const color = random() > 0.48 ? palette.light : palette.dark;
    const alpha = 0.045 + random() * 0.08;

    for (const offset of [-width, 0, width]) {
      const gradient = ctx.createRadialGradient(
        x + offset,
        y,
        0,
        x + offset,
        y,
        radius,
      );
      gradient.addColorStop(0, `rgba(${color},${alpha})`);
      gradient.addColorStop(0.6, `rgba(${color},${alpha * 0.55})`);
      gradient.addColorStop(1, `rgba(${color},0)`);
      ctx.fillStyle = gradient;
      ctx.fillRect(x + offset - radius, y - radius, radius * 2, radius * 2);
    }
  }

  for (let i = 0; i < palette.flecks; i += 1) {
    const x = random() * width;
    const y = random() * height;
    const radius = 0.35 + random() * 1.45;
    const light = random() > 0.45;
    const alpha = 0.035 + random() * 0.1;

    ctx.fillStyle = `rgba(${light ? palette.fleckLight : palette.fleckDark},${alpha})`;
    for (const offset of [-width, 0, width]) {
      ctx.beginPath();
      ctx.arc(x + offset, y, radius, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const texture = new THREE.CanvasTexture(surface);
  texture.colorSpace = colorSpace;
  return texture;
}

function mulberry32(seed) {
  return function random() {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let value = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    value = (value + Math.imul(value ^ (value >>> 7), 61 | value)) ^ value;
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function setAutoRotate(enabled) {
  autoRotate = enabled;
  rotateButton.setAttribute("aria-pressed", String(enabled));
}

function resize() {
  const width = viewport.clientWidth;
  const height = viewport.clientHeight;

  if (width === 0 || height === 0) return;

  camera.aspect = width / height;
  camera.updateProjectionMatrix();

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(width, height, false);

  // Fit the ball inside the open space, independent of the camera angle.
  const aspect = width / height;
  const diameter =
    aspect < 0.85
      ? Math.min(width * 0.8, height * 0.44)
      : Math.min(width * 0.4, height * 0.62);
  const halfFovTangent = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
  const angularRadius = Math.atan((diameter / height) * halfFovTangent);

  homeDistance = SPHERE_RADIUS / Math.sin(angularRadius);
  controls.minDistance = Math.max(2.1, homeDistance * 0.6);
  controls.maxDistance = homeDistance * 2.4;

  const direction = camera.position.clone().sub(controls.target);
  if (direction.lengthSq() < 1e-8) direction.copy(HOME_DIRECTION);
  direction.normalize();
  camera.position
    .copy(controls.target)
    .addScaledVector(direction, homeDistance);
  controls.update();
}
