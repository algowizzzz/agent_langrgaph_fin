import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Comprehensive File Uploads', () => {

  const testCases = [
    {
      name: '.txt',
      filePath: '/Users/saadahmed/Desktop/Apps/AWS_Extra/Agent/ai-document-agent-frontend/tests/test-document.txt',
    },
    {
      name: '.pdf',
      filePath: '/Users/saadahmed/Desktop/Apps/AWS_Extra/Agent/testing_31Jul/test_files/riskandfinace.pdf',
    },
    {
      name: '.csv',
      filePath: '/Users/saadahmed/Desktop/Apps/AWS_Extra/Agent/test_business_data.csv',
    },
    {
      name: '.docx',
      filePath: '/Users/saadahmed/Desktop/Apps/AWS_Extra/Agent/testing_31Jul/test_files/bmo_quarterly_review.docx',
    },
  ];

  for (const tc of testCases) {
    test(`should successfully upload a ${tc.name} file`, async ({ page }) => {
      // Navigate to the application
      await page.goto('/');

      // Locate the file input
      const fileInput = page.locator('[data-testid="chat-upload-input"]');

      // Upload the file
      await fileInput.setInputFiles(tc.filePath);

      // Wait for the success message to be visible
      const successMessage = page.locator('[data-testid="upload-success-message"]');
      await expect(successMessage).toBeVisible({ timeout: 20000 }); // Increased timeout for larger files

      // Verify the success message content
      const messageText = await successMessage.textContent();
      expect(messageText).toContain(path.basename(tc.filePath));
      expect(messageText).toContain('chunks created');
    });
  }
});
