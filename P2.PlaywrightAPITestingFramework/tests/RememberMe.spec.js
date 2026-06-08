const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');

test.describe('Remember Me Functionality - Salesforce', () => {
    let loginPage;

    test.beforeEach(async ({ page }) => {
        loginPage = new LoginPage(page);
        await loginPage.navigateToLoginPage();
        await loginPage.verifyLoginPageLoaded();
    });

    test('TC_005 | Remember Me checkbox is unchecked by default', async ({ page }) => {
        const isChecked = await loginPage.isRememberMeChecked();
        expect(isChecked).toBe(false);
    });

    test('TC_006 | Remember Me checkbox toggles correctly', async ({ page }) => {
        await loginPage.checkRememberMe();
        expect(await loginPage.isRememberMeChecked()).toBe(true);
        await loginPage.uncheckRememberMe();
        expect(await loginPage.isRememberMeChecked()).toBe(false);
    });

    test('TC_007 | Remember Me state persists after entering credentials', async ({ page }) => {
        await loginPage.enterUsername('validuser@test.com');
        await loginPage.enterPassword('ValidPassword@123');
        await loginPage.checkRememberMe();
        expect(await loginPage.isRememberMeChecked()).toBe(true);
    });
});
