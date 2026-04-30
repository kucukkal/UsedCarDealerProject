// test/UI/pages/InventoryPage.ts
import { expect, Locator, Page } from '@playwright/test';
import {BaseTestPage} from "./BaseTestPage";

export class InventoryPage extends BaseTestPage{
    readonly page: Page;
    readonly fileInput: Locator;
    readonly uploadButton: Locator;
    readonly tableRows: Locator;

    constructor(page: Page) {
        super(page)
        this.page = page;

        // Excel upload section
        this.fileInput = page.locator('input[type="file"]');
        this.uploadButton = page.getByRole('button', { name: /upload inventory file/i });

        // All table rows on page
        this.tableRows = page.locator('table tbody tr');
    }
    async clickSingleCarEntrySubmitButton(name:string){
        // await this.page!.pause();
        await this.clickButtonWithName(name);
        // const response = await this.page.waitForResponse(
        //     res => res.url().includes('/inventory/') && res.request().method() === 'POST'
        // );
        //
        // console.log(response.status());
        // console.log(await response.text());
        await this.page.waitForTimeout(7000)
    }
    async rerouteSingleCarEntryApi(json: any) {
        await this.page.route('**/inventory', async (route) => {
            const request = route.request();

            console.log('Intercepted:', request.method(), request.url());
            console.log('Original postData:', request.postData());
            console.log('New payload:', json);

            await route.continue({
                method: 'POST',
                headers: {
                    ...request.headers(),
                    'content-type': 'application/json',
                },
                postData: JSON.stringify(json),
            });
        });
    }
    async uploadExcelFile(filePath: string) {
        await expect(this.fileInput).toBeVisible();
        await this.fileInput.setInputFiles(filePath);
        // await this.takeScreenshot("full_UploadExcel.png",  true);
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
        // await this.takeScreenshot("full_inventory.png",  true);
        await expect(matchingRows).toHaveCount(expectedCount);
    }
    async enterValuesToSingleCarAddInputs(dataTable: { raw: () => [any, any]; }){
        const [headers, values] = dataTable.raw();
        for (const header of headers) {
            const i: number = headers.indexOf(header);
            if(header.trim() =='antique' || header.trim() =='condition_type')
                await this.chooseFromDropdown(header.trim(), values[i].trim())
            else
                await this.fillInputBox(header.trim(), values[i].trim())

        }
    }
    async mockCreateVehicleAndInventoryList(vehiclePayload: any) {
        const mockedVehicle = {
            id: 1,
            vin_number: 'MOCKVIN123456789',
            ...vehiclePayload,
            status: 'Available',
        };

        await this.page.route('**/inventory/', async (route) => {
            const request = route.request();

            // Mock POST - do NOT record to DB
            if (request.method() === 'POST') {
                console.log('Mocking POST /inventory/');
                await route.fulfill({
                    status: 201,
                    contentType: 'application/json',
                    body: JSON.stringify(mockedVehicle),
                });
                return;
            }

            // Mock GET - return mocked table data
            if (request.method() === 'GET') {
                console.log('Mocking GET /inventory/');
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify([mockedVehicle]),
                });
                return;
            }

            await route.continue();
        });
    }
}