/**
 * render.js — Canvas 2D 渲染模块。
 *
 * 负责把 World 里的粒子画成「融球（metaball）」质感的水流：
 *  1. 在离屏缓冲上，为每个水粒子画一个软边缘的光斑（径向渐变）。
 *  2. 叠加后会得到连通的高密度区域 → 用阈值映射把密度切成带柔和边缘的液体轮廓。
 *  3. 用一个预设的蓝色查色表（LUT）给不同密度上色，得到清澈的浅蓝色主体。
 *  4. 独立飞溅水珠（kind:'drop'）不参与融合，作为独立小圆点绘制。
 *
 * 物理在此不出现任何逻辑，只读取 World.particles 做绘制。
 */

import { TAU } from './physics.js';

/** 蓝色渐变（浅 → 深）的一维查色表索引 0..255。 */
function buildBlueLUT() {
  const stops = [
    [214, 238, 252], // 极浅蓝（低密度边缘，淡出用）
    [178, 227, 250],
    [120, 200, 243],
    [74, 166, 234],  // 深一点的水体主色
  ];
  const lr = new Uint8ClampedArray(256);
  const lg = new Uint8ClampedArray(256);
  const lb = new Uint8ClampedArray(256);
  const seg = stops.length - 1;
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    const k = Math.min(seg - 1, Math.floor(t * seg));
    const u = (t * seg) - k;
    const a = stops[k];
    const b = stops[k + 1];
    lr[i] = a[0] + (b[0] - a[0]) * u;
    lg[i] = a[1] + (b[1] - a[1]) * u;
    lb[i] = a[2] + (b[2] - a[2]) * u;
  }
  return { lr, lg, lb };
}

/**
 * 创建一个 metaball 渲染器。
 * @param {HTMLCanvasElement} canvas 主画布（全尺寸、负责呈现）。
 * @param {Object} [opts]
 * @returns 渲染器对象。
 */
export function createRenderer(canvas, opts = {}) {
  const o = Object.assign(
    {
      // 离屏缓冲相对「逻辑像素 × DPR」的比例。越高轮廓越细腻，代价是逐像素开销。
      bufferScale: 0.8,
      maxBufferPixels: 1_500_000, // 缓冲总像素上限（大屏自动降压，保帧率）
      glowFactor: 2.3,   // 光斑半径 = 粒子半径 * glowFactor（控制融合柔软度）
      smoothLow: 58,     // 阈值下限（密度低于它视为全透明）
      smoothHigh: 165,   // 阈值上限（密度高于它为纯色中心）
      dropAlpha: 0.9,
    },
    opts
  );

  const ctx = canvas.getContext('2d');
  const buffer = document.createElement('canvas');
  const bctx = buffer.getContext('2d', { willReadFrequently: true });

  const { lr, lg, lb } = buildBlueLUT();

  // 缓冲分辨率：跟随逻辑尺寸 × DPR 提高清晰度，同时限制总像素以保帧率。
  function resize(cssW, cssH) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let scale = o.bufferScale * Math.min(dpr, 1.5);
    const area = Math.max(1, cssW * cssH);
    if (area * scale * scale > o.maxBufferPixels) {
      scale = Math.sqrt(o.maxBufferPixels / area);
    }
    buffer.width = Math.max(1, Math.round(cssW * scale));
    buffer.height = Math.max(1, Math.round(cssH * scale));
    // 记录本帧的缓冲→逻辑像素缩放，Pass1 里按它换算坐标。
    o._scaleX = buffer.width / Math.max(1, cssW);
    o._scaleY = buffer.height / Math.max(1, cssH);
  }

  /**
   * 绘制一帧。
   * @param {import('./physics.js').World} world
   * @param {number} cssW 主画布逻辑宽度
   * @param {number} cssH 主画布逻辑高度
   */
  function draw(world, cssW, cssH) {
    const list = world.particles;

    // ---------- Pass 1：所有水粒子画成软光斑 ----------
    bctx.clearRect(0, 0, buffer.width, buffer.height);
    bctx.globalCompositeOperation = 'lighter';
    bctx.fillStyle = '#ffffff';

    for (let i = 0; i < list.length; i++) {
      const p = list[i];
      if (p.kind === 'drop') continue; // 独立水珠不融入主体
      const bx = p.x * o._scaleX;
      const by = p.y * o._scaleY;
      const br = p.r * ((o._scaleX + o._scaleY) * 0.5) * o.glowFactor;
      // 用径向渐变做软光斑（比实心圆更适合阈值化）。
      const g = bctx.createRadialGradient(bx, by, 0, bx, by, Math.max(0.5, br));
      g.addColorStop(0, 'rgba(255,255,255,0.95)');
      g.addColorStop(0.55, 'rgba(255,255,255,0.5)');
      g.addColorStop(1, 'rgba(255,255,255,0)');
      bctx.fillStyle = g;
      bctx.beginPath();
      bctx.arc(bx, by, Math.max(0.5, br), 0, TAU);
      bctx.fill();
    }
    bctx.globalCompositeOperation = 'source-over';

    // ---- Pass 2：阈值映射（真正的融合切割）→ 输出为蓝白 alpha 掩码 ----
    const img = bctx.getImageData(0, 0, buffer.width, buffer.height);
    const data = img.data;
    const span = o.smoothHigh - o.smoothLow;
    for (let i = 0; i < data.length; i += 4) {
      let a = data[i + 3];
      // 超过下限才可见：0 → smoothHigh 之间做平滑过渡。
      let t = (a - o.smoothLow) / span;
      if (t < 0) t = 0;
      else if (t > 1) t = 1;
      const idx = (t * 255) | 0;
      // 关键：alpha 随密度平滑变化，边缘才能抗锯齿、显得细腻；
      // 若强制成 255，轮廓会变成硬边锯齿（之前的“颗粒粗糙”来源）。
      data[i] = lr[idx];
      data[i + 1] = lg[idx];
      data[i + 2] = lb[idx];
      data[i + 3] = idx;
    }
    bctx.putImageData(img, 0, 0);

    // ---- 把蓝色主体缩放到主画布（高质量平滑） ----
    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(buffer, 0, 0, cssW, cssH);
    ctx.restore();

    // ---- Pass 3：独立飞溅水珠作为半透明小圆点画在上面 ----
    for (let i = 0; i < list.length; i++) {
      const p = list[i];
      if (p.kind !== 'drop') continue;
      const fade = 1 - p.age / p.ttl;
      if (fade <= 0) continue;
      // 独立水珠也给一层柔和边缘，避免小圆点出现硬像素。
      const a = o.dropAlpha * fade;
      const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, Math.max(0.6, p.r));
      g.addColorStop(0, 'rgba(96,180,244,' + a + ')');
      g.addColorStop(0.7, 'rgba(96,180,244,' + (a * 0.9) + ')');
      g.addColorStop(1, 'rgba(96,180,244,0)');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(p.x, p.y, Math.max(0.6, p.r), 0, TAU);
      ctx.fill();
    }
  }

  return { resize, draw, buffer };
}