import { execSync } from "child_process";
import * as path from "path";
import * as fs from "fs";

const openapiPath = path.resolve(__dirname, "../../../apps/api/openapi.json");
const outputPath = path.resolve(__dirname, "../src/index.ts");

console.log("Generating types from:", openapiPath);

if (!fs.existsSync(openapiPath)) {
  console.error(`Error: OpenAPI schema not found at ${openapiPath}. Run export_openapi.py first.`);
  process.exit(1);
}

try {
  // Let's generate types using openapi-typescript CLI
  execSync(`npx openapi-typescript "${openapiPath}" -o "${outputPath}"`, { stdio: "inherit" });
  console.log("Types successfully generated at:", outputPath);
} catch (error) {
  console.error("Error generating types:", error);
  process.exit(1);
}
