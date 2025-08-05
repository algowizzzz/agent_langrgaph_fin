import { test, expect } from '@playwright/test';

test.describe('Manual Test Replication', () => {

  test('should replicate exact manual workflow: upload PDF and count word risk', async ({ page }) => {
    // Enhanced logging to capture all browser activity
    page.on('console', msg => console.log('BROWSER:', msg.text()));
    
    // Track network activity for debugging
    const requests = [];
    const responses = [];
    
    page.on('request', request => {
      if (request.url().includes('/upload') || request.url().includes('/chat')) {
        const body = request.postData();
        requests.push({
          method: request.method(),
          url: request.url(),
          headers: request.headers(),
          body: body
        });
        console.log(`📤 REQUEST: ${request.method()} ${request.url()}`);
        if (request.url().includes('/chat') && body) {
          console.log(`📋 CHAT REQUEST BODY: ${body}`);
        }
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/upload') || response.url().includes('/chat')) {
        try {
          const body = await response.text();
          responses.push({
            status: response.status(),
            url: response.url(),
            headers: response.headers(),
            body: body
          });
          console.log(`📥 RESPONSE: ${response.status()} ${response.url()}`);
          if (response.url().includes('/chat')) {
            console.log(`💬 CHAT RESPONSE BODY: ${body}`);
          } else {
            console.log(`📄 BODY: ${body.substring(0, 400)}...`);
          }
        } catch (e) {
          console.log('❌ Could not read response body:', e.message);
        }
      }
    });

    console.log('🚀 === STEP 1: Navigate to application ===');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    console.log('✅ Application loaded');

    console.log('📁 === STEP 2: Upload riskandfinace.pdf ===');
    const fileInput = page.locator('[data-testid="chat-upload-input"]');
    const testFilePath = '/Users/saadahmed/Desktop/Apps/AWS_Extra/Agent/testing_31Jul/test_files/riskandfinace.pdf';
    
    // Verify file exists before uploading
    console.log(`📂 Uploading file: ${testFilePath}`);
    await fileInput.setInputFiles(testFilePath);
    console.log('✅ File input set');

    console.log('⏳ === STEP 3: Wait for upload success ===');
    const successMessage = page.locator('[data-testid="upload-success-message"]');
    await expect(successMessage).toBeVisible({ timeout: 20000 });
    
    // Verify the document state in frontend
    await expect(successMessage).toContainText('riskandfinace.pdf');
    console.log('✅ Upload success message visible');

    // CRITICAL: Verify document is properly set as active in the store
    // This is where previous tests might have failed
    console.log('🔍 === STEP 3.5: Verify document state ===');
    
    // Add verbose logging about the upload response
    const lastUploadResponse = responses.filter(r => r.url.includes('/upload')).pop();
    if (lastUploadResponse) {
      console.log('📊 Upload response details:', JSON.stringify(JSON.parse(lastUploadResponse.body), null, 2));
    }
    
    // Use more specific selector to avoid ambiguity - target the document list item
    const documentIndicator = page.locator('p.text-sm.font-medium.text-neutral-800.truncate.mt-1', { hasText: 'riskandfinace.pdf' });
    await expect(documentIndicator).toBeVisible();
    console.log('✅ Document visible in document list');
    
    // Additional check: Verify the document shows as active/selected
    const documentSection = page.locator('[class*="document"]', { hasText: 'riskandfinace.pdf' });
    if (await documentSection.isVisible()) {
      console.log('✅ Document section found in UI');
    } else {
      console.log('⚠️ Document section not visible - checking all document elements');
      const allDocs = await page.locator('text=riskandfinace.pdf').all();
      console.log(`📋 Found ${allDocs.length} elements containing filename`);
    }

    // Wait a moment for frontend state to fully update
    await page.waitForTimeout(1000);
    console.log('⏱️ Waited for frontend state update');

    console.log('💬 === STEP 4: Type exact query from manual test ===');
    const chatInput = page.locator('[data-testid="chat-message-input"]');
    
    // Ensure input is ready
    await expect(chatInput).toBeVisible();
    await chatInput.click();
    await chatInput.fill('count of word risk');
    console.log('✅ Query typed: "count of word risk"');
    
    console.log('📨 === STEP 5: Send message ===');
    const sendButton = page.locator('[data-testid="send-message-button"]');
    await expect(sendButton).toBeEnabled();
    await sendButton.click();
    console.log('✅ Message sent');

    console.log('👤 === STEP 6: Verify user message appears ===');
    const userMessage = page.locator('[data-testid="chat-message"]').filter({ hasText: 'count of word risk' });
    await expect(userMessage).toBeVisible({ timeout: 5000 });
    console.log('✅ User message visible in chat');

    console.log('🤖 === STEP 7: Wait for assistant response ===');
    
    // Debug: Check all chat messages currently on the page
    const allMessages = await page.locator('[data-testid="chat-message"]').all();
    console.log(`📊 Found ${allMessages.length} total chat messages on page`);
    
    for (let i = 0; i < allMessages.length; i++) {
      const messageText = await allMessages[i].textContent();
      console.log(`📝 Message ${i + 1}: ${messageText?.substring(0, 100)}...`);
    }
    
    // First, let's wait and see if any assistant message appears at all
    console.log('⏳ Waiting for any assistant response...');
    const anyAssistantMessage = page.locator('[data-testid="chat-message"]').filter({ hasText: /Based on|analysis|word|times|sorry|error|I/i });
    
    try {
      await expect(anyAssistantMessage).toBeVisible({ timeout: 30000 });
      const responseText = await anyAssistantMessage.textContent();
      console.log('📝 Got assistant response:', responseText?.substring(0, 300) + '...');
      
      // Check if it contains our expected "12 times"
      if (responseText?.includes('12 times')) {
        console.log('✅ Found expected "12 times" in response');
      } else {
        console.log('⚠️ Response does not contain "12 times" - checking content');
        console.log('📄 Full response text:', responseText);
      }
    } catch (error) {
      console.log('❌ No assistant response received within timeout');
      
      // Debug: Check what chat requests were made
      const chatRequests = requests.filter(r => r.url.includes('/chat'));
      const chatResponses = responses.filter(r => r.url.includes('/chat'));
      
      console.log(`📊 Chat debug: ${chatRequests.length} requests, ${chatResponses.length} responses`);
      
      if (chatResponses.length > 0) {
        const lastChatResponse = chatResponses[chatResponses.length - 1];
        console.log('📥 Last chat response:', lastChatResponse.body.substring(0, 500) + '...');
      }
      
      throw error;
    }

    console.log('🔍 === STEP 8: Verify response content ===');
    const finalResponseText = await anyAssistantMessage.textContent();
    console.log(`📝 Final response text: ${finalResponseText?.substring(0, 200)}...`);
    
    expect(finalResponseText).toContain('12 times');
    expect(finalResponseText).toContain('risk');
    console.log('✅ Response content verified');

    // Additional verification - check for reasoning steps
    const reasoningSection = page.locator('[data-testid="chat-message"]').filter({ hasText: 'Show AI reasoning' });
    if (await reasoningSection.isVisible()) {
      console.log('✅ AI reasoning section found');
    }

    console.log('\n📊 === FINAL DEBUG INFO ===');
    console.log(`📤 Total requests made: ${requests.length}`);
    console.log(`📥 Total responses received: ${responses.length}`);
    
    // Log all requests and responses for debugging
    requests.forEach((req, i) => {
      console.log(`Request ${i + 1}: ${req.method} ${req.url}`);
    });
    
    responses.forEach((resp, i) => {
      console.log(`Response ${i + 1}: ${resp.status} ${resp.url}`);
    });

    // Verify we got the expected network activity
    const uploadRequests = requests.filter(r => r.url.includes('/upload'));
    const chatRequests = requests.filter(r => r.url.includes('/chat'));
    const uploadResponses = responses.filter(r => r.url.includes('/upload'));
    const chatResponses = responses.filter(r => r.url.includes('/chat'));

    expect(uploadRequests.length).toBeGreaterThan(0);
    expect(chatRequests.length).toBeGreaterThan(0);
    expect(uploadResponses.length).toBeGreaterThan(0);
    expect(chatResponses.length).toBeGreaterThan(0);

    console.log('🎉 TEST COMPLETED SUCCESSFULLY - Manual workflow replicated!');
    console.log('📋 Summary:');
    console.log(`   - File uploaded: riskandfinace.pdf`);
    console.log(`   - Query sent: "count of word risk"`);
    console.log(`   - Response received: Contains "12 times"`);
    console.log(`   - Network requests: ${requests.length} made, ${responses.length} received`);
  });

});