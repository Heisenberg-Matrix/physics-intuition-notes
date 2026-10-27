/**
 * controls.ts — 滑块、开关与参数输入的事件绑定。
 *
 * 职责:一次性构建控制面板 DOM, 把用户输入翻译为回调交给 main。
 * 不负责公式计算; 仅提供 setThetaValue() 让 main 在拖动画布时反同步滑块。
 */

import { type Sign } from './math';

export interface ControlCallbacks {
  onThetaChange(deg: number): void;
  onSignChange(sign: Sign): void;
  onKChange(k: number): void;
  onShowAxesChange(show: boolean): void;
  onShowReferenceChange(show: boolean): void;
  onShowShadowChange(show: boolean): void;
}

export interface Controls {
  /** main 在用户拖动画布时, 用反解出的 θ° 回填滑块。 */
  setThetaValue(deg: number): void;
}

/** 读一个数字输入; 非法值回退到 fallback。 */
function readNum(el: HTMLInputElement, fallback: number): number {
  const v = Number(el.value);
  return Number.isFinite(v) ? v : fallback;
}

/** 一个「label + 控件 + 数值」字段。 */
function field(labelText: string): {
  row: HTMLLabelElement;
  value: HTMLOutputElement;
} {
  const row = document.createElement('label');
  row.className = 'field';
  const label = document.createElement('span');
  label.className = 'field-label';
  label.textContent = labelText;
  const value = document.createElement('output');
  value.className = 'field-value';
  row.append(label, value);
  return { row, value };
}

export function setupControls(root: HTMLElement, cb: ControlCallbacks): Controls {
  // ——— θ 滑块 ———
  const thetaF = field('θ (°)');
  const theta = document.createElement('input');
  theta.type = 'range';
  theta.min = '0';
  theta.max = '360';
  theta.step = '1';
  theta.value = '30';
  const syncTheta = () => {
    thetaF.value.textContent = String(Math.round(readNum(theta, 0)));
    cb.onThetaChange(readNum(theta, 0));
  };
  theta.addEventListener('input', syncTheta);
  thetaF.row.append(theta);

  // ——— sign 切换 ———
  const signF = field('符号 sign');
  const sign = document.createElement('select');
  sign.append(new Option('+1', '1'), new Option('−1', '-1'));
  sign.addEventListener('change', () => cb.onSignChange(Number(sign.value) as Sign));
  signF.row.append(sign);

  // ——— k(整数)——记
  const kF = field('k (整数)');
  const k = document.createElement('input');
  k.type = 'number';
  k.min = '-6';
  k.max = '6';
  k.step = '1';
  k.value = '0';
  const syncK = () => cb.onKChange(Math.round(readNum(k, 0)));
  k.addEventListener('input', syncK);
  kF.row.append(k);

  // ——— 坐标系显隐 ———
  const axesF = field('显示坐标系');
  const axes = document.createElement('input');
  axes.type = 'checkbox';
  axes.checked = true;
  axes.addEventListener('change', () => cb.onShowAxesChange(axes.checked));
  axesF.row.append(axes);

  // ——— 原角参照 ———
  const refF = field('显示原角参照');
  const ref = document.createElement('input');
  ref.type = 'checkbox';
  ref.checked = true;
  ref.addEventListener('change', () => cb.onShowReferenceChange(ref.checked));
  refF.row.append(ref);

  // ——— sin 影子投影(y 轴) ———
  const shadowF = field('y 轴影子投影');
  const shadow = document.createElement('input');
  shadow.type = 'checkbox';
  shadow.checked = true;
  shadow.addEventListener('change', () => cb.onShowShadowChange(shadow.checked));
  shadowF.row.append(shadow);

  root.append(thetaF.row, kF.row, signF.row, axesF.row, refF.row, shadowF.row);

  return {
    setThetaValue(deg: number) {
      theta.value = String(Math.round(deg));
      thetaF.value.textContent = String(Math.round(deg));
    },
  };
}