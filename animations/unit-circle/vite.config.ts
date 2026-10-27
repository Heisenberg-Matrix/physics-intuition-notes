import { defineConfig } from 'vite';

// base: './' 让构建产物使用相对路径，可放到任意静态子目录(GitHub Pages /animations/unit-circle/)
export default defineConfig({
  base: './',
  build: { outDir: 'dist' },
});