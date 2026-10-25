# Water Lab — 2D 粒子水流交互实验

复刻《鳄鱼小顽皮爱洗澡》风格的**卡通液体（Metaball 融球）水流** Demo。
纯原生 HTML/JS/Canvas 2D，无第三方依赖，无需后端。

## 运行（必须用 HTTP 服务器，否则 ES Module 会被浏览器拦截）

在项目目录启动一个本地静态服务器，例如：

```bash
# 任选其一
python -m http.server 8123     # 然后访问 http://localhost:8123/
```

或者用 VSCode 的 **Live Server** 插件打开 `index.html`。
（直接双击 `index.html`（file://）无法加载模块。）

## 文件结构

| 文件 | 作用 |
|---|---|
| `index.html` | 页面与参数面板 |
| `js/physics.js` | 纯物理（发射 / 积分 / 地面碰撞与水花 / 生命周期），不碰 DOM，可独立测试 |
| `js/render.js` | Canvas 2D 渲染：离屏缓冲 + 阈值切割的融球（metaball）主体 + 独立水珠 |
| `js/main.js` | 组装：固定时间步长主循环、DPI 适配、面板与拖拽发射点绑定 |
| `tests/physics.test.mjs` | 物理模块单元测试：`node tests/physics.test.mjs` |
| `scripts/verify.mjs` | 无头 Chrome（CDP）集成验证，开发期使用 |
| `SPEC.md` | 原始需求文档 |

## 操作

- 右侧滑块：实时调整 `angle（发射角度）、speed（力度）、startX/Y、velocityX/Y、gravity、emissionRate、particleRadius、groundY`。
  - `angle` / `speed` 与 `velocityX` / `velocityY` **双向同步**：改角度力度会自动换算并刷新 vx/vy，反之亦然。
  - 角度约定：以水平向右为 0°，**向上为正**（60° 即向右上方斜抛）。
- 一键预设：`平抛 0°`（纯水平初速，竖直初速为 0）、`斜抛 60°`（恢复默认斜抛）。
- 拖动画布上的圆圈：直接移动发射点。
- 三个按钮：停止/开启水流、暂停/继续、重置。

> 这是一个自包含的静态 demo，部署时只需原样托管本目录（入口 `index.html`）。