import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

/**
 * Bitta bundle chiqaradi: backend/frontend/dist/widgets/widgets.js
 * Django uni {% static 'widgets/widgets.js' %} orqali oladi
 * (STATICFILES_DIRS ichida frontend/dist bor).
 *
 * Fayl nomi hashsiz — Django shabloni oddiy static yo'l bilan ishlashi uchun.
 * Prodda kesh uchun ManifestStaticFilesStorage ishlatiladi.
 *
 * Eslatma: cssCodeSplit:false bilan Vite 7 chiqargan CSS fayl nomi entry
 * nomiga bog'liq bo'lib qolishi mumkin (masalan "main.css"), shuning uchun
 * assetFileNames CSS uchun aynan "widgets/style.css" ga moslab qo'yilgan;
 * boshqa asset turlari "widgets/[name][extname]" bo'yicha chiqadi.
 */
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, "../backend/frontend/dist"),
    emptyOutDir: true,
    cssCodeSplit: true,
    manifest: false,
    rollupOptions: {
      input: {
        widgets: resolve(__dirname, "src/main.jsx"),
        admin: resolve(__dirname, "src/admin.jsx"),
      },
      output: {
        entryFileNames: (chunk) => chunk.name === "admin" ? "admin/admin.js" : "widgets/widgets.js",
        chunkFileNames: "shared/[name].js",
        assetFileNames: (assetInfo) => {
          const name = assetInfo.name || (assetInfo.names && assetInfo.names[0]) || "";
          if (name.endsWith(".css")) return name.includes("admin") ? "admin/admin.css" : "widgets/style.css";
          return "widgets/[name][extname]";
        },
      },
    },
  },
});
