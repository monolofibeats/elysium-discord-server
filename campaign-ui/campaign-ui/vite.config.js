import { defineConfig } from 'vite';

export default defineConfig({
  esbuild: {
    jsx: 'transform', // damit er nicht meckert
    jsxFactory: 'h',
    jsxFragment: 'Fragment'
  }
});
