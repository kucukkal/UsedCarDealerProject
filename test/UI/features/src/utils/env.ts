import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
dotenv.config();

// export const LOGIN_URL = process.env.LOGIN_URL as string;
// export const API_URL = process.env.API_URL as string;
const envPath = path.resolve(__dirname, '../../../../.env');

// Load .env only if it exists locally.
// In GitHub Actions, secrets come through process.env already.
if (fs.existsSync(envPath)) {
    dotenv.config({ path: envPath });
}

function required(name: string): string {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Missing required environment variable: ${name}`);
    }
    return value;
}

export const env = {
    adminUsername: required('ADMIN_USERNAME'),
    adminPassword: required('ADMIN_PASSWORD'),
    baseUrl: process.env.BASE_URL || 'http://localhost:5173',
    LOGIN_URL:required('LOGIN_URL'),
    API_URL:required('API_URL')

};