/**
 * UnitCircle.ts — SVG 绘制与更新。
 *
 * 职责:构建画布的一次性静态结构(坐标轴、圆、辅助层、投影、圆周点),
 * 并通过 render() 把 math.ts 计算好的几何数据「摆放」到位。
 * 本模块不参与公式计算, 只接收数值并更新属性。
 */

import { type RenderModel, type Vec2 } from './math';

const SVG_NS = 'http://www.w3.org/2000/svg';

/** 单位圆半径(像素)。与 math.ts 画同一圆,两者共用常量。 */
export const RADIUS = 270;

/** 渲染开关:坐标系显隐、原角参照显隐。 */
export interface ViewOptions {
  showAxes: boolean;
  showReference: boolean;
}

/** 拖动画布上的圆周点时, 把命中角度(θ′)回调给外部。 */
export interface UnitCircleHandlers {
  onAngleDragged(thetaPrimeRad: number): void;
}

function create<K extends keyof SVGElementTagNameMap>(
  tag: K,
  attrs: Record<string, string | number>,
): SVGElementTagNameMap[K] {
  const el = document.createElementNS(SVG_NS, tag) as SVGElementTagNameMap[K];
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

export class UnitCircle {
  private readonly axisG: SVGGElement;
  private readonly refG: SVGGElement;
  private readonly activeG: SVGGElement;

  private readonly activeRay: SVGLineElement;
  private readonly activeProj: SVGLineElement;
  private readonly rightMark: SVGPolylineElement;
  private readonly activePoint: SVGCircleElement;
  private readonly hitPoint: SVGCircleElement;

  private readonly refRay: SVGLineElement;
  private readonly refProj: SVGLineElement;
  private readonly refPoint: SVGCircleElement;

  constructor(private readonly svg: SVGSVGElement, private readonly handlers: UnitCircleHandlers) {
    // ——— 图层: 坐标轴(可整体显隐) → 原角参照 → 活动层(圆点/投影,可整层显隐) ———
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
    this.rightMark = create('polyline', { class: 'right-mark' });
    this.activePoint = create('circle', { class: 'active-point', tabindex: '0' });
    // 命中区: 一个更大的透明圆, 方便抓取。
    this.hitPoint = create('circle', { class: 'hit-point' });
    this.activeG.append(
      this.activeRay,
      this.activeProj,
      this.rightMark,
      this.activePoint,
      this.hitPoint,
    );

    // 单位圆在最底层、投影与点在上方。
    const circle = create('circle', { class: 'circle' });
    svg.append(circle, this.axisG, this.refG, this.activeG);

    this.attachDrag();
  }

  /** 坐标轴 + 单位刻度 ±1(以及轴端字母 x/y)。 */
  private buildAxes(axisG: SVGGElement): void {
    const R = RADIUS;
    const span = R + 40;
    axisG.append(
      create('line', { class: 'axis-line', x1: -span, y1: 0, x2: span, y2: 0 }),
      create('line', { class: 'axis-line', x1: 0, y1: -span, x2: 0, y2: span }),
    );

    // x 轴上 ±1 处: 短竖刻度 + 下方标签。
    const makeXTick = (x: number, label: string) => {
      axisG.append(
        create('line', { class: 'grid-tick', x1: x, y1: -6, x2: x, y2: 6 }),
      );
      const t = create('text', { class: 'axis-label', x: x, y: 26, 'text-anchor': 'middle' });
      t.textContent = label;
      axisG.append(t);
    };
    makeXTick(R, '1');
    makeXTick(-R, '−1');

    // y 轴上 ±1 处: 短横刻度 + 侧方标签。
    const makeYLabel = (y: number, label: string, anchor: string, dx: number) => {
      axisG.append(create('line', { class: 'grid-tick', x1: -6, y1: y, x2: 6, y2: y }));
      const t = create('text', {
        class: 'axis-label',
        x: dx,
        y: y - 8,
        'text-anchor': anchor,
      });
      t.textContent = label;
      axisG.append(t);
    };
    makeYLabel(-R, '1', 'end', -12);
    makeYLabel(R, '−1', 'start', 12);

    // 端点字母
    const xLabel = create('text', { class: 'axis-name', x: span - 8, y: -10, 'text-anchor': 'end' });
    xLabel.textContent = 'x';
    const yLabel = create('text', { class: 'axis-name', x: 16, y: -span + 14, 'text-anchor': 'start' });
    yLabel.textContent = 'y';
    axisG.append(xLabel, yLabel);
  }

  /** 更新所有几何位置。 */
  render(model: RenderModel, view: ViewOptions): void {
    const a = model.active;
    this.activeRay.setAttribute('x2', String(a.x));
    this.activeRay.setAttribute('y2', String(a.y));
    this.activeProj.setAttribute('x1', String(a.x));
    this.activeProj.setAttribute('y1', String(a.y));
    this.activeProj.setAttribute('x2', String(a.x));
    this.activeProj.setAttribute('y2', '0');
    this.rightMark.setAttribute('points', this.rightMarkPoints(a.x));
    this.activePoint.setAttribute('cx', String(a.x));
    this.activePoint.setAttribute('cy', String(a.y));
    this.hitPoint.setAttribute('cx', String(a.x));
    this.hitPoint.setAttribute('cy', String(a.y));

    const r = model.ref;
    this.refRay.setAttribute('x2', String(r.x));
    this.refRay.setAttribute('y2', String(r.y));
    this.refProj.setAttribute('x1', String(r.x));
    this.refProj.setAttribute('y1', String(r.y));
    this.refProj.setAttribute('x2', String(r.x));
    this.refProj.setAttribute('y2', '0');
    this.refPoint.setAttribute('cx', String(r.x));
    this.refPoint.setAttribute('cy', String(r.y));

    this.axisG.style.display = view.showAxes ? '' : 'none';
    this.refG.style.display = view.showReference ? '' : 'none';
  }

  /** 直角标记: 在投影落点 (px, 0) 处画一个小方角。 */
  private rightMarkPoints(px: number): string {
    const s = 12; // 边长
    const dir = px >= 0 ? -1 : 1; // 朝向圆心(向原点)开口
    const x0 = px + dir * s;
    return `${px} 0 ${x0} 0 ${x0} ${s}`;
  }

  private attachDrag(): void {
    let dragging = false;

    this.hitPoint.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      dragging = true;
      this.svg.classList.add('dragging');
      this.svg.setPointerCapture(e.pointerId);
      this.moveTo(e);
    });
    this.svg.addEventListener('pointermove', (e) => {
      if (dragging) this.moveTo(e);
    });
    const end = () => {
      dragging = false;
      this.svg.classList.remove('dragging');
    };
    this.svg.addEventListener('pointerup', end);
    this.svg.addEventListener('pointercancel', end);
    this.svg.addEventListener('lostpointercapture', end);
  }

  /** 指针事件 → 命中角度(θ′), 原点在 viewBox (0,0)。 */
  private moveTo(e: PointerEvent): void {
    const p = toViewBoxInline(e, this.svg);
    if (!p) return;
    const angle = Math.atan2(-p.y, p.x);
    this.handlers.onAngleDragged(angle);
  }
}

function toViewBoxInline(e: PointerEvent, svg: SVGSVGElement): Vec2 | null {
  const pt = svg.createSVGPoint();
  pt.x = e.clientX;
  pt.y = e.clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return null;
  const p = pt.matrixTransform(ctm.inverse());
  return { x: p.x, y: p.y };
}