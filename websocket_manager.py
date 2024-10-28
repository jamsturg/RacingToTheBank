import logging
import asyncio
import websockets
import json
from typing import Dict, Optional, Callable
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ws = None
        self.connected = False
        self.callbacks = {}
        self.last_message = None

    async def connect(self, url: str):
        """Connect to WebSocket server"""
        try:
            self.ws = await websockets.connect(url)
            self.connected = True
            self.logger.info("Connected to WebSocket server")
            return True
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {str(e)}")
            return False

    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            self.logger.info("Disconnected from WebSocket server")

    async def send_message(self, message: Dict):
        """Send message to WebSocket server"""
        try:
            if self.connected and self.ws:
                await self.ws.send(json.dumps(message))
                self.logger.debug(f"Sent message: {message}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return False

    async def receive_message(self) -> Optional[Dict]:
        """Receive message from WebSocket server"""
        try:
            if self.connected and self.ws:
                message = await self.ws.recv()
                self.last_message = {
                    'data': json.loads(message),
                    'timestamp': datetime.now()
                }
                self.logger.debug(f"Received message: {message}")
                return self.last_message['data']
            return None
        except Exception as e:
            self.logger.error(f"Error receiving message: {str(e)}")
            return None

    def register_callback(self, event_type: str, callback: Callable):
        """Register callback for event type"""
        self.callbacks[event_type] = callback
        self.logger.debug(f"Registered callback for {event_type}")

    def unregister_callback(self, event_type: str):
        """Unregister callback for event type"""
        if event_type in self.callbacks:
            del self.callbacks[event_type]
            self.logger.debug(f"Unregistered callback for {event_type}")

    async def handle_message(self, message: Dict):
        """Handle received message"""
        try:
            event_type = message.get('type')
            if event_type in self.callbacks:
                await self.callbacks[event_type](message)
            else:
                self.logger.warning(f"No callback registered for {event_type}")
        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")

    async def start_listening(self):
        """Start listening for messages"""
        try:
            while self.connected:
                message = await self.receive_message()
                if message:
                    await self.handle_message(message)
        except Exception as e:
            self.logger.error(f"Error in message loop: {str(e)}")
            await self.disconnect()

    def get_last_message(self) -> Optional[Dict]:
        """Get last received message"""
        return self.last_message

    def is_connected(self) -> bool:
        """Check if connected to WebSocket server"""
        return self.connected

    async def reconnect(self, url: str, max_attempts: int = 3):
        """Attempt to reconnect to WebSocket server"""
        attempts = 0
        while attempts < max_attempts and not self.connected:
            self.logger.info(f"Reconnection attempt {attempts + 1}/{max_attempts}")
            if await self.connect(url):
                return True
            attempts += 1
            await asyncio.sleep(2 ** attempts)  # Exponential backoff
        return False

    async def ping(self) -> bool:
        """Send ping to check connection"""
        try:
            if self.connected and self.ws:
                await self.ws.ping()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Ping error: {str(e)}")
            return False

    def get_connection_status(self) -> Dict:
        """Get detailed connection status"""
        return {
            'connected': self.connected,
            'last_message_time': self.last_message['timestamp'] if self.last_message else None,
            'registered_callbacks': list(self.callbacks.keys())
        }
