// test/UI/pages/InventoryPage.ts
import { expect, Locator, Page } from '@playwright/test';

export class InventoryPage {
    readonly page: Page;
    readonly fileInput: Locator;
    readonly uploadButton: Locator;
    readonly tableRows: Locator;

    constructor(page: Page) {
        this.page = page;

        // Excel upload section
        this.fileInput = page.locator('input[type="file"]');
        this.uploadButton = page.getByRole('button', { name: /upload inventory file/i });

        // All table rows on page
        this.tableRows = page.locator('table tbody tr');
    }

    async uploadExcelFile(filePath: string) {
        await expect(this.fileInput).toBeVisible();
        await this.fileInput.setInputFiles(filePath);
        await this.uploadButton.click();

        // wait for upload request to finish
        await this.page.waitForLoadState('networkidle');
        await this.page.waitForTimeout(3000)
    }

    async expectCarsForLocation(location: string, expectedCount: number) {
        // Assumes location appears as a table cell in the inventory table.
        // This counts rows that contain the location text.
        const matchingRows = this.page.locator('table tbody tr', {
            has: this.page.locator(`td:text-is("${location}")`)
        });

        await expect(matchingRows).toHaveCount(expectedCount);
    }
}