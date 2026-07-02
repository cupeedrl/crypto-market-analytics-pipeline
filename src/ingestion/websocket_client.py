import json
import websocket
from typing import Callable, List

class BinanceWebSocketClient:
    """Client kết nối Binance WebSocket"""
    
    def __init__(self, symbols: List[str], callback: Callable):
        """
        Khởi tạo WebSocket client
        
        Args:
            symbols: List symbols cần subscribe (ví dụ: ['btcusdt', 'ethusdt'])
            callback: Function được gọi khi nhận message
        """
        self.symbols = symbols
        self.callback = callback
        self.ws = None
    
    def on_message(self, ws, message):
        """Xử lý message nhận được"""
        data = json.loads(message)
        if 'e' in data and data['e'] == '24hrTicker':
            self.callback(data)
    
    def on_error(self, ws, error):
        """Xử lý lỗi"""
        print(f"WebSocket Error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Xử lý khi đóng connection"""
        print("### WebSocket Closed ###")
    
    def on_open(self, ws):
        """Xử lý khi mở connection - subscribe symbols"""
        print("### WebSocket Opened ###")
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params": [f"{symbol}@ticker" for symbol in self.symbols],
            "id": 1
        }
        ws.send(json.dumps(subscribe_message))
    
    def start(self):
        """Bắt đầu kết nối WebSocket"""
        self.ws = websocket.WebSocketApp(
            "wss://stream.binance.com:9443/ws",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever()
    
    def stop(self):
        """Dừng kết nối WebSocket"""
        if self.ws:
            self.ws.close()