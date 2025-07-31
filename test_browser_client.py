"""
Test script for the TriAI browser client functionality.
"""

import requests
import time
from bs4 import BeautifulSoup


class BrowserClientTester:
    """Test the browser client interface."""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.results = {}
        
    def test_static_file_serving(self):
        """Test that all static files are served correctly."""
        print("=" * 50)
        print("TESTING STATIC FILE SERVING")
        print("=" * 50)
        
        files_to_test = [
            ('/', 'HTML'),
            ('/styles.css', 'CSS'),
            ('/app.js', 'JavaScript')
        ]
        
        for path, file_type in files_to_test:
            try:
                response = requests.get(f"{self.base_url}{path}")
                
                if response.status_code == 200:
                    print(f"✅ {file_type} file ({path}): {len(response.content)} bytes")
                    self.results[f"{file_type} File Serving"] = True
                else:
                    print(f"❌ {file_type} file ({path}): Status {response.status_code}")
                    self.results[f"{file_type} File Serving"] = False
                    
            except Exception as e:
                print(f"❌ {file_type} file ({path}): {e}")
                self.results[f"{file_type} File Serving"] = False
    
    def test_html_structure(self):
        """Test that HTML contains required elements."""
        print("\n" + "=" * 50)
        print("TESTING HTML STRUCTURE")
        print("=" * 50)
        
        try:
            response = requests.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check for key elements
            elements_to_check = [
                ('agent-select', 'Agent selection dropdown'),
                ('current-user', 'Current user display'),
                ('chat-messages', 'Chat messages container'),
                ('message-input', 'Message input field'),
                ('send-button', 'Send button'),
                ('memory-panel', 'Memory panel'),
                ('results-section', 'Results section')
            ]
            
            for element_id, description in elements_to_check:
                element = soup.find(id=element_id)
                if element:
                    print(f"✅ {description}: Found")
                    self.results[f"HTML Element: {element_id}"] = True
                else:
                    print(f"❌ {description}: Missing")
                    self.results[f"HTML Element: {element_id}"] = False
                    
            # Check for CSS and JS links
            css_link = soup.find('link', {'href': 'styles.css'})
            js_script = soup.find('script', {'src': 'app.js'})
            
            if css_link:
                print("✅ CSS stylesheet: Linked")
                self.results["CSS Link"] = True
            else:
                print("❌ CSS stylesheet: Not found")
                self.results["CSS Link"] = False
                
            if js_script:
                print("✅ JavaScript file: Linked")
                self.results["JS Link"] = True
            else:
                print("❌ JavaScript file: Not found")
                self.results["JS Link"] = False
                
        except Exception as e:
            print(f"❌ HTML structure test failed: {e}")
            
    def test_api_endpoints_from_browser_perspective(self):
        """Test API endpoints that the browser client will use."""
        print("\n" + "=" * 50)
        print("TESTING API ENDPOINTS FOR BROWSER")
        print("=" * 50)
        
        # Test user endpoint
        try:
            response = requests.get(f"{self.base_url}/api/user")
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ User API: {user_data.get('username')}")
                self.results["User API"] = True
            else:
                print(f"❌ User API: Status {response.status_code}")
                self.results["User API"] = False
        except Exception as e:
            print(f"❌ User API: {e}")
            self.results["User API"] = False
            
        # Test agents endpoint
        try:
            response = requests.get(f"{self.base_url}/api/agents")
            if response.status_code == 200:
                agents = response.json()
                print(f"✅ Agents API: {len(agents)} agents available")
                for agent in agents:
                    print(f"   - {agent['agent']}: {agent['description']}")
                self.results["Agents API"] = True
            else:
                print(f"❌ Agents API: Status {response.status_code}")
                self.results["Agents API"] = False
        except Exception as e:
            print(f"❌ Agents API: {e}")
            self.results["Agents API"] = False
            
        # Test message sending
        try:
            message_data = {
                "user_to": "DataAnalyst",
                "message": "Test message from browser client tester"
            }
            response = requests.post(
                f"{self.base_url}/api/message",
                json=message_data,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("✅ Message API: Send message successful")
                    self.results["Message Send API"] = True
                else:
                    print(f"❌ Message API: {result}")
                    self.results["Message Send API"] = False
            else:
                print(f"❌ Message API: Status {response.status_code}")
                self.results["Message Send API"] = False
        except Exception as e:
            print(f"❌ Message API: {e}")
            self.results["Message Send API"] = False
            
        # Test message retrieval
        try:
            response = requests.get(f"{self.base_url}/api/messages/DataAnalyst")
            if response.status_code == 200:
                messages = response.json()
                print(f"✅ Messages API: Retrieved {len(messages)} messages")
                self.results["Messages Retrieve API"] = True
            else:
                print(f"❌ Messages API: Status {response.status_code}")
                self.results["Messages Retrieve API"] = False
        except Exception as e:
            print(f"❌ Messages API: {e}")  
            self.results["Messages Retrieve API"] = False
    
    def test_css_styles(self):
        """Test that CSS contains key styles."""
        print("\n" + "=" * 50)
        print("TESTING CSS STYLES")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/styles.css")
            css_content = response.text
            
            # Check for key CSS classes/selectors
            css_checks = [
                ('.container', 'Main container'),
                ('.header', 'Header styles'),
                ('.agent-panel', 'Agent selection panel'),
                ('.chat-section', 'Chat interface'),
                ('.message', 'Message styling'),
                ('.btn-primary', 'Primary button'),
                (':root', 'CSS variables'),
                ('@media', 'Responsive design')
            ]
            
            for selector, description in css_checks:
                if selector in css_content:
                    print(f"✅ {description}: Found")
                    self.results[f"CSS: {selector}"] = True
                else:
                    print(f"❌ {description}: Not found")
                    self.results[f"CSS: {selector}"] = False
                    
            # Check for blue theme colors
            blue_colors = ['#2c5aa0', '#4a90e2', '#e7f3ff', '#f0f8ff']
            blue_found = any(color in css_content for color in blue_colors)
            
            if blue_found:
                print("✅ Blue theme colors: Found")
                self.results["Blue Theme"] = True
            else:
                print("❌ Blue theme colors: Not found")
                self.results["Blue Theme"] = False
                
        except Exception as e:
            print(f"❌ CSS test failed: {e}")
    
    def test_javascript_structure(self):
        """Test that JavaScript contains key functionality."""
        print("\n" + "=" * 50)
        print("TESTING JAVASCRIPT STRUCTURE")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/app.js")
            js_content = response.text
            
            # Check for key JavaScript components
            js_checks = [
                ('class TriAIClient', 'Main client class'),
                ('async apiCall', 'API communication'),
                ('loadAgents', 'Agent loading'),
                ('sendMessage', 'Message sending'),
                ('displayMessages', 'Message display'),
                ('setupEventListeners', 'Event handling'),
                ('addEventListener', 'Event listeners'),
                ('createDataTable', 'Table creation'),
                ('formatTime', 'Time formatting')
            ]
            
            for pattern, description in js_checks:
                if pattern in js_content:
                    print(f"✅ {description}: Found")
                    self.results[f"JS: {pattern}"] = True
                else:
                    print(f"❌ {description}: Not found") 
                    self.results[f"JS: {pattern}"] = False
                    
        except Exception as e:
            print(f"❌ JavaScript test failed: {e}")
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("BROWSER CLIENT TEST RESULTS SUMMARY")
        print("=" * 60)
        
        categories = {
            "Static Files": [k for k in self.results.keys() if "File Serving" in k or "Link" in k],
            "HTML Structure": [k for k in self.results.keys() if "HTML Element" in k],
            "API Integration": [k for k in self.results.keys() if "API" in k],
            "Styling": [k for k in self.results.keys() if "CSS" in k or "Blue Theme" in k],
            "JavaScript": [k for k in self.results.keys() if "JS:" in k]
        }
        
        total_passed = 0
        total_tests = 0
        
        for category, tests in categories.items():
            if not tests:
                continue
                
            category_passed = sum(1 for test in tests if self.results.get(test, False))
            category_total = len(tests)
            
            print(f"\n{category}:")
            print("-" * 40)
            
            for test in tests:
                result = self.results.get(test, False)
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {test:.<30} {status}")
                
            print(f"  Category Score: {category_passed}/{category_total}")
            total_passed += category_passed
            total_tests += category_total
        
        print("\n" + "=" * 60)
        print(f"OVERALL RESULTS: {total_passed}/{total_tests} tests passed")
        
        if total_passed == total_tests:
            print("🎉 ALL BROWSER CLIENT TESTS PASSED! Ready for use.")
        elif total_passed / total_tests >= 0.8:
            print("✅ Browser client is mostly functional.")
        else:
            print("⚠️ Browser client needs attention.")
            
        print("=" * 60)
        print("🌐 Open http://localhost:8080 in your browser to test the interface!")
        print("=" * 60)


def main():
    """Run all browser client tests."""
    tester = BrowserClientTester()
    
    tester.test_static_file_serving()
    tester.test_html_structure()
    tester.test_api_endpoints_from_browser_perspective()
    tester.test_css_styles()
    tester.test_javascript_structure()
    tester.print_summary()


if __name__ == "__main__":
    main()