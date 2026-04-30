import { Page, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';


export class BaseTestPage {

    protected page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    /**
     * Navigate to any page using the top navigation links
     * Example:
     * await basePage.directingToPage("Inventory")
     */
    async directingToPage(pageName: string) {
        await this.page.getByRole('link', { name: pageName, exact: true }).click();

        // optional: verify navigation happened
        await this.verifyNavigation(pageName);
    }

    /**
     * Verify the URL after navigation
     */
    async verifyNavigation(pageName: string) {
        const pageRoutes: Record<string, string> = {
            Home: '/home',
            Login: '/login',
            Inventory: '/inventory',
            Sales: '/sales',
            Service: '/service',
            Finance: '/finance',
            Promotion: '/promotion',
            'Admin – User Management': '/admin'
        };

        if (pageRoutes[pageName]) {
            await expect(this.page).toHaveURL(new RegExp(pageRoutes[pageName]));
        }
    }

    /**
     * Logout action available from any page
     */
    async logout() {
        await this.page.getByRole('button', { name: /logout/i }).click();
    }

    /**
     * Wait for page to fully load
     */
    async waitForPageLoad() {
        await this.page.waitForLoadState('networkidle');
    }

    /**
     * Generic click helper
     */
    async clickButton(buttonName: string) {
        await this.page.getByRole('button', { name: buttonName }).click();
    }
    async takeScreenshot(fileName: string, fullPage: boolean = true) {
        const projectRoot = path.resolve(__dirname, '../../../../');
        const reportsDir = path.join(projectRoot,  'reports', 'ui');

        if (!fs.existsSync(reportsDir)) {
            fs.mkdirSync(reportsDir, { recursive: true });
        }

        const filePath = path.join(reportsDir, `${fileName}.png`);

        console.log(`Saving screenshot to: ${filePath}`);

        await this.page.screenshot({
            path: filePath,
            fullPage
        });
    }

    /**
     * Generic text verification
     */
    async verifyTextVisible(text: string) {
        await expect(this.page.getByText(text)).toBeVisible();
    }
    async clickButtonWithName(name: string) {
        const button = this.page.getByRole('button', { name: name })
        await button.waitFor({ state: 'visible' })
        await button.click();
    }
    async fillInputBox(name: string, text: string) {
        await this.page.locator(`input[name="${name}"]`).fill(text);
    }
    async chooseFromDropdown(name: string, value: string) {
        const locator = this.page.locator(`select[name="${name}"]`);
        await locator.selectOption(value.trim());


    }

}