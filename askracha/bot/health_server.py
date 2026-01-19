"""
Simple HTTP health check server for cloud deployments.
Runs alongside the Discord bot to satisfy platform health check requirements.
"""
import asyncio
import logging
from aiohttp import web

logger = logging.getLogger(__name__)


class HealthCheckServer:
    """Lightweight HTTP server for health checks."""
    
    def __init__(self, port: int = 8000):
        """
        Initialize health check server.
        
        Args:
            port: Port to listen on (default: 8000)
        """
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        
        # Setup routes
        self.app.router.add_get('/', self.health_check)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/healthz', self.health_check)
        self.app.router.add_get('/ping', self.health_check)
    
    async def health_check(self, request):
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'service': 'askracha-discord-bot',
            'message': 'Bot is running'
        })
    
    async def start(self):
        """Start the health check server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()
            logger.info(f"Health check server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
            raise
    
    async def stop(self):
        """Stop the health check server."""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            logger.info("Health check server stopped")
        except Exception as e:
            logger.error(f"Error stopping health check server: {e}")
