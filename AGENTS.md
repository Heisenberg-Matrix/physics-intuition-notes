# AGENTS.md — 给在本仓库工作的 AI / 自动化代理

本仓库是「物理直观讲义」项目。`animations/` 用于存放交互实验与动画 demo。
在本仓库新增或修改动画 demo 时，遵循以下约定。**默认由你完成实现、验证、提交与推送，无需逐步询问。**

## 目录约定

- 一个 demo 一个子目录：`animations/<slug>/`，`slug` 用小写连字符（如 `water-lab`、`color-waves`、`pendulum`）。
- 入口文件必须是 `index.html`，保证访问 `/animations/<slug>/` 可直接打开。
- 每个 demo 自成一体、全部使用**相对路径**；不依赖构建步骤，不需要后端。
- 新增 demo 后，必须在 `animations/README.md` 的「实验列表」中补一条链接（一行即可）。
- 多个 demo 共用的代码放 `animations/shared/`，用相对路径引用；**不要复制粘贴同一份实现**。
- 已有参考实现：`animations/water-lab/`（原生 HTML + ES Modules + Canvas 2D，物理与渲染分离，含 Node 测试）。

## 技术约束（默认）

- 原生 HTML / CSS / JavaScript（ES Modules）+ Canvas 2D 或 SVG 即可。
- 不默认引入 Three.js、React、PixiJS、第三方物理引擎；确有必要时，先说明理由与体积代价。
- 纯静态：可直接托管在 GitHub Pages 或任意静态服务器。
- 若含物理模拟：注意高 DPI 适配、窗口 resize、固定时间步长、粒子/对象数量上限与回收，避免内存无限增长。

## 每个 demo 至少包含

- `index.html`
- 源码目录（如 `js/`）
- `README.md`：运行方法、可调参数、物理假设与边界条件、验证情况。
- 推荐：把物理/核心逻辑与渲染分离，并附一个可在 Node 下运行的测试（参考 `water-lab/tests/`）。

## 本地验证

```bash
cd <repo 根目录>
python -m http.server 8123      # 或 .venv\Scripts\python -m http.server 8123
# 打开 http://localhost:8123/animations/<slug>/
```

- 不能只凭代码臆测：至少确认页面能加载、控制台无报错、核心交互可用，并记录验证结果。
- 若当前环境无法运行浏览器或做视觉检查，必须明确说明「未做视觉验证」，不要编造测试结论。

## 提交与推送

- 只改 `animations/<slug>/` 和 `animations/README.md` 的索引。
- 除任务明确要求外，不要改动 `high-school/`、`university/`、`teaching/` 和根 `README.md` 的其它内容。
- 不要提交 `.venv/`、`node_modules/`、`__pycache__/`、大型视频/图片素材（大素材用 Release 附件或 Git LFS）。
- 提交信息格式：`animations: 新增 <slug> <一句话描述>`
- 完成后推送到 `main`：`git push origin main`。

## 不要做

- 不要开启 GitHub Pages、修改仓库设置、添加协作者或改动分支保护，除非任务明确要求。
- 不要修改根 `README.md` 的「许可说明」。
