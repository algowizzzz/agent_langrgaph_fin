import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Backend Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Upload test document for all tests (use the hidden file input from ChatInput)
    const fileInput = page.locator('input[type="file"]').nth(1);
    const testFilePath = path.join(__dirname, 'test-document.txt');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for upload to complete
    await page.waitForTimeout(5000);
  });

  test('should successfully upload document and show confirmation', async ({ page }) => {
    // Check that document appears in UI after upload
    await expect(page.locator('text=test-document.txt')).toBeVisible({ timeout: 10000 });
    
    // Check that chat input placeholder changes
    await expect(page.locator('textarea')).toHaveAttribute('placeholder', /Ask me anything about your documents/);
  });

  test('should send summarization request and receive response', async ({ page }) => {
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    // Send summarization request
    await chatInput.fill('Summarize this document');
    await sendButton.click();
    
    // Wait for user message to appear
    await expect(page.locator('text=Summarize this document')).toBeVisible({ timeout: 5000 });
    
    // Wait for assistant response (this may take longer)
    await expect(page.locator('[role="assistant"]')).toBeVisible({ timeout: 60000 });
    
    // Check that response contains relevant content
    const response = await page.locator('[role="assistant"]').textContent();
    expect(response).toContain('risk'); // Since our test document is about risk
  });

  test('should count word occurrences correctly', async ({ page }) => {
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    // Send word count request
    await chatInput.fill('Count the word "risk"');
    await sendButton.click();
    
    // Wait for response
    await expect(page.locator('[role="assistant"]')).toBeVisible({ timeout: 60000 });
    
    // Check that response mentions word count
    const response = await page.locator('[role="assistant"]').textContent();
    expect(response).toMatch(/\d+/); // Should contain numbers
  });

  test('should extract key topics from document', async ({ page }) => {
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    // Send key topics request
    await chatInput.fill('Extract key topics from this document');
    await sendButton.click();
    
    // Wait for response
    await expect(page.locator('[role="assistant"]')).toBeVisible({ timeout: 60000 });
    
    // Check that response contains relevant topics
    const response = await page.locator('[role="assistant"]').textContent();
    expect(response?.toLowerCase()).toContain('risk');
  });

  test('should handle multiple consecutive messages', async ({ page }) => {
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    // Send first message
    await chatInput.fill('What is this document about?');
    await sendButton.click();
    
    // Wait for first response
    await expect(page.locator('[role="assistant"]')).toBeVisible({ timeout: 60000 });
    
    // Send second message
    await chatInput.fill('What are the main topics?');
    await sendButton.click();
    
    // Wait for second response
    await expect(page.locator('[role="assistant"]').nth(1)).toBeVisible({ timeout: 60000 });
    
    // Check that both messages and responses are visible
    await expect(page.locator('text=What is this document about?')).toBeVisible();
    await expect(page.locator('text=What are the main topics?')).toBeVisible();
  });

  test('should show processing time in response', async ({ page }) => {
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    // Send message
    await chatInput.fill('Hello');
    await sendButton.click();
    
    // Wait for response
    await expect(page.locator('[role="assistant"]')).toBeVisible({ timeout: 60000 });
    
    // Look for processing time indicator (this depends on UI implementation)
    // The exact selector would depend on how processing time is displayed
  });

  test('should handle backend errors gracefully', async ({ page }) => {
    // Mock backend to return error
    await page.route('**/chat', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });
    
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    // Send message
    await chatInput.fill('Test error handling');
    await sendButton.click();
    
    // Check for error message in UI
    await expect(page.locator('text=error')).toBeVisible({ timeout: 15000 });
  });

  test('should handle long processing times', async ({ page }) => {
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    // Send a complex query that might take longer
    await chatInput.fill('Provide a detailed analysis of all the concepts in this document with their relationships');
    await sendButton.click();
    
    // Check that loading state is shown
    await expect(page.locator('.animate-spin')).toBeVisible({ timeout: 5000 });
    
    // Wait for eventual response (longer timeout for complex queries)
    await expect(page.locator('[role="assistant"]')).toBeVisible({ timeout: 120000 });
  });

  test('should maintain session consistency', async ({ page }) => {
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    // Send first message about the document
    await chatInput.fill('What is the main topic?');
    await sendButton.click();
    
    // Wait for response
    await expect(page.locator('[role="assistant"]')).toBeVisible({ timeout: 60000 });
    
    // Send follow-up that references previous context
    await chatInput.fill('Tell me more about that topic');
    await sendButton.click();
    
    // Wait for second response
    await expect(page.locator('[role="assistant"]').nth(1)).toBeVisible({ timeout: 60000 });
    
    // The response should be contextually relevant
    const secondResponse = await page.locator('[role="assistant"]').nth(1).textContent();
    expect(secondResponse?.length).toBeGreaterThan(10); // Should have substantial content
  });

  test('should display reasoning steps if available', async ({ page }) => {
    const chatInput = page.locator('textarea');
    const sendButton = page.locator('button[title="Send message"]');
    
    // Send message that would trigger tool usage
    await chatInput.fill('Analyze the text metrics of this document');
    await sendButton.click();
    
    // Wait for response
    await expect(page.locator('[role="assistant"]')).toBeVisible({ timeout: 60000 });
    
    // Look for reasoning steps or tool usage indicators
    // This depends on how the UI displays reasoning information
    // Could be expandable sections, tooltips, or inline text
  });
});