// support/hooks.ts
import { Before, After } from "@cucumber/cucumber";
import { chromium } from "playwright";
import type { CustomWorld } from "./world.js";
const isHeaded = process.env.HEADED === 'true';

Before(async function (this: CustomWorld) {
    this.browser = await chromium.launch({headless: !isHeaded,
        slowMo: isHeaded ? 200 : 0,
    });
    this.context = await this.browser.newContext();
    this.page = await this.context.newPage();
});

After(async function (this: CustomWorld) {
    await this.page?.close();
    await this.context?.close();
    await this.browser?.close();
});
