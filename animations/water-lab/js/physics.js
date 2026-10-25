/**
 * physics.js — 纯物理模块（不含任何 DOM / Canvas 依赖，可独立测试）。
 *
 * 坐标系：屏幕坐标，Y 轴向下为正。单位：逻辑像素（lp）、逻辑像素/秒（lp/s）、lp/s²。
 *
 * 负责：
 *  - 粒子状态（位置/速度/半径/生命周期）
 *  - 固定时间步长的积分 + 动量子步（防高速粒子穿透地面）
 *  - 持续发射与停止发射
 *  - 地面碰撞 + 水花（液体融合主体 + 独立飞溅水滴）
 *  - 粒子数量上限与生命周期回收
 *
 * 渲染完全交给 render.js。
 */

export const TAU = Math.PI * 2;

/** 生成 [min, max) 均匀随机数。 */
function rand(min, max) {
  return min + Math.random() * (max - min);
}

/** 物理世界：持有全部参数、粒子列表，驱动所有更新。 */
export class World {
  constructor(params = {}) {
    /** 全部可调参数。 */
    this.params = Object.assign(
      {
        // —— 发射器 ——
        startX: 200,        // 发射点 X (lp)
        startY: 80,         // 发射点 Y (lp)
        velocityX: 140,     // 水平初速 (lp/s)
        velocityY: -30,     // 竖直初速 (lp/s)，负值向上
        emissionRate: 250,  // 每秒发射粒子数（更密 → 水流更细腻）
        jitter: 20,         // 初速度随机扰动幅度 (lp/s)
        // —— 物理 ——
        gravity: 620,       // 重力加速度 (lp/s²)
        particleRadius: 5.5, // 水粒子基础半径 (lp)
        groundY: 520,       // 地面碰撞线 y (lp)
        // —— 生命周期 / 上限 ——
        flowTTL: 4,         // 水流粒子最大寿命 (s)，与上限共同约束数量
        maxParticles: 2600,
        // —— 其它 ——
        enable: true,       // 是否持续发射
      },
      params
    );

    /** @type {{x:number,y:number,vx:number,vy:number,r:number,age:number,ttl:number,kind:'flow'|'body'|'drop'}[]} */
    this.particles = [];

    /** 相对时间戳。 */
    this.time = 0;

    // 发射累计器：累计 dt，满 1/rate 才产出一个粒子，保证不同帧率下发射节奏稳定。
    this._emitAcc = 0;
  }

  /** 修改单个参数。 */
  setParam(key, value) {
    this.params[key] = value;
  }

  /** 批量修改参数。 */
  setParams(patch) {
    Object.assign(this.params, patch);
  }

  /**
   * 推进一个时间步 dt（秒）。内部按位移把大 dt 拆成小子步，避免高速粒子穿过地面。
   */
  update(dt) {
    const theTime = this.time + dt;
    this.time = theTime;

    // —— 发射 ——
    if (this.params.enable) {
      this._emitAcc += dt * this.params.emissionRate;
      while (this._emitAcc >= 1) {
        this._emitOne();
        this._emitAcc -= 1;
      }
    } else {
      this._emitAcc = 0;
    }

    // —— 定步长子步数：按单步最大竖直位移控制，约等于半径量级 ——
    const s = this.params;
    const peakVy = Math.abs(s.velocityY) + s.gravity * dt;
    const stepDist = peakVy * dt; // 一帧内最大可能位移
    const substeps = Math.min(6, Math.max(1, Math.ceil(stepDist / Math.max(1, s.particleRadius))));
    const h = dt / substeps;

    for (let k = 0; k < substeps; k++) {
      this._integrateSubstep(h);
    }

    // —— 回收死粒子 ——
    const alive = [];
    const pList = this.particles;
    for (let i = 0; i < pList.length; i++) {
      const p = pList[i];
      if (p.age < p.ttl && p.y - p.r < s.groundY + 2 && Number.isFinite(p.x) && Number.isFinite(p.y)) {
        alive.push(p);
      }
    }
    this.particles = alive;

    // —— 数量上限：超限裁掉最老的 ——
    if (this.particles.length > s.maxParticles) {
      this.particles.splice(0, this.particles.length - s.maxParticles);
    }
  }

  /** 单个子步：半隐式欧拉积分 + 地面撞击处理。 */
  _integrateSubstep(h) {
    const s = this.params;
    const list = this.particles;

    for (let i = 0; i < list.length; i++) {
      const p = list[i];
      p.vy += s.gravity * h;      // 先更新速度（semi-implicit Euler）
      p.x += p.vx * h;
      p.y += p.vy * h;
      p.age += h;
    }

    // 地面撞击（倒序遍历，用末尾 swap 删除）。
    // 各类粒子的地上行为刻意区分，避免「主干 → 水花 → 再落地 → 再产水花」的失控级联：
    //  - flow ：主干撞击，钳回地面并产出水花，然后移除；
    //  - body ：贴地静止并横向摩擦抹平，靠 ttl 淡出消散（形成短暂横向扩散的水坨）；
    //  - drop ：独立水珠触地即消失。
    for (let i = list.length - 1; i >= 0; i--) {
      const p = list[i];
      if (p.y + p.r >= s.groundY) {
        if (p.kind === 'flow') {
          p.y = s.groundY - p.r;
          this._spawnImpact(p);
          list[i] = list[list.length - 1];
          list.pop();
        } else if (p.kind === 'drop') {
          list[i] = list[list.length - 1];
          list.pop();
        } else {
          // body：停在路面并横向抹平，随 ttl 淡出，不再产生新水花。
          p.y = s.groundY - p.r;
          p.vy = 0;
          p.vx *= 0.99;
        }
      }
    }
  }

  /**
   * 单个粒子撞击地面：原粒子消失，产生水花。
   * 水花 = 融合液体主体（贴地横铺、加入主体） + 少量独立飞溅水珠。
   * 强度随撞击速度增大而增大。
   */
  _spawnImpact(p) {
    const s = this.params;
    const impact = Math.hypot(p.vx, p.vy);

    // 归一化强度（略经验化，0~1）。
    const norm = Math.min(1, impact / (s.gravity * 0.6));

    // 1) 融合液体主体：贴地的微平铺水坨，汇入 metaball 主体形成横向扩散，
    //    中心贴合地面（y - r = groundY），只轻微上浮、随即自然消失。
    const bodyCount = 1 + Math.min(3, Math.round(norm * 2.2));
    for (let i = 0; i < bodyCount; i++) {
      const r2 = p.r * rand(0.8, 1.3);
      this.particles.push({
        x: p.x + rand(-1, 1) * p.r * 2,
        y: s.groundY - r2,
        vx: rand(-1, 1) * (70 + 200 * norm),
        vy: -Math.abs(rand(0, 50 * norm)),
        r: r2,
        age: 0,
        ttl: rand(0.25, 0.5),
        kind: 'body',
      });
    }

    // 2) 独立飞溅水珠：向上、向两侧，受重力，刻意少量、强度受撞击速度调控。
    const dropCount = 2 + Math.min(5, Math.round(norm * 3));
    for (let i = 0; i < dropCount; i++) {
      const dir = Math.random() < 0.5 ? -1 : 1;
      const r2 = p.r * rand(0.35, 0.8);
      this.particles.push({
        x: p.x + dir * rand(0, p.r * 2),
        y: s.groundY - r2,
        vx: dir * rand(40, 90) * (0.5 + norm),
        vy: -Math.abs(rand(50, 220) * (0.4 + norm)),
        r: r2,
        age: 0,
        ttl: rand(0.4, 0.85),
        kind: 'drop',
      });
    }
  }

  /** 持续发射：产出一个水流粒子。 */
  _emitOne() {
    const s = this.params;
    const j = s.jitter;
    this.particles.push({
      x: s.startX + rand(-2, 2),
      y: s.startY + rand(-2, 2),
      vx: s.velocityX + rand(-j, j),
      vy: s.velocityY + rand(-j, j),
      r: s.particleRadius * rand(0.9, 1.1),
      age: 0,
      ttl: s.flowTTL * rand(0.6, 1.0),
      kind: 'flow',
    });
  }

  /** 清空所有粒子（用于重置）。 */
  clear() {
    this.particles.length = 0;
    this._emitAcc = 0;
  }
}