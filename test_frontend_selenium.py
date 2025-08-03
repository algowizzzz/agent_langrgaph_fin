#!/usr/bin/env python3
"""
Frontend Selenium Test Script
Tests the AI Document Agent frontend for streaming issues
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class FrontendTester:
    def __init__(self):
        self.driver = None
        self.frontend_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8000"
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        print("🔧 Setting up Chrome driver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Uncomment next line to run headless (no browser window)
        # chrome_options.add_argument("--headless")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        print("✅ Chrome driver setup complete")
        
    def check_backend_health(self):
        """Check if backend is running"""
        print("🏥 Checking backend health...")
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is healthy")
                return True
            else:
                print(f"❌ Backend unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend not accessible: {e}")
            return False
    
    def check_frontend_accessible(self):
        """Check if frontend is accessible"""
        print("🌐 Checking frontend accessibility...")
        try:
            self.driver.get(self.frontend_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("✅ Frontend is accessible")
            return True
        except Exception as e:
            print(f"❌ Frontend not accessible: {e}")
            return False
    
    def wait_for_documents_to_load(self):
        """Wait for documents to load in sidebar"""
        print("📚 Waiting for documents to load...")
        try:
            # Wait for page to fully load first
            time.sleep(5)
            
            # Debug: Print page title and URL
            print(f"🔍 Page title: {self.driver.title}")
            print(f"🔍 Current URL: {self.driver.current_url}")
            
            # Look for any documents section
            try:
                documents_section = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Documents') or contains(text(), 'documents')]"))
                )
                print(f"✅ Found documents section: {documents_section.text}")
            except TimeoutException:
                print("⚠️  No documents section found")
            
            # Debug: Print all text content on page
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            print(f"🔍 Page contains: {page_text[:200]}...")
            
            # Look for any clickable document elements with more flexible selectors
            doc_selectors = [
                "//div[contains(@class, 'pdf')]",
                "//div[contains(@class, 'document')]", 
                "//div[contains(text(), '.pdf')]",
                "//div[contains(text(), '.txt')]",
                "//div[contains(text(), '.csv')]",
                "//div[contains(text(), 'riskandfinace')]",
                "//div[contains(text(), 'car24')]",
                "//button[contains(@class, 'document')]",
                "//*[contains(text(), 'Selected')]",
                "//*[contains(text(), 'chunks')]"
            ]
            
            documents_found = False
            for selector in doc_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"✅ Found {len(elements)} elements with selector: {selector}")
                        for i, elem in enumerate(elements[:3]):  # Show first 3
                            print(f"  📄 Element {i}: {elem.text[:50]}...")
                        documents_found = True
                        break
                except Exception as e:
                    continue
            
            if documents_found:
                print("✅ Documents loaded successfully")
                return True
            else:
                print("⚠️  No documents found, but continuing test...")
                return True  # Continue anyway for testing
                
        except Exception as e:
            print(f"❌ Error waiting for documents: {e}")
            # Continue anyway for testing
            return True
    
    def select_document(self, doc_name_partial="riskandfinace"):
        """Select a document from the sidebar"""
        print(f"📄 Trying to select document...")
        try:
            # Try multiple strategies to find and select documents
            selection_strategies = [
                f"//div[contains(text(), '{doc_name_partial}')]",
                "//div[contains(text(), '.pdf')]",
                "//div[contains(text(), '.txt')]", 
                "//div[contains(@class, 'pdf')]",
                "//div[contains(@class, 'document')]",
                "//*[contains(text(), 'riskandfinace')]",
                "//*[contains(text(), 'car24')]",
                "//button[contains(@class, 'document')]",
                "//*[@role='button'][contains(text(), '.')]"
            ]
            
            for strategy in selection_strategies:
                try:
                    doc_elements = self.driver.find_elements(By.XPATH, strategy)
                    if doc_elements:
                        print(f"🎯 Found {len(doc_elements)} documents with strategy: {strategy}")
                        for i, elem in enumerate(doc_elements[:3]):
                            print(f"  📄 Option {i}: {elem.text[:50]}...")
                        
                        # Try to click the first one
                        doc_elements[0].click()
                        print(f"✅ Selected document: {doc_elements[0].text[:50]}...")
                        time.sleep(3)  # Wait for selection to register
                        return True
                except Exception as e:
                    print(f"⚠️  Strategy {strategy} failed: {e}")
                    continue
            
            print("⚠️  No documents found to select, continuing test anyway...")
            return True  # Continue test even without document selection
                
        except Exception as e:
            print(f"❌ Error selecting document: {e}")
            return True  # Continue test anyway
    
    def submit_query(self, query="hello"):
        """Submit a query and return success status"""
        print(f"💬 Submitting query: '{query}'...")
        try:
            # Try multiple selectors for chat input
            input_selectors = [
                "//input[@placeholder='Ask me anything about your document...']",
                "//textarea[@placeholder='Ask me anything about your document...']",
                "//input[contains(@placeholder, 'Ask me')]",
                "//textarea[contains(@placeholder, 'Ask me')]",
                "//input[contains(@placeholder, 'Upload documents')]",
                "//textarea[contains(@placeholder, 'Upload documents')]",
                "//input[@data-testid='chat-message-input']",
                "//textarea[@data-testid='chat-message-input']",
                "//input[@type='text']",
                "//textarea"
            ]
            
            chat_input = None
            for selector in input_selectors:
                try:
                    chat_input = self.driver.find_element(By.XPATH, selector)
                    print(f"✅ Found input with selector: {selector}")
                    break
                except:
                    continue
            
            if not chat_input:
                print("❌ No chat input found")
                return False
            
            # Clear and type query
            chat_input.clear()
            chat_input.send_keys(query)
            print(f"✅ Typed query: '{query}'")
            
            # Try multiple selectors for submit button
            button_selectors = [
                "//button[contains(@class, 'send')]",
                "//button[contains(text(), 'Send')]",
                "//button[@type='submit']",
                "//button[@data-testid='send-message-button']",
                "//button[contains(@title, 'Send')]",
                "//button[last()]"  # Try the last button on page
            ]
            
            submit_button = None
            for selector in button_selectors:
                try:
                    submit_button = self.driver.find_element(By.XPATH, selector)
                    print(f"✅ Found button with selector: {selector}")
                    break
                except:
                    continue
            
            if not submit_button:
                # Try pressing Enter instead
                from selenium.webdriver.common.keys import Keys
                chat_input.send_keys(Keys.RETURN)
                print("✅ Pressed Enter to submit")
            else:
                submit_button.click()
                print("✅ Clicked submit button")
            
            time.sleep(2)  # Wait for submission to process
            return True
            
        except Exception as e:
            print(f"❌ Error submitting query: {e}")
            return False
    
    def monitor_reasoning_steps(self, max_wait_time=60):
        """Monitor AI reasoning steps and final response"""
        print("🧠 Monitoring AI reasoning steps...")
        
        start_time = time.time()
        reasoning_steps = []
        final_response = None
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check for reasoning steps
                step_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'reasoning') or contains(text(), '✅') or contains(text(), '⚡')]")
                
                for step in step_elements:
                    step_text = step.text.strip()
                    if step_text and step_text not in reasoning_steps:
                        reasoning_steps.append(step_text)
                        print(f"📋 Step: {step_text}")
                
                # Check for "AI is thinking..." status
                thinking_elements = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'AI is thinking')]")
                if thinking_elements:
                    print("🤔 AI is thinking...")
                
                # Check for final response (look for message bubbles that aren't reasoning steps)
                response_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'message') or contains(@class, 'response')][not(contains(@class, 'reasoning'))]")
                
                for response in response_elements:
                    response_text = response.text.strip()
                    if response_text and len(response_text) > 50 and "AI is thinking" not in response_text:
                        final_response = response_text
                        print("✅ Final response received!")
                        return True, reasoning_steps, final_response
                
                # Check for error messages
                error_elements = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'error') or contains(text(), 'Error') or contains(@class, 'error')]")
                if error_elements:
                    error_text = error_elements[0].text
                    print(f"❌ Error detected: {error_text}")
                    return False, reasoning_steps, error_text
                
                time.sleep(1)  # Wait 1 second before checking again
                
            except Exception as e:
                print(f"⚠️  Error monitoring steps: {e}")
                time.sleep(1)
        
        print(f"⏰ Timeout after {max_wait_time} seconds")
        return False, reasoning_steps, None
    
    def capture_console_logs(self):
        """Capture browser console logs for debugging"""
        print("📋 Capturing console logs...")
        try:
            logs = self.driver.get_log('browser')
            if logs:
                print("🔍 Browser Console Logs:")
                for log in logs[-10:]:  # Show last 10 logs
                    print(f"  {log['level']}: {log['message']}")
            else:
                print("✅ No console errors found")
        except Exception as e:
            print(f"⚠️  Could not capture console logs: {e}")
    
    def test_streaming_functionality(self):
        """Main test for streaming functionality"""
        print("\n🧪 TESTING STREAMING FUNCTIONALITY")
        print("=" * 50)
        
        # Test 1: Simple query
        print("\n📝 Test 1: Simple Query")
        if self.submit_query("hello"):
            success, steps, response = self.monitor_reasoning_steps(30)
            if success:
                print("✅ Simple query test PASSED")
            else:
                print("❌ Simple query test FAILED")
                self.capture_console_logs()
        
        time.sleep(5)  # Wait between tests
        
        # Test 2: Document summary
        print("\n📝 Test 2: Document Summary")
        if self.submit_query("summarize the document"):
            success, steps, response = self.monitor_reasoning_steps(60)
            if success:
                print("✅ Document summary test PASSED")
                print(f"📊 Reasoning steps captured: {len(steps)}")
            else:
                print("❌ Document summary test FAILED") 
                print(f"📊 Reasoning steps captured: {len(steps)}")
                self.capture_console_logs()
    
    def run_full_test(self):
        """Run complete frontend test"""
        print("🚀 STARTING FRONTEND SELENIUM TEST")
        print("=" * 50)
        
        try:
            # Setup
            if not self.check_backend_health():
                return False
            
            self.setup_driver()
            
            # Basic connectivity
            if not self.check_frontend_accessible():
                return False
            
            # Wait for page to fully load
            time.sleep(3)
            
            # Load documents
            if not self.wait_for_documents_to_load():
                return False
            
            # Select a document
            if not self.select_document():
                return False
            
            # Test streaming functionality
            self.test_streaming_functionality()
            
            print("\n🎉 TEST COMPLETED")
            print("=" * 50)
            
            # Keep browser open for manual inspection
            input("Press Enter to close browser and exit...")
            
        except Exception as e:
            print(f"💥 Test failed with exception: {e}")
            self.capture_console_logs()
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 Browser closed")

def main():
    tester = FrontendTester()
    tester.run_full_test()

if __name__ == "__main__":
    main()