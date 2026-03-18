import {Page, Locator} from '@playwright/test';
import {expect} from '@playwright/test';
import {loadFixture} from "../utils/dataLoader";
import { env } from '../utils/env';
import { BaseTestPage} from "./BaseTestPage";

export class LoginPage extends BaseTestPage {
    readonly page: Page;
    readonly usernameInput: Locator;
    readonly passwordInput: Locator;
    readonly loginButton: Locator;
    readonly messageText: Locator;
    readonly logoutButton: Locator;

    constructor(page: Page) {
        super(page)
        this.page = page;
        this.usernameInput = page.getByRole('textbox').first();
        this.passwordInput = page.locator('input[type="password"]');
        this.loginButton = page.getByRole('button', { name: 'Login' });
        this.logoutButton = page.getByRole('button', { name: 'Logout' });
        this.messageText = page.getByText('Welcome to the Used Car');
    }

    async goto() {
        await this.page.goto(env.LOGIN_URL);
        await this.verifyLoginPage();
        // Or wherever your file is hosted
    }
    async verifyLoginPage(){
        await expect(this.usernameInput).toBeVisible()
        await expect(this.passwordInput).toBeVisible()
        await expect(this.loginButton).toBeVisible()
    }
    async gotoPage(pageName: string) {
        await this.directingToPage(pageName)
        // await this.takeScreenshot("full_pageDirected.png",  true);
    }

    async login(userType:string) {
        let username=env.adminUsername;
        let password=env.adminPassword;
        // switch(userType) {
        //     case "admin":
        //         username=env.adminUsername;
        //         password=env.adminPassword;
        //         break;
            // case "sales_denver":
            //     username=users.sales_denver.username;
            //     password=users.sales_denver.password;
            //     break;
            // case "invalid admin":
            //     username=users.invalidAdmin.username;
            //     password=users.invalidAdmin.password;
            //     break;
        //}
        await this.usernameInput.fill(username);
        await this.passwordInput.fill(password);
        // await this.takeScreenshot("full_LoginCredentials.png",  true);
        await this.loginButton.click();
        await this.page.waitForTimeout(2000);
    }
    async logout(){
        await this.logoutButton.click();
        await this.page.waitForTimeout(3000)
    }
    async getMessage() {
        return await this.messageText.textContent();
    }
}
