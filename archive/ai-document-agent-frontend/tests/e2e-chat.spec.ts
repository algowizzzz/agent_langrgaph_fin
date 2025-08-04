import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('End-to-End Chat Flow', () => {

  test('should upload a document and get a summary', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');

    // 1. Upload the document
    const fileInput = page.locator('[data-testid="chat-upload-input"]');
    const testFilePath = '/Users/saadahmed/Desktop/Apps/AWS_Extra/Agent/ai-document-agent-frontend/tests/test-document.txt';
    await fileInput.setInputFiles(testFilePath);

    // Wait for the success message to be visible
    const successMessage = page.locator('[data-testid="upload-success-message"]');
    await expect(successMessage).toBeVisible({ timeout: 20000 });

    // 2. Ask a question
    const chatInput = page.locator('[data-testid="chat-message-input"]');
    await chatInput.fill('please summarize this document');
    
    // 3. Submit the question
    const sendButton = page.locator('[data-testid="send-message-button"]');
    await expect(sendButton).toBeEnabled();
    await sendButton.click();

    // 4. Verify the response
    // There should be 3 messages now: welcome, user's question, and assistant's response.
    const chatMessages = page.locator('[data-testid="chat-message"]');
    await expect(chatMessages).toHaveCount(3, { timeout: 30000 });

    // Check that the last message is from the assistant and contains relevant content
    const lastMessage = chatMessages.last();
    await expect(lastMessage).not.toContainText('error');
    await expect(lastMessage).toContainText('Hermes'); // A keyword from the test document
  });

});
