import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const target = resolve(frontendDir, "../backend/frontend/src/i18n.json");

await mkdir(dirname(target), { recursive: true });
await copyFile(resolve(frontendDir, "src/i18n.json"), target);
