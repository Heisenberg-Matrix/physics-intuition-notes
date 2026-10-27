/**
 * math.ts — 纯数学计算模块。
 *
 * 职责:本模块只负责「算数字」,不包含任何 DOM / SVG 代码。
 * 所有供 UnitCircle 渲染的几何数值(圆周点、投影线段)都由这里推导,
 * 使整个 demo 由同一套数学状态驱动。
 */

/** 单角变换的正负号:θ′= sign·θ + k·π。 */
export type Sign = 1 | -1;

/** 屏幕坐标下的一个点。SVG 原点在圆心, y 轴向下,故数学 y 需取负。 */
export interface Vec2 {
  x: number;
  y: number;
}

/** 一段线段(用于 sin 投影:垂直从圆周点到 x 轴)。 */
export interface Segment {
  x: number;
  y0: number;
  y1: number;
}

export function toRadians(deg: number): number {
  return (deg * Math.PI) / 180;
}

export function toDegrees(rad: number): number {
  return (rad * 180) / Math.PI;
}

/** 规范化角度到 [0, 2π)。 */
export function normalizeAngle(rad: number): number {
  const twoPi = 2 * Math.PI;
  return ((rad % twoPi) + twoPi) % twoPi;
}

/**
 * 单位圆 (半径缩放为 radius) 上角度 angleRad 对应的屏幕坐标。
 * 数学上逆时针为正;屏幕 y 向下,故 y = -radius·sinθ。
 */
export function pointOnUnitCircle(angleRad: number, radius: number): Vec2 {
  return { x: radius * Math.cos(angleRad), y: -radius * Math.sin(angleRad) };
}

/** 单角变换: θ′= sign·θ + k·π。 */
export function transformAngle(theta: number, sign: Sign, k: number): number {
  return sign * theta + k * Math.PI;
}

/** θ′ 的 sin 值。 */
export function sinOfTransform(theta: number, sign: Sign, k: number): number {
  return Math.sin(transformAngle(theta, sign, k));
}

/**
 * 由圆周点上命中的角度(它位于 θ′)反解原始角 θ。
 * 由 θ′= sign·θ + k·π ⇒ θ = sign·(θ′ − k·π)。
 * 拖动交互用:用户拖到哪个角,就反算 θ。
 */
export function thetaFromTransformed(thetaPrime: number, sign: Sign, k: number): number {
  return sign * (thetaPrime - k * Math.PI);
}

/** 屏幕坐标偏移 (dx,dy) 命中点的圆周角度(0 在 +x 轴,逆时针为正)。 */
export function angleFromDrag(dx: number, dy: number): number {
  return Math.atan2(-dy, dx);
}

/**
 * 由当前状态推导出 UnitCircle 需要的完整几何数据。
 * 纯数学: 分离计算与渲染, 渲染层只负责「摆放」。
 */
export interface RenderModel {
  radius: number;
  /** 变换后 θ′ 对应圆周点。 */
  active: Vec2;
  /** sin 投影: 从 active 点垂直引到 x 轴 (y=0)。 */
  activeProj: Segment;
  /** 原角 θ 的圆周点(原角参照)。 */
  ref: Vec2;
  /** 原角的 sin 投影。 */
  refProj: Segment;
}

export function buildRenderModel(theta: number, sign: Sign, k: number, radius: number): RenderModel {
  const thetaPrime = transformAngle(theta, sign, k);
  const active = pointOnUnitCircle(thetaPrime, radius);
  const ref = pointOnUnitCircle(theta, radius);

  return {
    radius,
    active,
    activeProj: { x: active.x, y0: active.y, y1: 0 },
    ref,
    refProj: { x: ref.x, y0: ref.y, y1: 0 },
  };
}