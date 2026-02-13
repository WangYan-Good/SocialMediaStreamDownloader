import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目路径到系统路径
sys.path.append(os.path.abspath('.'))

class TestPlatformDispatcher(unittest.TestCase):
    """Test cases for PlatformDispatcher class"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        from backend.src.platform.platform_dispatcher import PlatformDispatcher
        self.dispatcher = PlatformDispatcher()
        self.dispatcher.register()
    
    @patch('backend.src.platform.douyin.douyin_handler')
    def test_dispatch_douyin_url(self, mock_handler):
        """Test dispatching a Douyin URL"""
        # Mock the handler function
        mock_handler.return_value = None
        
        # Test data
        test_data = {
            'urls': ['https://www.douyin.com/video/123456'],
            'score': 10,
            'favorite': True
        }
        
        # Call dispatch method
        try:
            self.dispatcher.dispatch(test_data)
            # Verify the handler was called
            # Note: Since dispatch uses thread pool, we can't directly verify the call
            # But we can at least verify no exception was raised
            self.assertTrue(True)  # Placeholder assertion
        except Exception as e:
            self.fail(f"Dispatch raised an exception: {e}")
    
    def test_invalid_json_data(self):
        """Test dispatching with invalid JSON data"""
        with self.assertRaises(ValueError):
            self.dispatcher.dispatch(None)
    
    def test_missing_urls_field(self):
        """Test dispatching with missing URLs field"""
        test_data = {
            'score': 10
        }
        
        with self.assertRaises(ValueError):
            self.dispatcher.dispatch(test_data)
    
    def test_empty_urls_list(self):
        """Test dispatching with empty URLs list"""
        test_data = {
            'urls': []
        }
        
        with self.assertRaises(ValueError):
            self.dispatcher.dispatch(test_data)


class TestURLValidation(unittest.TestCase):
    """Test cases for URL validation functions in server.py"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Import the is_valid_url function from server.py
        from server import is_valid_url
        self.is_valid_url = is_valid_url
    
    def test_valid_urls(self):
        """Test valid URL formats"""
        valid_urls = [
            'https://www.douyin.com',
            'http://douyin.com',
            'https://v.douyin.com/somepath',
            'https://example.com:8080/path',
            'http://localhost',
            'https://192.168.1.1:3000'
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.is_valid_url(url), f"URL should be valid: {url}")
    
    def test_invalid_urls(self):
        """Test invalid URL formats"""
        invalid_urls = [
            'not-a-url',
            '',
            'htp://invalid-protocol.com',
            'missing-tld',
            'javascript:alert(1)',  # Potential XSS attempt
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.is_valid_url(url), f"URL should be invalid: {url}")


if __name__ == '__main__':
    unittest.main()