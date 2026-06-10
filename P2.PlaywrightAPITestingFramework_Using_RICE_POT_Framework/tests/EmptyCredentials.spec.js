

const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');

test.describe('Empty Credentials Validation - Salesforce', () => {
    let loginPage;

    test.beforeEach(async ({ page }) => {
        loginPage = new LoginPage(page);
        await loginPage.navigateToLoginPage();
        await loginPage.verifyLoginPageLoaded();
    });

    test('TC_008 | Submitting empty username and password shows error', async ({ page }) => {
        await loginPage.clickLoginButton();
        await expect(loginPage.errorContainer).toBeVisible();
        await expect(page).toHaveURL(/login\.salesforce\.com/);
    });

    test('TC_009 | Submitting valid username with empty password shows error', async ({ page }) => {
        await loginPage.enterUsername('validuser@test.com');
        await loginPage.clickLoginButton();
        await expect(loginPage.errorContainer).toBeVisible();
        await expect(page).toHaveURL(/login\.salesforce\.com/);
    });

    test('TC_010 | Submitting empty username with valid password shows error', async ({ page }) => {
        await loginPage.enterPassword('ValidPassword@123');
        await loginPage.clickLoginButton();
        await expect(loginPage.errorContainer).toBeVisible();
        await expect(page).toHaveURL(/login\.salesforce\.com/);
    });
});
