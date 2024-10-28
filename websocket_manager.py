import logging
import asyncio
import json
from typing import Optional, Callable, Dict
from datetime import datetime, timedelta
import random
import ssl
from urllib.parse import urlparse, urljoin, urlunparse
import backoff
from collections import deque
import websockets
from websockets.exceptions import (
    ConnectionClosed, 
    InvalidStatusCode, 
    InvalidMessage, 
    WebSocketProtocolError,
    ConnectionClosedOK,
    ConnectionClosedError
)

logger = logging.getLogger(__name__)

class WebSocketError(Exception):
    """Custom WebSocket error"""
    pass

class WebSocketManager:
    def __init__(self, url: str, on_message: Callable, on_error: Callable):
        """Initialize WebSocket manager with URL validation"""
        self.on_message = on_message
        self.on_error = on_error
        self.websocket = None
        self.is_connected = False
        self.should_reconnect = True
        self.retry_count = 0
        self.max_retries = 10
        self.base_delay = 1.0
        self.max_delay = 60.0
        self.connection_timeout = 30
        self.last_heartbeat = None
        self.heartbeat_interval = timedelta(seconds=15)
        self.message_queue = asyncio.Queue()
        self.connection_monitor_task = None
        self.connection_lost_callbacks = []
        self.error_history = deque(maxlen=5)
        self.consecutive_errors = 0
        self.last_error_time = None
        self.connection_events = deque(maxlen=100)
        
        # Validate and set URL after other initializations
        self.url = self._validate_and_normalize_url(url)
        self.ssl_context = self._create_ssl_context() if self.use_ssl else None

    def _validate_and_normalize_url(self, url: str) -> str:
        """Validate and normalize WebSocket URL with enhanced error handling"""
        try:
            # Parse URL
            parsed = urlparse(url)
            
            # Validate scheme
            if not parsed.scheme:
                raise WebSocketError("Missing WebSocket scheme")
            if parsed.scheme not in ('ws', 'wss'):
                raise WebSocketError(f"Invalid WebSocket scheme: {parsed.scheme}")
            
            # Validate host
            if not parsed.netloc:
                raise WebSocketError("Missing WebSocket host")
            
            # Handle empty path - always ensure a path exists
            path = parsed.path if parsed.path else '/'
            
            # Store connection info
            self.use_ssl = parsed.scheme == 'wss'
            self.host = parsed.netloc
            self.port = parsed.port or (443 if self.use_ssl else 80)
            self.path = path
            
            # Normalize URL components
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc,
                path,
                parsed.params,
                parsed.query,
                parsed.fragment or ''
            ))
            
            logger.info(f"WebSocket URL validated and normalized: {normalized}")
            return normalized
            
        except WebSocketError as e:
            logger.error(f"WebSocket URL validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected URL validation error: {str(e)}")
            raise WebSocketError(f"Invalid WebSocket URL: {str(e)}")

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with enhanced security"""
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.options |= (
                ssl.OP_NO_TLSv1 | 
                ssl.OP_NO_TLSv1_1 | 
                ssl.OP_NO_COMPRESSION |
                ssl.OP_NO_RENEGOTIATION |
                ssl.OP_CIPHER_SERVER_PREFERENCE
            )
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256')
            return ssl_context
        except Exception as e:
            logger.error(f"SSL context creation failed: {str(e)}")
            raise RuntimeError(f"SSL context creation failed: {str(e)}")

    @backoff.on_exception(
        backoff.expo,
        (ConnectionClosed, ConnectionClosedOK, ConnectionClosedError,
         InvalidStatusCode, InvalidMessage, WebSocketProtocolError,
         ConnectionError, asyncio.TimeoutError, WebSocketError),
        max_tries=10,
        max_time=300
    )
    async def connect(self):
        """Connect to WebSocket with automatic reconnection"""
        if not self.connection_monitor_task:
            self.connection_monitor_task = asyncio.create_task(self._monitor_connection_health())

        while self.should_reconnect and self.retry_count < self.max_retries:
            try:
                if self.websocket and not self.websocket.closed:
                    await self.websocket.close()
                
                extra_options = {
                    'ping_interval': None,
                    'ping_timeout': None,
                    'close_timeout': 10,
                    'max_size': 10 * 1024 * 1024,
                    'compression': None,
                    'max_queue': 256,
                    'read_limit': 65536,
                    'write_limit': 65536,
                    'open_timeout': 20,
                    'extra_headers': {
                        'Connection': 'Upgrade',
                        'Upgrade': 'websocket',
                        'Host': self.host,
                        'Sec-WebSocket-Version': '13',
                        'Sec-WebSocket-Key': self._generate_websocket_key()
                    }
                }
                
                if self.use_ssl:
                    extra_options['ssl'] = self.ssl_context

                self.websocket = await websockets.connect(
                    self.url,
                    **extra_options
                )
                
                self.is_connected = True
                self.retry_count = 0
                logger.info("WebSocket connection established")
                return True
                
            except Exception as e:
                self.is_connected = False
                self.retry_count += 1
                logger.error(f"Connection attempt {self.retry_count} failed: {str(e)}")
                
                if self.retry_count < self.max_retries:
                    delay = min(
                        self.base_delay * (2 ** self.retry_count) + random.uniform(0, 1),
                        self.max_delay
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max retry attempts reached")
                    return False

    async def _monitor_connection_health(self):
        """Monitor connection health and handle reconnection"""
        while self.should_reconnect:
            try:
                if not self.is_connected or (self.websocket and self.websocket.closed):
                    logger.warning("Connection lost, initiating reconnection")
                    await self.connect()
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Health monitoring error: {str(e)}")
                await asyncio.sleep(1)

    def _generate_websocket_key(self) -> str:
        """Generate WebSocket key for handshake"""
        import base64
        import os
        return base64.b64encode(os.urandom(16)).decode()

    async def send(self, message: Dict) -> bool:
        """Send message with retry logic"""
        if not self.is_connected:
            await self.connect()
            
        try:
            if self.websocket and not self.websocket.closed:
                await self.websocket.send(json.dumps(message))
                return True
            return False
        except Exception as e:
            logger.error(f"Send error: {str(e)}")
            self.is_connected = False
            return False

    async def receive(self):
        """Receive messages with error handling"""
        while self.is_connected:
            try:
                if self.websocket and not self.websocket.closed:
                    message = await self.websocket.recv()
                    await self.on_message(json.loads(message))
            except Exception as e:
                logger.error(f"Receive error: {str(e)}")
                self.is_connected = False
                await self.connect()
            await asyncio.sleep(0.1)

    async def close(self):
        """Close connection with cleanup"""
        self.should_reconnect = False
        self.is_connected = False
        
        if self.connection_monitor_task:
            self.connection_monitor_task.cancel()
            try:
                await self.connection_monitor_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            try:
                await asyncio.wait_for(
                    self.websocket.close(),
                    timeout=5
                )
            except Exception as e:
                logger.error(f"Close error: {str(e)}")
            finally:
                self.websocket = None
