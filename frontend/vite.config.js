import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server on port 5173 (matches FRONTEND_ORIGIN in backend .env).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
