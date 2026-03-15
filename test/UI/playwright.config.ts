import { defineConfig, devices } from '@playwright/test';

export default defineConfig({

    testDir: './tests',

    timeout: 30 * 1000,

    expect: {
        timeout: 5000,
    },

    fullyParallel: true,

    forbidOnly: !!process.env.CI,

    retries: process.env.CI ? 2 : 0,

    workers: process.env.CI ? 2 : undefined,

    reporter: [
        ['list'],
        ['html', { outputFolder: '../reports/ui/playwright-report', open: 'never' }]
    ],

    use: {
        headless: true,
        baseURL: 'http://localhost:5173',

        trace: 'on-first-retry',

        screenshot: 'only-on-failure',

        video: 'retain-on-failure',

        actionTimeout: 0,
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },

        {
            name: 'firefox',
            use: { ...devices['Desktop Firefox'] },
        },

        {
            name: 'webkit',
            use: { ...devices['Desktop Safari'] },
        },
    ],

    webServer: {
        command: 'npm run dev',
        port: 5173,
        reuseExistingServer: !process.env.CI,
    },
});