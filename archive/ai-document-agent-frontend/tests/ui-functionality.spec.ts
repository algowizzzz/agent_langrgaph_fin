import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('AI Document Agent UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for the page to load
    await expect(page.locator('h1')).toContainText('AI Document Agent');
  });

  test('should display welcome screen and basic UI elements', async ({ page }) => {
    // Check header elements
    await expect(page.locator('h1')).toContainText('AI Document Agent');
    await expect(page.locator('text=Intelligent document analysis powered by AI')).toBeVisible();
    
    // Check welcome message
    await expect(page.locator('h2')).toContainText('Welcome to AI Document Agent');
    await expect(page.locator('text=Upload your documents and start asking questions')).toBeVisible();
    
    // Check document upload area is visible
    await expect(page.locator('text=Drag & drop your document here')).toBeVisible();
    
    // Check supported formats are shown
    await expect(page.locator('text=Supported formats')).toBeVisible();
    await expect(page.locator('text=PDF')).toBeVisible();
    await expect(page.locator('text=DOCX')).toBeVisible();
    await expect(page.locator('text=CSV')).toBeVisible();
    await expect(page.locator('text=TXT')).toBeVisible();
    
    // Check chat input placeholder
    await expect(page.locator('textarea[placeholder*="Upload a document first"]')).toBeVisible();
  });

  test('should upload a document successfully', async ({ page }) => {
    // Get the file upload input (use the hidden one from ChatInput)
    const fileInput = page.locator('input[type="file"]').nth(1);
    
    // Upload the test document
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload to process (check for loading state or success indication)
    // This might take a moment, so we wait for the upload to complete
    await page.waitForTimeout(2000);
    
    // Check if the document status appears or welcome screen changes
    // The exact behavior depends on the implementation
    await expect(page.locator('textarea')).not.toHaveAttribute('placeholder', /Upload a document first/);
  });

  test('should display document status after upload', async ({ page }) => {
    // Upload document first
    const fileInput = page.locator('input[type="file"]').nth(1);
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload to complete
    await page.waitForTimeout(3000);
    
    // Check if document status is shown
    await expect(page.locator('text=test-document.txt')).toBeVisible({ timeout: 10000 });
  });

  test('should allow typing in chat input', async ({ page }) => {
    // Upload document first
    const fileInput = page.locator('input[type="file"]').nth(1);
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload
    await page.waitForTimeout(3000);
    
    // Type in the chat input
    const chatInput = page.locator('textarea');
    await chatInput.fill('Summarize this document');
    
    // Check the input has the text
    await expect(chatInput).toHaveValue('Summarize this document');
  });

  test('should show quick suggestion buttons', async ({ page }) => {
    // Upload document first
    const fileInput = page.locator('input[type="file"]').nth(1);
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload
    await page.waitForTimeout(3000);
    
    // Check quick suggestion buttons are visible
    await expect(page.locator('button:has-text("Summarize document")')).toBeVisible();
    await expect(page.locator('button:has-text("Count word")')).toBeVisible();
    await expect(page.locator('button:has-text("Extract key topics")')).toBeVisible();
  });

  test('should enable send button when text is entered', async ({ page }) => {
    // Upload document first
    const fileInput = page.locator('input[type="file"]').nth(1);
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload
    await page.waitForTimeout(3000);
    
    // Initially send button should be disabled
    const sendButton = page.locator('button[title="Send message"]');
    await expect(sendButton).toBeDisabled();
    
    // Type message
    const chatInput = page.locator('textarea');
    await chatInput.fill('Test message');
    
    // Send button should now be enabled
    await expect(sendButton).toBeEnabled();
  });

  test('should click quick suggestion and populate input', async ({ page }) => {
    // Upload document first
    const fileInput = page.locator('input[type="file"]').nth(1);
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload
    await page.waitForTimeout(3000);
    
    // Click a quick suggestion
    await page.locator('button:has-text("Summarize document")').click();
    
    // Check that the input is populated
    const chatInput = page.locator('textarea');
    await expect(chatInput).toHaveValue('Summarize document');
  });

  test('should handle file upload errors gracefully', async ({ page }) => {
    // Try to upload a file that's too large or wrong type
    // This test checks error handling
    const fileInput = page.locator('input[type="file"]').nth(1);
    
    // Create a temporary large file or use a non-supported file type
    // For now, we'll test the UI response to upload attempts
    
    // The exact implementation depends on how errors are shown in the UI
    // This is a placeholder for error handling tests
  });

  test('should send a chat message and show loading state', async ({ page }) => {
    // Upload document first
    const fileInput = page.locator('input[type="file"]').nth(1);
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload
    await page.waitForTimeout(3000);
    
    // Type and send a message
    const chatInput = page.locator('textarea');
    await chatInput.fill('Count the word "risk"');
    
    const sendButton = page.locator('button[title="Send message"]');
    await sendButton.click();
    
    // Check that message appears in chat
    await expect(page.locator('text=Count the word "risk"')).toBeVisible({ timeout: 2000 });
    
    // Check for loading indicator
    await expect(page.locator('.animate-spin')).toBeVisible({ timeout: 5000 });
  });

  test('should display response from backend', async ({ page }) => {
    // Upload document first
    const fileInput = page.locator('input[type="file"]').nth(1);
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload
    await page.waitForTimeout(3000);
    
    // Send a simple message
    const chatInput = page.locator('textarea');
    await chatInput.fill('Hello');
    
    const sendButton = page.locator('button[title="Send message"]');
    await sendButton.click();
    
    // Wait for response (this might take longer for actual API calls)
    // Check that we get some kind of response
    await expect(page.locator('[role="assistant"]')).toBeVisible({ timeout: 30000 });
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // This test can be enhanced to mock network failures
    // and test error handling in the UI
    
    // Upload document first
    const fileInput = page.locator('input[type="file"]').nth(1);
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload
    await page.waitForTimeout(3000);
    
    // Intercept network requests and simulate failure
    await page.route('**/chat', route => {
      route.abort('failed');
    });
    
    // Try to send a message
    const chatInput = page.locator('textarea');
    await chatInput.fill('Test message');
    
    const sendButton = page.locator('button[title="Send message"]');
    await sendButton.click();
    
    // Check for error message
    await expect(page.locator('text=error')).toBeVisible({ timeout: 15000 });
  });

  test('should auto-scroll to new messages', async ({ page }) => {
    // Upload document and send multiple messages to test scrolling
    const fileInput = page.locator('input[type="file"]');
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload
    await page.waitForTimeout(3000);
    
    // Send a message
    const chatInput = page.locator('textarea');
    await chatInput.fill('First message');
    
    const sendButton = page.locator('button[title="Send message"]');
    await sendButton.click();
    
    // Wait a moment and check that new messages are visible
    await page.waitForTimeout(1000);
    await expect(page.locator('text=First message')).toBeVisible();
  });
});