import unittest
from unittest.mock import Mock, patch
from src.ingestion.websocket_client import BinanceWebSocketClient

class TestWebSocketClient(unittest.TestCase):
    def test_on_message(self):
        """Test xử lý message từ WebSocket"""
        callback = Mock()
        client = BinanceWebSocketClient(['btcusdt'], callback)
        
        message = '{"e": "24hrTicker", "s": "BTCUSDT", "c": "65000.00"}'
        client.on_message(None, message)
        
        callback.assert_called_once()
    
    def test_on_message_ignore_non_ticker(self):
        """Test bỏ qua message không phải ticker"""
        callback = Mock()
        client = BinanceWebSocketClient(['btcusdt'], callback)
        
        message = '{"e": "subscriptionConfirmation"}'
        client.on_message(None, message)
        
        callback.assert_not_called()

if __name__ == '__main__':
    unittest.main()