/**
  * Steps for login.feature
  * Rules:
  * - Use Playwright Page from CustomWorld (this.page)
  * - Use LoginPage POM from ../src/pages/LoginPage.js
  * - No raw locators in steps
  * - Steps should call POM methods only
  */
import { Given, When, Then } from "@cucumber/cucumber";
import type { CustomWorld } from "../../support/world";
import { LoginPage } from "../src/pages/loginPage"
import { InventoryPage } from "../src/pages/inventoryPage"
import path from 'path'


console.log("✅ my_steps.ts loaded");
Given("User navigates to Login page", async function (this: CustomWorld) {
    const page = new LoginPage(this.page!);
    await page.goto()
    //await page.takeScreenshot("fullpage_LoginPage.png",  true);
    console.log("✅ step registered");
});
When("User enters {string} credentials", async function (this: CustomWorld, userType: string) {
    const page = new LoginPage(this.page!);
    await page.login(userType);
});
Then("User is at Home page", async function (this: CustomWorld) {
    const page = new LoginPage(this.page!);
    await page.getMessage();
});

When('I click the {string} link',  async function (this: CustomWorld, pageName: string) {
    const page = new LoginPage(this.page!);
    await page.gotoPage(pageName)
});

When('I upload the inventory Excel file {string}', async function (this: CustomWorld, fileName: string) {
    const page = new InventoryPage(this.page!);
    const filePath = path.resolve(__dirname, "../../../fixtures", fileName);
    await page.uploadExcelFile(filePath);

});

Then(/^I should see "([^"]*)" cars for location "([^"]*)"$/,async function (this: CustomWorld, expectedCount: string, location: string) {
    const page = new InventoryPage(this.page!);
    await page.expectCarsForLocation(location, parseInt(expectedCount));
});

 // When("I enter password {string}", async function (this: CustomWorld, password: string) {
 //   const loginPage = new LoginPage(this.page);
 //   await loginPage.enterPassword(password);
 // });

 // When("I click the login button", async function (this: CustomWorld) {
 //   const loginPage = new LoginPage(this.page!);
 //   await loginPage.clickLoginButton();
 // });
 //
 // Then("I should see the dashboard", async function (this: CustomWorld) {
 //   const loginPage = new LoginPage(this.page!);
 //   await loginPage.verifyDashboardVisible();
 // });
 //
 // Then("I should see an error message {string}", async function (this: CustomWorld, errorMsg: string) {
 //     const loginPage = new LoginPage(this.page!);
 //     await loginPage.verifyDashboardVisible();
 // });
Then(/^User logs out$/,  async function () {
    const page = new LoginPage(this.page!);
    await page.logout();
});
When(/^I used the following values to reroute the api call$/, async function (dataTable) {
    const rows = dataTable.hashes();

    const vehicle = rows[0];

    this.vehiclePayload = {
        make: vehicle.make,
        model: vehicle.model,
        sub_model: vehicle.sub_model,
        year: Number(vehicle.year),
        mileage: Number(vehicle.mileage),
        vehicle_type: vehicle.vehicle_type,
        color: vehicle.color,
        antique: vehicle.antique === 'Yes',
        condition_type: vehicle.condition_type,
        cost: Number(vehicle.cost),
        sale_price: Number(vehicle.sale_price),
        location: vehicle.location,
    };

    console.log('Saved payload:', this.vehiclePayload);
});
When('I reroute the inventory API call with my saved payload', async function (this: CustomWorld) {
    const page = new InventoryPage(this.page!);
    await page.rerouteSingleCarEntryApi(this.vehiclePayload);
});
Then(/^I submit the vehicle form$/, async function () {
    const page = new InventoryPage(this.page!);
    await page.clickButtonWithName("Add Car")
});