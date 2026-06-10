const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');

test.describe('Invalid Login - Salesforce', () => {
    let loginPage;

    test.beforeEach(async ({ page }) => {
        loginPage = new LoginPage(page);
        await loginPage.navigateToLoginPage();
        await loginPage.verifyLoginPageLoaded();
    });

    test('TC_003 | Incorrect password displays authentication error', async ({ page }) => {
        await loginPage.performLogin('validuser@test.com', 'WrongPassword999');
        await expect(loginPage.errorContainer).toBeVisible();
        const errorText = await loginPage.getErrorMessage();
        expect(errorText).toContain('Please check your username and password');
        await expect(page).toHaveURL(/login\.salesforce\.com/);
    });

    test('TC_004 | Non-existent username displays authentication error', async ({ page }) => {
        await loginPage.performLogin('nonexistent_xyz_abc@fake12345.com', 'AnyPassword@123');
        await expect(loginPage.errorContainer).toBeVisible();
        const isError = await loginPage.isErrorDisplayed();
        expect(isError).toBe(true);
        await expect(page).toHaveURL(/login\.salesforce\.com/);
    });
});
