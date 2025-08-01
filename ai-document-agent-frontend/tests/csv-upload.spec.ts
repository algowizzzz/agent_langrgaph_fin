import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('CSV File Upload', () => {
  test('should successfully upload test_business_data.csv', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');

    // Locate the file input
    const fileInput = page.locator('[data-testid="chat-upload-input"]');
    
    // Define the path to the test file
    const testFilePath = '/Users/saadahmed/Desktop/Apps/AWS_Extra/Agent/test_business_data.csv';

    // Upload the file
    await fileInput.setInputFiles(testFilePath);

    // A simple wait to see if the UI updates at all
    await page.waitForTimeout(5000); 

    // Wait for the success message to be visible
    const successMessage = page.locator('[data-testid="upload-success-message"]');
    await expect(successMessage).toBeVisible({ timeout: 15000 });

    // Verify the success message content
    const messageText = await successMessage.textContent();
    expect(messageText).toContain('test_business_data.csv');
    expect(messageText).toContain('chunks created');

    console.log('CSV upload test completed successfully.');
  });
});
