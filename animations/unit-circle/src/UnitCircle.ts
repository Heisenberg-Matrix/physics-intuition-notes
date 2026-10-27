/**
 * UnitCircle.ts — SVG 绘制与更新 + 交互。
 *
 * 三层职责, 分别落位:
 *  - 数学: 由 main.ts 调 math.ts 算出 P / OP / sin 线段坐标, 此处只「摆放」;
 *  - 绘制: 圆、坐标轴、活动点、半径、sin 投影三件套的静态结构;
 *  - 交互: 同一时刻只高亮一个对象, 命中优先级「点 > 半径 > 圆内(sin)」,
 *          圆周点可拖动; 不改鼠标光标。
 *
 * 悬停只改视觉状态, 不改变数学; 拖动期间点保持高亮, 结束后恢复。
 */

import { normalizeAngle, toDegrees, type RenderModel, type Vec2 } from './math';

const SVG_NS = 'http://www.w3.org/2000/svg';

/** 单位圆半径(像素)。与 math.ts 画同一圆, 两者共用常量。 */
export const RADIUS = 270;

/** 渲染开关: 坐标系显隐、原角参照显隐。 */
export interface ViewOptions {
  showAxes: boolean;
  showReference: boolean;
}

/** 交互回调: 拖到某个角(θ′)与键盘逐步调角。 */
export interface UnitCircleHandlers {
  /** 圆周点拖到 angleRad(内部连续, 不做整度吸附)。 */
  onAngleDragged(angleRad: number): void;
  /** 键盘/无障碍逐步调整角度(度为单位)。 */
  onAngularStep(deltaDeg: number): void;
}

/** 三个可高亮对象。 */
type HitTarget = 'point' | 'radius' | 'sin';

const HOT = 'hot'; // 当前高亮的对象
const POINT_PROX = 34; // 距圆周点多近算「指到点」(命中判定宽于可见圆点)
const RAY_PROX = 18; // 距半径线段多近算「指到半径」

function create<K extends keyof SVGElementTagNameMap>(
  tag: K,
  attrs: Record<string, string | number>,
): SVGElementTagNameMap[K] {
  const el = document.createElementNS(SVG_NS, tag) as SVGElementTagNameMap[K];
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

export class UnitCircle {
  private readonly svg: SVGSVGElement;

  private readonly axisG: SVGGElement;
  private readonly refG: SVGGElement;
  private readonly activeG: SVGGElement;

  private readonly activeRay: SVGLineElement;
  private readonly activeProj: SVGLineElement;
  private readonly sinShadow: SVGLineElement;
  private readonly sinSign: SVGTextElement;
  private readonly activePoint: SVGCircleElement;

  private readonly refRay: SVGLineElement;
  private readonly refProj: SVGLineElement;
  private readonly refPoint: SVGCircleElement;

  /** 当前活动点 P 的坐标(SVG 原点为圆心)。悬停距离判定会用。 */
  private curP: Vec2 = { x: RADIUS, y: 0 };
  /** 当前高亮的对象; 全局只有一个。 */
  private active: HitTarget | null = null;
  /** 是否正在拖动圆周点。 */
  private dragging = false;
  /** 上一次渲染的 sin 符号; 变化时触发切换动效。 */
  private lastSign = '';

  constructor(svg: SVGSVGElement, private readonly handlers: UnitCircleHandlers) {
    this.svg = svg;

    // ——— 图层: 坐标轴 → 原角参照 → 活动层 ———
    this.axisG = create('g', { class: 'axis', 'aria-hidden': 'true' });
    this.buildAxes(this.axisG);

    this.refG = create('g', { class: 'ref' });
    this.refRay = create('line', { class: 'ref-ray' });
    this.refProj = create('line', { class: 'ref-proj' });
    this.refPoint = create('circle', { class: 'ref-point' });
    this.refG.append(this.refRay, this.refProj, this.refPoint);

    this.activeG = create('g', { class: 'active' });
    this.activeRay = create('line', { class: 'active-ray' });
    this.activeProj = create('line', { class: 'sin-proj' });
    // sin 影子投影: 从 P 水平投到 y 轴(淡化虚线), 表征 sin 值的高度。
    this.sinShadow = create('line', { class: 'sin-shadow' });
    // sin 正负符号: 跟随投影移动, 与投影同高亮。
    this.sinSign = create('text', {
      class: 'sin-sign',
      'text-anchor': 'middle',
      'aria-hidden': 'true',
    });
    this.activePoint = create('circle', {
      class: 'active-point',
      r: '6',
      tabindex: '0',
      role: 'slider',
      'aria-label': '圆周点 P, 可用方向键或鼠标拖动调整角度',
      'aria-valuemin': 0,
      'aria-valuemax': 360,
    });
    this.activeG.append(
      this.activeRay,
      this.activeProj,
      this.sinShadow,
      this.sinSign,
      this.activePoint,
    );

    const circle = create('circle', { class: 'circle', r: RADIUS });
    svg.append(circle, this.axisG, this.refG, this.activeG);

    this.attachHover();
    this.attachDrag();
    this.attachKeyboard();
  }

  /* ————————————————— 渲染 ————————————————— */

  /** 更新三件套与参照的几何位置; 不触发热状态。 */
  render(model: RenderModel, view: ViewOptions): void {
    const a = model.active;
    this.curP = a;
    this.activeRay.setAttribute('x2', String(a.x));
    this.activeRay.setAttribute('y2', String(a.y));
    this.activeProj.setAttribute('x1', String(a.x));
    this.activeProj.setAttribute('y1', String(a.y));
    this.activeProj.setAttribute('x2', String(a.x));
    this.activeProj.setAttribute('y2', '0');
    // 影子投影: 从 P 水平投到 y 轴(x=0)
    this.sinShadow.setAttribute('x1', '0');
    this.sinShadow.setAttribute('y1', String(a.y));
    this.sinShadow.setAttribute('x2', String(a.x));
    this.sinShadow.setAttribute('y2', String(a.y));

    this.updateSign(a);

    this.setCircle(this.activePoint, a);
    const ang = normalizeAngle(Math.atan2(-a.y, a.x));
    this.activePoint.setAttribute('aria-valuenow', String(Math.round(toDegrees(ang))));

    // 参照层
    const r = model.ref;
    this.refRay.setAttribute('x2', String(r.x));
    this.refRay.setAttribute('y2', String(r.y));
    this.refProj.setAttribute('x1', String(r.x));
    this.refProj.setAttribute('y1', String(r.y));
    this.refProj.setAttribute('x2', String(r.x));
    this.refProj.setAttribute('y2', '0');
    this.setCircle(this.refPoint, r);

    this.axisG.style.display = view.showAxes ? '' : 'none';
    this.refG.style.display = view.showReference ? '' : 'none';
  }

  private setCircle(el: SVGElement, p: Vec2): void {
    el.setAttribute('cx', String(p.x));
    el.setAttribute('cy', String(p.y));
  }

  /** 更新 sin 正负符号: 位置随投影走, 符号切换时触发滑动动效。 */
  private updateSign(a: Vec2): void {
    const sgn = Math.abs(a.y) < 4 ? '0' : a.y < 0 ? '+' : '−'; // |a.y|<4px ≈ 越过 x 轴瞬间
    // 放在投影线段外侧稍远一点, 贴近线段但避开圆心/点。
    const x = a.x + (a.x >= 0 ? 24 : -24);
    const y = a.y / 2 + 7;
    this.sinSign.setAttribute('x', String(x));
    this.sinSign.setAttribute('y', String(y));
    if (this.sinSign.textContent !== sgn) this.sinSign.textContent = sgn;

    if (sgn !== this.lastSign) {
      this.lastSign = sgn;
      // 重触发滑动动画: 先移除再强制回排, 重新添加。
      this.sinSign.classList.remove('sign-flip');
      void this.sinSign.getBoundingClientRect();
      this.sinSign.classList.add('sign-flip');
    }
  }

  /* ————————————————— 交互 ————————————————— */

  /** 高亮置为且只能是一个 target; 传入不同时清掉旧的再亮新的。 */
  private setHot(target: HitTarget | null): void {
    if (this.active === target) return;
    this.active = target;
    this.toggleHot(this.activePoint, target === 'point');
    this.toggleHot(this.activeRay, target === 'radius');
    const sinOn = target === 'sin';
    this.toggleHot(this.activeProj, sinOn);
    this.toggleHot(this.sinShadow, sinOn);
    this.toggleHot(this.sinSign, sinOn);
  }

  private toggleHot(el: SVGElement, on: boolean): void {
    el.classList.toggle(HOT, on);
  }

  /**
   * 判定指针落在哪个对象上。
   * 优先级: 点 > 半径 > 圆内(sin)。圆外且不在点/半径上 → none。
   */
  private hitAt(p: Vec2): HitTarget | null {
    const dCenter = Math.hypot(p.x, p.y);
    const dPoint = Math.hypot(p.x - this.curP.x, p.y - this.curP.y);
    if (dPoint <= POINT_PROX) return 'point';
    const rayDist = distToSegment(p, { x: 0, y: 0 }, this.curP);
    if (rayDist <= RAY_PROX) return 'radius';
    return dCenter <= RADIUS ? 'sin' : null;
  }

  private attachHover(): void {
    this.svg.addEventListener('pointermove', (e) => {
      if (this.dragging) return;
      const p = toViewBox(e, this.svg);
      if (!p) return;
      this.setHot(this.hitAt(p));
    });
    this.svg.addEventListener('pointerleave', () => this.setHot(null));
  }

  private attachDrag(): void {
    this.svg.addEventListener('pointerdown', (e) => {
      const p = toViewBox(e, this.svg);
      if (!p) return;
      if (this.hitAt(p) === null) return; // 任一对象高亮(圆内/半径/点)即可拖动圆点
      e.preventDefault();
      this.dragging = true;
      this.svg.classList.add('dragging');
      this.setHot('point');
      this.svg.setPointerCapture(e.pointerId);
      this.drag(e);
    });
    this.svg.addEventListener('pointermove', (e) => {
      if (this.dragging) this.drag(e);
    });
    const end = () => {
      if (!this.dragging) return;
      this.dragging = false;
      this.svg.classList.remove('dragging');
      // 抬起后按指针所在位置重新判定高亮
      if (this.lastP) this.setHot(this.hitAt(this.lastP));
      else this.setHot(null);
    };
    this.svg.addEventListener('pointerup', end);
    this.svg.addEventListener('pointercancel', end);
    this.svg.addEventListener('lostpointercapture', end);
  }

  private lastP: Vec2 | null = null;

  private drag(e: PointerEvent): void {
    const p = toViewBox(e, this.svg);
    if (!p) return;
    this.lastP = p;
    this.handlers.onAngleDragged(Math.atan2(-p.y, p.x));
  }

  private attachKeyboard(): void {
    this.activePoint.addEventListener('keydown', (e) => {
      // 方向键步进: 单键 1°, Shift 键 5°。
      const big = e.shiftKey ? 5 : 1;
      switch (e.key) {
        case 'ArrowLeft':
        case 'ArrowDown':
          e.preventDefault();
          this.handlers.onAngularStep(-big);
          break;
        case 'ArrowRight':
        case 'ArrowUp':
          e.preventDefault();
          this.handlers.onAngularStep(big);
          break;
        default:
          break;
      }
    });
  }

  /* ————————————————— 静态结构 / 几何 ————————————————— */

  private buildAxes(axisG: SVGGElement): void {
    const R = RADIUS;
    const span = R + 40;
    axisG.append(
      create('line', { class: 'axis-line', x1: -span, y1: 0, x2: span, y2: 0 }),
      create('line', { class: 'axis-line', x1: 0, y1: -span, x2: 0, y2: span }),
    );

    const makeXTick = (x: number, label: string) => {
      axisG.append(create('line', { class: 'grid-tick', x1: x, y1: -6, x2: x, y2: 6 }));
      const t = create('text', { class: 'axis-label', x: x, y: 26, 'text-anchor': 'middle' });
      t.textContent = label;
      axisG.append(t);
    };
    makeXTick(R, '1');
    makeXTick(-R, '−1');

    const makeYLabel = (y: number, label: string, anchor: string, dx: number) => {
      axisG.append(create('line', { class: 'grid-tick', x1: -6, y1: y, x2: 6, y2: y }));
      const t = create('text', { class: 'axis-label', x: dx, y: y - 8, 'text-anchor': anchor });
      t.textContent = label;
      axisG.append(t);
    };
    makeYLabel(-R, '1', 'end', -12);
    makeYLabel(R, '−1', 'start', 12);

    const xLabel = create('text', { class: 'axis-name', x: span - 8, y: -10, 'text-anchor': 'end' });
    xLabel.textContent = 'x';
    const yLabel = create('text', { class: 'axis-name', x: 16, y: -span + 14, 'text-anchor': 'start' });
    yLabel.textContent = 'y';
    axisG.append(xLabel, yLabel);
  }
}

/** 点 p 到线段 a→b 的最短距离。 */
function distToSegment(p: Vec2, a: Vec2, b: Vec2): number {
  const abx = b.x - a.x;
  const aby = b.y - a.y;
  const lenSq = abx * abx + aby * aby;
  if (lenSq === 0) return Math.hypot(p.x - a.x, p.y - a.y);
  let t = ((p.x - a.x) * abx + (p.y - a.y) * aby) / lenSq;
  t = Math.min(1, Math.max(0, t));
  const cx = a.x + t * abx;
  const cy = a.y + t * aby;
  return Math.hypot(p.x - cx, p.y - cy);
}

/** 指针事件 → viewBox 坐标(SVG 原点即圆心)。 */
function toViewBox(e: PointerEvent, svg: SVGSVGElement): Vec2 | null {
  const pt = svg.createSVGPoint();
  pt.x = e.clientX;
  pt.y = e.clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return null;
  const p = pt.matrixTransform(ctm.inverse());
  return { x: p.x, y: p.y };
}