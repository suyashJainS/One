import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  root: resolve(__dirname, "src"),
  base: "/static/dist/",
  build: {
    outDir: resolve(__dirname, "../static/dist"),
    emptyOutDir: true,
    manifest: "manifest.json",
    rollupOptions: {
      input: {
        app: resolve(__dirname, "src/main.js"),
        styles: resolve(__dirname, "src/styles/tailwind.css"),
      },
      output: {
        entryFileNames: "assets/[name].js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name].[ext]",
      },
    },
  },
});
