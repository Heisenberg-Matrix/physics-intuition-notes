/**
 * 纯物理模块的独立运行测试（无需浏览器）。
 * 运行：node tests/physics.test.mjs
 * 只测 physics.js（无 DOM / Canvas 依赖）。
 */
import { World } from '../js/physics.js';

let pass = 0;
let fail = 0;
function assert(name, cond, extra = '') {
  if (cond) {
    pass++;
  } else {
    fail++;
    console.error('  ✗ FAIL:', name, extra);
  }
}

const G = 620;

function make(over = {}) {
  return new World(Object.assign(
    {
      startX: 0, startY: 0, velocityX: 0, velocityY: 0,
      emissionRate: 0, particleRadius: 5, gravity: G, groundY: 300,
      flowTTL: 4, maxParticles: 5000, enable: false, jitter: 0,
    },
    over
  ));
}

const dt = 1 / 240;

/* 1. 重力：静止粒子经过一个子步后 vy > 0 且 y 增加 */
{
  const w = make();
  w._emitOne();
  const p = w.particles[0];
  const before = { y: p.y, vy: p.vy };
  for (let i = 0; i < 60; i++) w.update(dt); // 累计 0.25s
  assert('重力使 vy 增加', p.vy > before.vy, `before=${before.vy} after=${p.vy}`);
  assert('重力使 y 增加（下落）', p.y > before.y, `y=${p.y}`);
}

// 2. 自由落体位移与解析解一致
{
  const w = make();
  w._emitOne();
  const p = w.particles[0];
  const y0 = p.y, vy0 = p.vy;
  for (let i = 0; i < 120; i++) w.update(dt); // 0.5s
  const t = 120 * dt;
  const expect = y0 + vy0 * t + 0.5 * G * t * t;
  assert('自由落体位移接近解析解', Math.abs(p.y - expect) < 1.0, `got=${p.y} expect=${expect}`);
}

// 3. 抛体：水平速度恒定（抬高地面避免提前碰撞）
{
  const w = make({ velocityX: 120, velocityY: 0, groundY: 100000 });
  w._emitOne();
  const p = w.particles[0];
  const x0 = p.x;
  for (let i = 0; i < 300; i++) w.update(dt); // 1.25s
  assert('水平位移 ≈ vx*t', Math.abs(p.x - x0 - 120 * 1.25) < 2, `dx=${p.x - x0}`);
}

// 4. 开启发射产得粒子；关闭后不再新增
{
  const w = make({ emissionRate: 100, enable: true });
  w.update(1 / 60); const n1 = w.particles.length;
  w.update(1 / 60); const n2 = w.particles.length;
  assert('开启发射时粒子增加', n2 > n1, `${n1}->${n2}`);
  w.setParam('enable', false);
  const after = w.particles.length;
  for (let i = 0; i < 30; i++) w.update(1 / 60);
  assert('关闭发射后不再新增', w.particles.length <= after, `${after}->${w.particles.length}`);
}

// 5. 地面碰撞：撞击后出现融合主体 + 独立水珠，粒子不穿透地面
{
  const w = make({ groundY: 300, velocityX: 50, velocityY: 300, enable: true, emissionRate: 200 });
  let hitBody = false, hitDrop = false, ran = 0;
  for (let i = 0; i < 8000 && !(hitBody && hitDrop); i++) {
    w.update(dt);
    ran++;
    for (const p of w.particles) {
      if (p.kind === 'body') hitBody = true;
      if (p.kind === 'drop') hitDrop = true;
      assert('粒子不落到地面以下', p.y + p.r <= w.params.groundY + 2, `y=${p.y} r=${p.r}`);
    }
  }
  assert('撞击产生融合主体', hitBody);
  assert('撞击产生独立水珠', hitDrop);
}

// 6. 生命周期回收：flow 粒子 ttl 过后被清理
{
  const w = make({ velocityY: -200, flowTTL: 0.4 });
  w._emitOne();
  w.update(1 / 60);
  assert('初始有粒子', w.particles.length === 1);
  for (let i = 0; i < 200; i++) w.update(1 / 60); // 3.3s >> ttl
  const flow = w.particles.filter((p) => p.kind === 'flow');
  assert('flow 粒子在 ttl 后被清理', flow.length === 0, `remaining flow=${flow.length}`);
}

// 7. 数量上限
{
  const w = make({ emissionRate: 5000, maxParticles: 50, flowTTL: 10 });
  for (let i = 0; i < 2000; i++) w._emitOne();
  w.update(1 / 60);
  assert('粒子数不超过上限', w.particles.length <= 50, `${w.particles.length}`);
}

// 8. 停止发射后已有水流继续运动
{
  const w = make({ velocityX: 100, velocityY: 0, groundY: 100000, flowTTL: 2, emissionRate: 100, enable: true });
  w.update(1 / 60); w.update(1 / 60);
  const n = w.particles.length;
  const yBefore = w.particles[0].y;
  w.setParam('enable', false);
  for (let i = 0; i < 30; i++) w.update(1 / 60);
  assert('停发后粒子未新增', w.particles.length <= n, `n=${n} now=${w.particles.length}`);
  const moved = w.particles.some((p) => p.y > yBefore + 1);
  assert('已有粒子继续下落', moved);
}

console.log(`\n结果：${pass} 通过 / ${fail} 失败`);
process.exit(fail === 0 ? 0 : 1);