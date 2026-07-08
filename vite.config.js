import { defineConfig } from 'vite'
import { resolve } from 'path'
import { fileURLToPath } from 'url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))
const ROOT = 'frontend'
const PAGES = ['index', 'home', 'latest', 'article', 'login', 'register', 'bookmarks', 'profile', 'ai', 'map', 'admin', '404', 'trending', 'live', 'history', 'forgot-password', 'contact', 'about', 'privacy', 'auth-callback']

function buildInput() {
  const entries = {}
  for (const name of PAGES) {
    entries[name] = resolve(__dirname, ROOT, `${name}.html`)
  }
  return entries
}

export default defineConfig({
  root: ROOT,
  base: '/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    minify: 'esbuild',
    cssMinify: true,
    rollupOptions: {
      input: buildInput(),
      output: {
        entryFileNames: 'assets/js/[name]-[hash].js',
        chunkFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash][extname]',
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  plugins: [
    {
      name: 'samachar-html-transform',
      transformIndexHtml: {
        order: 'pre',
        handler(html, ctx) {
          if (ctx.filename?.endsWith('auth-callback.html') || ctx.filename?.endsWith('map.html')) return html;
          return html
            .replace(
              /<script[^>]*src=["']assets\/js\/layout\.js(?:\?[^"']*)?["'][^>]*><\/script>\s*/g,
              '',
            )
            .replace(
              /<script[^>]*src=["']assets\/js\/api\.js(?:\?[^"']*)?["'][^>]*><\/script>\s*/g,
              '',
            )
            .replace(
              /<script[^>]*src=["']assets\/js\/app\.js(?:\?[^"']*)?["'][^>]*><\/script>\s*/g,
              '',
            )
            .replace(
              '</body>',
              '  <script type="module" src="/src/js/main.js"></script>\n</body>',
            )
        },
      },
    },
  ],
})
