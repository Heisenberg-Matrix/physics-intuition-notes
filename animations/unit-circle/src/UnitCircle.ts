/**
 * UnitCircle.ts — SVG 绘制与更新 + 交互(悬停 / 拖动 / 键盘)。
 *
 * 三层职责,分别落位:
 *  - 数学: 由 main.ts 调 math.ts 算出 P / OP / sin 线段坐标, 此处只「摆放」;
 *  - 绘制: 圆、坐标轴、活动点、半径、sin 投影三件套的静态结构;
 *  - 交互: 三个对象独立响应悬停, 圆周点可拖动(命中区放大), 键盘调角。
 * 悬停只改视觉状态, 不改变数学; 拖动期间点保持高亮, 结束后恢复。
 */

import { normalizeAngle, toDegrees, type RenderModel, type Vec2 } from './math';

const SVG_NS = 'http://www.w3.org/2000/svg';

/** 单位圆半径(像素)。与 math.ts 画同一圆,两者共用常量。 */
export const RADIUS = 270;

/** 渲染开关:坐标系显隐、原角参照显隐。 */
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

function create<K extends keyof SVGElementTagNameMap>(
  tag: K,
  attrs: Record<string, string | number>,
): SVGElementTagNameMap[K] {
  const el = document.createElementNS(SVG_NS, tag) as SVGElementTagNameMap[K];
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

const HOT = 'hot'; // 悬停或拖动中

export class UnitCircle {
  private readonly svg: SVGSVGElement;

  private readonly axisG: SVGGElement;
  private readonly refG: SVGGElement;
  private readonly activeG: SVGGElement;

  // 可见对象
  private readonly activeRay: SVGLineElement;
  private readonly activeProj: SVGLineElement;
  private readonly rightMark: SVGPolylineElement;
  private readonly activePoint: SVGCircleElement;

  // 命中区(不可见, 放大以降低精确点按压力)
  private readonly hitPoint: SVGCircleElement;
  private readonly hitRay: SVGLineElement;
  private readonly hitProj: SVGLineElement;

  private readonly refRay: SVGLineElement;
  private readonly refProj: SVGLineElement;
  private readonly refPoint: SVGCircleElement;

  /** 是否正在拖动圆周点。拖动期间点保持高亮、线段悬停忽略。 */
  private dragging = false;

  constructor(svg: SVGSVGElement, private readonly handlers: UnitCircleHandlers) {
    this.svg = svg;

    // ——— 图层: 坐标轴(可整体显隐) → 原角参照 → 活动层 ———
    this.axisG = create('g', { class: 'axis', 'aria-hidden': 'true' });
    this.buildAxes(this.axisG);

    this.refG = create('g', { class: 'ref' });
    this.refRay = create('line', { class: 'ref-ray' });
    this.refProj = create('line', { class: 'ref-proj' });
    this.refPoint = create('circle', { class: 'ref-point' });
    this.refG.append(this.refRay, this.refProj, this.refPoint);

    // 活动层: ① 透明宽命中线(悬停) → ② 可见半径/投影 → ③ 圆点(最上层)
    this.activeG = create('g', { class: 'active' });
    this.hitRay = create('line', { class: 'hit-line hit-ray' });
    this.hitProj = create('line', { class: 'hit-line hit-proj' });
    this.activeRay = create('line', { class: 'active-ray' });
    this.activeProj = create('line', { class: 'sin-proj' });
    this.rightMark = create('polyline', { class: 'right-mark' });

    this.activePoint = create('circle', {
      class: 'active-point',
      r: '6', // 兜底半径; 悬停由 CSS 的 r 属性放大
      tabindex: '0',
      role: 'slider',
      'aria-label': '圆周点 P, 可用方向键或鼠标拖动调整角度',
      'aria-valuemin': 0,
      'aria-valuemax': 360,
    });
    this.hitPoint = create('circle', { class: 'hit-point', r: '26' });

    this.activeG.append(
      this.hitRay,
      this.hitProj,
      this.activeRay,
      this.activeProj,
      this.rightMark,
      this.activePoint,
      this.hitPoint,
    );

    const circle = create('circle', { class: 'circle', r: RADIUS });
    svg.append(circle, this.axisG, this.refG, this.activeG);

    this.setUpHover();
    this.attachDrag();
    this.attachKeyboard();
  }

  /* ————————————————— 渲染 ————————————————— */

  /** 更新三件套与参照的几何位置; 不触发热状态。 */
  render(model: RenderModel, view: ViewOptions): void {
    const a = model.active;
    this.activeRay.setAttribute('x2', String(a.x));
    this.activeRay.setAttribute('y2', String(a.y));
    this.activeProj.setAttribute('x1', String(a.x));
    this.activeProj.setAttribute('y1', String(a.y));
    this.activeProj.setAttribute('x2', String(a.x));
    this.activeProj.setAttribute('y2', '0');
    this.rightMark.setAttribute('points', this.rightMarkPoints(a.x, a.y));

    this.hitRay.setAttribute('x2', String(a.x));
    this.hitRay.setAttribute('y2', String(a.y));
    this.hitProj.setAttribute('x1', String(a.x));
    this.hitProj.setAttribute('y1', String(a.y));
    this.hitProj.setAttribute('x2', String(a.x));
    this.hitProj.setAttribute('y2', '0');

    this.setCircle(this.activePoint, a);
    this.setCircle(this.hitPoint, a);

    const ang = normalizeAngle(Math.atan2(-a.y, a.x));
    this.activePoint.setAttribute('aria-valuenow', String(Math.round(toDegrees(ang))));

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

  private setCircle(el: SVGCircleElement, p: Vec2): void {
    el.setAttribute('cx', String(p.x));
    el.setAttribute('cy', String(p.y));
  }

  /* ————————————————— 交互 ————————————————— */

  /**
   * 悬停绑定: 三个对象各自独立响应 pointerenter / pointerleave, 只切视觉状态 .hot。
   * 拖动期间线段不响应(避免烦人闪烁); 圆周点通过命中区高亮, 拖动期间保持。
   */
  private setUpHover(): void {
    // 半径与 sin 投影: 命中区(透明宽线)收 hover, 转发 .hot 到可见线段。
    this.wireHover(this.hitRay, this.activeRay);
    this.wireHover(this.hitProj, this.activeProj);

    // 圆周点: 命中区大圆负责悬停与拖动的视觉高亮。
    this.hitPoint.addEventListener('pointerenter', () => this.activePoint.classList.add(HOT));
    this.hitPoint.addEventListener('pointerleave', () => {
      if (!this.dragging) this.activePoint.classList.remove(HOT);
    });
  }

  /** 命中区收 hover, 把 .hot 转发到对应可见元素; 拖动期间忽略。 */
  private wireHover(hit: SVGElement, target: SVGElement): void {
    hit.addEventListener('pointerenter', () => {
      if (!this.dragging) target.classList.add(HOT);
    });
    hit.addEventListener('pointerleave', () => {
      if (!this.dragging) target.classList.remove(HOT);
    });
  }

  private attachDrag(): void {
    let activePointerId = -1;

    const start = (e: PointerEvent) => {
      e.preventDefault();
      this.dragging = true;
      this.svg.classList.add('dragging');
      this.activePoint.classList.add(HOT);
      this.svg.setPointerCapture(e.pointerId);
      activePointerId = e.pointerId;
      this.moveTo(e);
    };
    const move = (e: PointerEvent) => {
      if (!this.dragging || e.pointerId !== activePointerId) return;
      this.moveTo(e);
    };
    const end = () => {
      if (!this.dragging) return;
      this.dragging = false;
      this.svg.classList.remove('dragging');
      this.activePoint.classList.remove(HOT);
    };

    this.hitPoint.addEventListener('pointerdown', start);
    this.svg.addEventListener('pointermove', move);
    this.svg.addEventListener('pointerup', end);
    this.svg.addEventListener('pointercancel', end);
    this.svg.addEventListener('lostpointercapture', end);
  }

  /** 把当前指针位置投影为圆周角(连续, 不吸附整度)。 */
  private moveTo(e: PointerEvent): void {
    const p = toViewBox(e, this.svg);
    if (!p) return;
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

  private rightMarkPoints(px: number, py: number): string {
    const s = 12;
    const v = py > 0 ? s : -s;
    const h = px > 0 ? -s : s;
    return `${px} 0 ${px} ${v} ${px + h} ${v}`;
  }
}

function toViewBox(e: PointerEvent, svg: SVGSVGElement): Vec2 | null {
  const pt = svg.createSVGPoint();
  pt.x = e.clientX;
  pt.y = e.clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return null;
  const p = pt.matrixTransform(ctm.inverse());
  return { x: p.x, y: p.y };
}