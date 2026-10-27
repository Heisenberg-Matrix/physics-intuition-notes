/**
 * main.ts — 状态持有与各模块接线。
 *
 * 职责:维护唯一状态 {θ, sign, k, 显隐开关}; 接收 controls 的输入,
 * 用 math 计算几何, 交给 UnitCircle 渲染, 并刷新公式/数值读数。
 */

import { RADIUS, UnitCircle } from './UnitCircle';
import { setupControls } from './controls';
import {
  buildRenderModel,
  sinOfTransform,
  thetaFromTransformed,
  toDegrees,
  toRadians,
  transformAngle,
  type Sign,
} from './math';

interface State {
  thetaDeg: number;
  sign: Sign;
  k: number;
  showAxes: boolean;
  showReference: boolean;
}

const svg = document.getElementById('circle') as unknown as SVGSVGElement;
const formulaEl = document.getElementById('formula') as HTMLParagraphElement;
const valuesEl = document.getElementById('values') as HTMLParagraphElement;
const controlsRoot = document.getElementById('controls') as HTMLElement;

const state: State = {
  thetaDeg: 30,
  sign: 1,
  k: 0,
  showAxes: true,
  showReference: true,
};

/** 把任意度数规范化到 [0, 360)。 */
function normalizeDeg(deg: number): number {
  return ((deg % 360) + 360) % 360;
}

/** 由当前状态计算几何并渲染。 */
function render(): void {
  const model = buildRenderModel(toRadians(state.thetaDeg), state.sign, state.k, RADIUS);
  unitCircle.render(model, {
    showAxes: state.showAxes,
    showReference: state.showReference,
  });
  updateReadout();
}

/** 刷新公式与数值读数。 */
function updateReadout(): void {
  const thetaRad = toRadians(state.thetaDeg);
  const thetaPrimeDeg = normalizeDeg(toDegrees(transformAngle(thetaRad, state.sign, state.k)));
  const sinVal = sinOfTransform(thetaRad, state.sign, state.k);

  const signStr = state.sign === 1 ? '+' : '−';
  const kTerm =
    state.k === 0 ? '' : state.k === 1 ? 'π' : state.k === -1 ? '−π' : `${state.k}π`;

  formulaEl.textContent = `sin θ′ = sin( ${signStr}θ + ${kTerm} )`;

  valuesEl.textContent =
    `θ = ${state.thetaDeg}°,  ` +
    `sign = ${signStr}1,  k = ${state.k}  ` +
    `→ θ′ = ${thetaPrimeDeg}°,  sin θ′ = ${sinVal.toFixed(3)}`;
}

/** 由圆弧拖动命中的 θ′ 反解 θ, 更新状态与画布。 */
function applyDrag(thetaPrimeRad: number): void {
  state.thetaDeg = normalizeDeg(toDegrees(thetaFromTransformed(thetaPrimeRad, state.sign, state.k)));
  controls.setThetaValue(state.thetaDeg);
  render();
}

/**
 * 组装。
 * 注意 applyDrag 使用与 render 同一份状态; 变量声明顺序保证 render 时 unitCircle/controls 已就绪。
 */
const unitCircle = new UnitCircle(svg, {
  onAngleDragged: applyDrag,
});

const controls = setupControls(controlsRoot, {
  onThetaChange: (deg) => {
    state.thetaDeg = deg;
    render();
  },
  onSignChange: (sign) => {
    state.sign = sign;
    render();
  },
  onKChange: (k) => {
    state.k = k;
    render();
  },
  onShowAxesChange: (show) => {
    state.showAxes = show;
    render();
  },
  onShowReferenceChange: (show) => {
    state.showReference = show;
    render();
  },
});

render();