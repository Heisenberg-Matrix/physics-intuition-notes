/**
 * main.js — 组装：把物理 World、渲染 Renderer、主循环和参数界面连起来。
 *
 * 职责：
 *  - 尺寸 / 高 DPI 处理（逻辑坐标固定，DPR 只影响物理像素）
 *  - 固定时间步长的游戏循环（accumulator），保证运动不依赖显示刷新率
 *  - 把面板滑块 / 按钮 / 拖拽发射点绑定到 World 参数
 */

import { World } from './physics.js';
import { createRenderer } from './render.js';

const canvas = document.getElementById('scene');
const ctx = canvas.getContext('2d');
const world = new World();
const renderer = createRenderer(canvas);

/* ------------------------------ 尺寸与 DPI ------------------------------ */
let cssW = 0;
let cssH = 0;

function resize() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  cssW = canvas.clientWidth || window.innerWidth;
  cssH = canvas.clientHeight || window.innerHeight;
  canvas.width = Math.round(cssW * dpr);
  canvas.height = Math.round(cssH * dpr);
  // 主画布按 DPR 缩放，让 1 逻辑像素 = 1 CSS 像素，绘制清晰。
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  renderer.resize(cssW, cssH);
}
window.addEventListener('resize', resize);
resize();

/* --------------------------- 固定时间步长循环 --------------------------- */
const PHYS_DT = 1 / 240; // 物理定步长
let last = performance.now();
let acc = 0;
let paused = false;

// 每秒刷新一次状态栏（FPS、粒子数）——也用于可观测性验证。
let fpsFrames = 0;
let fpsLast = performance.now();
const statusEl = document.getElementById('status');

function updateStatus(fps) {
  const kinds = { flow: 0, body: 0, drop: 0 };
  for (const p of world.particles) kinds[p.kind] = (kinds[p.kind] || 0) + 1;
  statusEl.textContent =
    `FPS ${fps.toFixed(0)} · 粒子 ${world.particles.length}（水流 ${kinds.flow} / 主体 ${kinds.body} / 水珠 ${kinds.drop}）`;
}

function frame(now) {
  // —— FPS 统计 ——
  fpsFrames++;
  if (now - fpsLast >= 1000) {
    updateStatus((fpsFrames * 1000) / (now - fpsLast));
    fpsFrames = 0;
    fpsLast = now;
  }
  // dt 以秒记，并限制单帧最大 0.1s，防止切后台后跳步。
  let dt = Math.min(0.1, (now - last) / 1000);
  last = now;

  if (!paused) {
    acc += dt;
    const maxSteps = 6;
    let steps = 0;
    while (acc >= PHYS_DT && steps < maxSteps) {
      world.update(PHYS_DT);
      acc -= PHYS_DT;
      steps++;
    }
    if (acc > PHYS_DT) acc = 0; // 丢弃溢出的累计时间
  } else {
    acc = 0;
  }

  // 绘制场景
  ctx.clearRect(0, 0, cssW, cssH);
  drawScene();

  requestAnimationFrame(frame);
}

/** 浅色背景 + 地面 + 水流。 */
function drawScene() {
  // 背景
  const bg = ctx.createLinearGradient(0, 0, 0, cssH);
  bg.addColorStop(0, '#eef6ff');
  bg.addColorStop(1, '#ddeafb');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, cssW, cssH);

  const groundY = world.params.groundY;

  // 发射点标记（可拖动）
  const sx = world.params.startX;
  const sy = world.params.startY;
  ctx.strokeStyle = 'rgba(40,90,160,0.35)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(sx, sy, 8, 0, Math.PI * 2);
  ctx.stroke();

  // 地面（画在水流下方）
  ctx.fillStyle = '#b6d3a8';
  ctx.fillRect(0, groundY, cssW, cssH - groundY);
  ctx.fillStyle = '#7fb56a';
  ctx.fillRect(0, Math.max(0, groundY - 3), cssW, 3);

  // 水流主体
  renderer.draw(world, cssW, cssH);
}

world.setParams({ groundY: Math.round(cssH * 0.78) });
world.setParams({ startX: Math.round(cssW * 0.42), startY: Math.round(cssH * 0.14) });

// 默认斜抛：角度 60°（向上）、力度 300 lp/s → 由角度/力度换算成 vx、vy。
// 物理层仍然只认 velocityX / velocityY，架构不变。
const DEFAULT_ANGLE = 60;
const DEFAULT_SPEED = 300;
function velocityFrom(angleDeg, speed) {
  const rad = (angleDeg * Math.PI) / 180;
  return {
    velocityX: speed * Math.cos(rad),
    velocityY: -speed * Math.sin(rad), // 屏幕坐标 Y 向下，向上为负
  };
}
world.setParams(velocityFrom(DEFAULT_ANGLE, DEFAULT_SPEED));

/* ------------------------------ UI 绑定 ------------------------------ */
const bindings = [
  ['startX', 'range'],
  ['startY', 'range'],
  ['velocityX', 'range'],
  ['velocityY', 'range'],
  ['gravity', 'range'],
  ['emissionRate', 'range'],
  ['particleRadius', 'range'],
  ['groundY', 'range'],
];

const inputs = {};
for (const [key] of bindings) {
  const el = document.getElementById('p-' + key);
  const val = document.getElementById('v-' + key);
  if (!el) continue;
  inputs[key] = { el, val };
  el.value = world.params[key];
  val.textContent = round(world.params[key]);
  el.addEventListener('input', () => {
    const v = parseFloat(el.value) || 0;
    world.setParam(key, v);
    val.textContent = round(v);
    // 直接改 vx / vy 时，角度与力度显示同步更新（单向派生，不回写 vx/vy）。
    if (key === 'velocityX' || key === 'velocityY') writeAngleSpeedUI();
  });
}

function round(x) {
  return Math.round(x * 100) / 100;
}

/* -------------------- 角度 + 力度（从 vx/vy 派生 / 回写） -------------------- */
const angleEl = document.getElementById('p-angle');
const angleVal = document.getElementById('v-angle');
const speedEl = document.getElementById('p-speed');
const speedVal = document.getElementById('v-speed');

// 由世界当前 vx/vy 反推角度、力度，刷新这两个滑块。
function writeAngleSpeedUI() {
  const vx = world.params.velocityX;
  const vy = world.params.velocityY;
  const speed = Math.hypot(vx, vy);
  const angle = (Math.atan2(-vy, vx) * 180) / Math.PI; // 向上为正
  angleEl.value = round(angle);
  angleVal.textContent = round(angle);
  speedEl.value = round(speed);
  speedVal.textContent = round(speed);
}

// 由角度 + 力度回写 vx/vy，并同步所有相关控件。
function applyAngleSpeed(angleDeg, speed) {
  world.setParams(velocityFrom(angleDeg, speed));
  // 同步 vx / vy 滑块
  for (const k of ['velocityX', 'velocityY']) {
    const it = inputs[k];
    if (!it) continue;
    it.el.value = round(world.params[k]);
    it.val.textContent = round(world.params[k]);
  }
  angleEl.value = round(angleDeg);
  angleVal.textContent = round(angleDeg);
  speedEl.value = round(speed);
  speedVal.textContent = round(speed);
}

angleEl.addEventListener('input', () => {
  applyAngleSpeed(parseFloat(angleEl.value) || 0, parseFloat(speedEl.value) || 0);
});
speedEl.addEventListener('input', () => {
  applyAngleSpeed(parseFloat(angleEl.value) || 0, parseFloat(speedEl.value) || 0);
});

// 一键预设：平抛（0°）/ 斜抛（60°），保留当前力度。
const horizontalBtn = document.getElementById('btn-horizontal');
const obliqueBtn = document.getElementById('btn-oblique');
horizontalBtn.addEventListener('click', () => {
  applyAngleSpeed(0, parseFloat(speedEl.value) || DEFAULT_SPEED);
});
obliqueBtn.addEventListener('click', () => {
  applyAngleSpeed(DEFAULT_ANGLE, parseFloat(speedEl.value) || DEFAULT_SPEED);
});

writeAngleSpeedUI();

/* 按钮：开/关 水流 */
const flowBtn = document.getElementById('btn-flow');
function syncFlowBtn() {
  flowBtn.textContent = world.params.enable ? '停止水流' : '开启水流';
}
flowBtn.addEventListener('click', () => {
  world.setParam('enable', !world.params.enable);
  syncFlowBtn();
});

/* 按钮：暂停/继续 */
const pauseBtn = document.getElementById('btn-pause');
pauseBtn.addEventListener('click', () => {
  paused = !paused;
  pauseBtn.textContent = paused ? '继续' : '暂停';
});

/* 按钮：重置 */
const resetBtn = document.getElementById('btn-reset');
resetBtn.addEventListener('click', () => {
  world.clear();
  syncFlowBtn();
});

/* 拖动发射点 */
let dragging = false;
canvas.addEventListener('pointerdown', (e) => {
  dragging = true;
  moveEmitter(e);
});
window.addEventListener('pointermove', (e) => {
  if (dragging) moveEmitter(e);
});
window.addEventListener('pointerup', () => {
  dragging = false;
});

function moveEmitter(e) {
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  world.setParam('startX', clamp(x, 0, cssW));
  world.setParam('startY', clamp(y, 0, cssH));
  inputs.startX.el.value = Math.round(x);
  inputs.startX.val.textContent = Math.round(x);
  inputs.startY.el.value = Math.round(y);
  inputs.startY.val.textContent = Math.round(y);
}

function clamp(v, a, b) {
  return Math.max(a, Math.min(b, v));
}

syncFlowBtn();
requestAnimationFrame(frame);

// 供自动化测试 / 调试钩子（不影响正常使用）。
window.__lab = {
  world,
  isPaused: () => paused,
  setPaused(v) {
    paused = !!v;
    pauseBtn.textContent = paused ? '继续' : '暂停';
  },
  applyAngleSpeed,
  getAngleSpeed() {
    const { velocityX, velocityY } = world.params;
    return {
      angle: (Math.atan2(-velocityY, velocityX) * 180) / Math.PI,
      speed: Math.hypot(velocityX, velocityY),
    };
  },
};