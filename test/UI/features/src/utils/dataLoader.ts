import fs from "fs";
import path from "path";

export function loadFixture<T>(fileName: string): T {
    const filePath = path.resolve(__dirname, `../fixtures/${fileName}`);
    return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}
