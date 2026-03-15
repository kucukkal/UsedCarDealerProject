// support/world.ts
import { setWorldConstructor, World } from "@cucumber/cucumber";
import type { IWorldOptions } from "@cucumber/cucumber";
import type { Browser, BrowserContext, Page } from "playwright";

export class CustomWorld extends World {
    browser?: Browser;
    context?: BrowserContext;
    page?: Page;

    constructor(options: IWorldOptions) {
        super(options);
    }
}

setWorldConstructor(CustomWorld);
