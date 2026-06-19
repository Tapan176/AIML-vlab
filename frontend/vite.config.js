import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Migrated from Create React App.
//   - CRA put JSX inside .js files and relied on the automatic JSX runtime
//     (components don't `import React`). Vite/esbuild treats .js as plain JS by
//     default, so we point esbuild at src/*.js with the jsx loader + automatic
//     runtime. optimizeDeps mirrors that for dev dependency pre-bundling.
//   - Build output goes to build/ (not Vite's default dist/) so the Dockerfile
//     and vercel.json (distDir: build) keep working unchanged.
export default defineConfig({
  plugins: [react()],
  server: { port: 3000 },
  build: { outDir: 'build' },
  esbuild: {
    loader: 'jsx',
    include: /src\/.*\.jsx?$/,
    exclude: [],
    jsx: 'automatic',
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: { '.js': 'jsx' },
      jsx: 'automatic',
    },
  },
  // Vitest config — read only by `vitest`, ignored by `vite build`.
  test: { environment: 'jsdom', globals: true },
});
