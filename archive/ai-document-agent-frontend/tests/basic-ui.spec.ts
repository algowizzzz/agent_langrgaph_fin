import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Basic UI Functionality', () => {
  test('should load the application and show welcome screen', async ({ page }) => {
    await page.goto('/');
    
    // Check that the main title is visible
    await expect(page.locator('h1:has-text("AI Document Agent")')).toBeVisible();
    
    // Check that welcome message is shown
    await expect(page.locator('h2:has-text("Welcome to AI Document Agent")')).toBeVisible();
    
    // Check that drag and drop area is visible
    await expect(page.locator('text=Drag & drop your document here')).toBeVisible();
    
    // Check that the chat input is present
    await expect(page.locator('textarea')).toBeVisible();
  });

  test('should upload a document and show success feedback', async ({ page }) => {
    await page.goto('/');
    
    // Get the file input from chat component using test ID
    const fileInput = page.locator('[data-testid="chat-upload-input"]');
    
    // Upload test document
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for success message to appear
    await expect(page.locator('[data-testid="upload-success-message"]')).toBeVisible({ timeout: 10000 });
    
    // Check that success message contains filename
    const successMessage = await page.locator('[data-testid="upload-success-message"]').textContent();
    expect(successMessage).toContain('test-document.txt');
    expect(successMessage).toContain('chunks created');
  });

  test('should enable send button when text is entered', async ({ page }) => {
    await page.goto('/');
    
    // Upload document first
    const fileInput = page.locator('[data-testid="chat-upload-input"]');
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload success
    await expect(page.locator('[data-testid="upload-success-message"]')).toBeVisible({ timeout: 10000 });
    
    // Get chat input and send button using test IDs
    const chatInput = page.locator('[data-testid="chat-message-input"]');
    const sendButton = page.locator('[data-testid="send-message-button"]');
    
    // Initially send button should be disabled
    await expect(sendButton).toBeDisabled();
    
    // Type a message
    await chatInput.fill('Hello');
    
    // Send button should now be enabled
    await expect(sendButton).toBeEnabled();
  });

  test('should send a message and show it in the chat', async ({ page }) => {
    await page.goto('/');
    
    // Upload document
    const fileInput = page.locator('[data-testid="chat-upload-input"]');
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload success
    await expect(page.locator('[data-testid="upload-success-message"]')).toBeVisible({ timeout: 10000 });
    
    // Send a message
    const chatInput = page.locator('[data-testid="chat-message-input"]');
    const sendButton = page.locator('[data-testid="send-message-button"]');
    
    await chatInput.fill('Test message');
    await sendButton.click();
    
    // Check that the message appears in the chat
    await expect(page.locator('text=Test message')).toBeVisible({ timeout: 5000 });
  });

  test('should show loading state when processing', async ({ page }) => {
    await page.goto('/');
    
    // Upload document
    const fileInput = page.locator('input[type="file"]').last();
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    await page.waitForTimeout(2000);
    
    // Send a message
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    await chatInput.fill('Summarize this document');
    await sendButton.click();
    
    // Check for loading indicator (spinning animation)
    await expect(page.locator('.animate-spin')).toBeVisible({ timeout: 5000 });
  });

  test('should click quick suggestion buttons', async ({ page }) => {
    await page.goto('/');
    
    // Upload document
    const fileInput = page.locator('input[type="file"]').last();
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    await page.waitForTimeout(2000);
    
    // Click a suggestion button
    const summarizeButton = page.locator('button:has-text("Summarize document")');
    await expect(summarizeButton).toBeVisible();
    await summarizeButton.click();
    
    // Check that input is populated
    const chatInput = page.locator('textarea');
    await expect(chatInput).toHaveValue('Summarize document');
  });

  test('should handle backend response', async ({ page }) => {
    await page.goto('/');
    
    // Upload document
    const fileInput = page.locator('input[type="file"]').last();
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    await page.waitForTimeout(3000);
    
    // Send a simple message
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    await chatInput.fill('Hello');
    await sendButton.click();
    
    // Wait for user message to appear
    await expect(page.locator('text=Hello')).toBeVisible({ timeout: 5000 });
    
    // Wait for assistant response (this should work if backend is running)
    // We give it more time since it involves actual API calls
    await expect(page.locator('[data-testid="chat-message"]')).toHaveCount(2);
    await expect(page.locator('[data-testid="chat-message"]').last()).not.toContainText('error');
  });
});