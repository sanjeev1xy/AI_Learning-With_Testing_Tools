const { expect } = require('@playwright/test');

class LoginPage {
    constructor(page) {
        this.page = page;
        this.usernameInput = page.locator("//input[@type='email']");
        this.passwordInput = page.locator("//input[@type='password']");
        this.rememberMeCheckbox = page.locator("//input[@type='checkbox']");
        this.loginButton = page.locator("//input[@value='Log In']");
        this.errorContainer = page.locator("//div[contains(@class,'loginError') and normalize-space()]");
        this.errorMessage = page.locator("//div[contains(@class,'loginError') and normalize-space()]");
        this.forgotPasswordLink = page.locator("//a[normalize-space()='Forgot Your Password?']");
    }

    async navigateToLoginPage() {
        await this.page.goto('https://login.salesforce.com/?locale=in');
        await this.page.waitForLoadState('load');
        const consentButton = this.page.locator("//button[normalize-space()='Continue' or normalize-space()='Accept All' or normalize-space()='Save']");
        const isConsentVisible = await consentButton.first().isVisible({ timeout: 3000 }).catch(() => false);
        if (isConsentVisible) {
            await consentButton.first().click();
            await this.page.waitForLoadState('load');
        }
    }

    async verifyLoginPageLoaded() {
        await expect(this.usernameInput).toBeVisible();
        await expect(this.passwordInput).toBeVisible();
        await expect(this.loginButton).toBeVisible();
    }

    async enterUsername(username) {
        await this.usernameInput.waitFor({ state: 'visible' });
        await this.usernameInput.clear();
        await this.usernameInput.fill(username);
    }

    async enterPassword(password) {
        await this.passwordInput.waitFor({ state: 'visible' });
        await this.passwordInput.clear();
        await this.passwordInput.fill(password);
    }

    async clickLoginButton() {
        await this.loginButton.waitFor({ state: 'visible' });
        await this.loginButton.click();
    }

    async checkRememberMe() {
        await this.rememberMeCheckbox.waitFor({ state: 'visible' });
        await this.rememberMeCheckbox.check();
    }

    async uncheckRememberMe() {
        await this.rememberMeCheckbox.waitFor({ state: 'visible' });
        await this.rememberMeCheckbox.uncheck();
    }

    async isRememberMeChecked() {
        return await this.rememberMeCheckbox.isChecked();
    }

    async performLogin(username, password) {
        await this.enterUsername(username);
        await this.enterPassword(password);
        await this.clickLoginButton();
    }

    async performLoginWithRememberMe(username, password) {
        await this.enterUsername(username);
        await this.enterPassword(password);
        await this.checkRememberMe();
        await this.clickLoginButton();
    }

    async getErrorMessage() {
        await this.errorContainer.waitFor({ state: 'visible' });
        return await this.errorMessage.textContent();
    }

    async isErrorDisplayed() {
        return await this.errorContainer.isVisible();
    }

    async clearAllFields() {
        await this.usernameInput.clear();
        await this.passwordInput.clear();
    }
}

module.exports = { LoginPage };
