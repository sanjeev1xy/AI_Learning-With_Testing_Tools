const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');

test.describe('Valid Login - Salesforce', () => {
    let loginPage;

    test.beforeEach(async ({ page }) => {
        loginPage = new LoginPage(page);
        await loginPage.navigateToLoginPage();
        await loginPage.verifyLoginPageLoaded();
    });

    test('TC_001 | Valid credentials redirect to Salesforce dashboard', async ({ page }) => {
        await loginPage.performLogin('validuser@test.com', 'ValidPassword@123');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveURL(/salesforce\.com/i);
        await expect(page).not.toHaveURL(/login\.salesforce\.com/);
    });

    test('TC_002 | Valid credentials with Remember Me redirect to dashboard', async ({ page }) => {
        await loginPage.performLoginWithRememberMe('validuser@test.com', 'ValidPassword@123');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveURL(/salesforce\.com/i);
        await expect(page).not.toHaveURL(/login\.salesforce\.com/);
    });
});
