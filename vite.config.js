import { resolve } from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  root: 'frontend',
  publicDir: false,
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'frontend/index.html'),
        home: resolve(__dirname, 'frontend/home.html'),
        latest: resolve(__dirname, 'frontend/latest.html'),
        trending: resolve(__dirname, 'frontend/trending.html'),
        article: resolve(__dirname, 'frontend/article.html'),
        factcheck: resolve(__dirname, 'frontend/factcheck.html'),
        about: resolve(__dirname, 'frontend/about.html'),
        profile: resolve(__dirname, 'frontend/profile.html'),
        bookmarks: resolve(__dirname, 'frontend/bookmarks.html'),
        login: resolve(__dirname, 'frontend/login.html'),
        register: resolve(__dirname, 'frontend/register.html'),
        notfound: resolve(__dirname, 'frontend/404.html'),
      },
    },
  },
});
