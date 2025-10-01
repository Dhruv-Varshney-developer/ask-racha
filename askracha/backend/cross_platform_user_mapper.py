"""
Cross-platform user identification mapping for rate limiting.
Provides consistent user identification across web and Discord interfaces.
"""
import logging
import hashlib
from typing import Optional, Dict, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class UserIdentity:
    """Represents a user identity across platforms."""
    platform: str  # 'web', 'discord'
    platform_user_id: str  # Platform-specific user ID
    unified_user_id: str  # Unified user ID for rate limiting
    user_type: str = 'anonymous'  # 'authenticated', 'anonymous'


class CrossPlatformUserMapper:
    """Maps users across different platforms for consistent rate limiting."""
    
    def __init__(self):
        """Initialize the user mapper."""
        self.logger = logging.getLogger(__name__)
    
    def get_unified_user_id(self, platform: str, platform_user_id: str, user_type: str = 'anonymous') -> str:
        """
        Get unified user ID for rate limiting across platforms.
        
        Args:
            platform: Platform name ('web', 'discord')
            platform_user_id: Platform-specific user identifier
            user_type: Type of user ('authenticated', 'anonymous')
            
        Returns:
            Unified user ID for rate limiting
        """
        if user_type == 'authenticated':
            # For authenticated users, we can potentially link accounts
            # For now, keep them separate but use consistent format
            return f"auth:{platform}:{platform_user_id}"
        else:
            # For anonymous users, use platform-specific identification
            return f"anon:{platform}:{platform_user_id}"
    
    def create_web_user_identity(self, request_headers: Dict[str, str], 
                                session_data: Dict[str, Any], 
                                remote_addr: str) -> UserIdentity:
        """
        Create user identity from web request data.
        
        Args:
            request_headers: HTTP request headers
            session_data: Session data dictionary
            remote_addr: Remote IP address
            
        Returns:
            UserIdentity object
        """
        # Strategy 1: Check for authenticated user
        user_id = request_headers.get('X-User-ID')
        if user_id:
            unified_id = self.get_unified_user_id('web', user_id, 'authenticated')
            return UserIdentity(
                platform='web',
                platform_user_id=user_id,
                unified_user_id=unified_id,
                user_type='authenticated'
            )
        
        # Strategy 2: Check for session-based user ID
        if 'user_id' in session_data:
            user_id = str(session_data['user_id'])
            unified_id = self.get_unified_user_id('web', user_id, 'authenticated')
            return UserIdentity(
                platform='web',
                platform_user_id=user_id,
                unified_user_id=unified_id,
                user_type='authenticated'
            )
        
        # Strategy 3: Use IP address for anonymous users
        real_ip = (
            request_headers.get('X-Forwarded-For', '').split(',')[0].strip() or
            request_headers.get('X-Real-IP', '') or
            remote_addr or
            'unknown'
        )
        
        unified_id = self.get_unified_user_id('web', real_ip, 'anonymous')
        return UserIdentity(
            platform='web',
            platform_user_id=real_ip,
            unified_user_id=unified_id,
            user_type='anonymous'
        )
    
    def create_discord_user_identity(self, discord_user_id: str) -> UserIdentity:
        """
        Create user identity from Discord user data.
        
        Args:
            discord_user_id: Discord user ID
            
        Returns:
            UserIdentity object
        """
        # Discord users are always considered authenticated since they have Discord accounts
        unified_id = self.get_unified_user_id('discord', discord_user_id, 'authenticated')
        return UserIdentity(
            platform='discord',
            platform_user_id=discord_user_id,
            unified_user_id=unified_id,
            user_type='authenticated'
        )
    
    def can_share_rate_limit(self, identity1: UserIdentity, identity2: UserIdentity) -> bool:
        """
        Determine if two user identities should share rate limits.
        
        Args:
            identity1: First user identity
            identity2: Second user identity
            
        Returns:
            True if they should share rate limits
        """
        # For now, keep platform-specific rate limits
        # In the future, this could be enhanced to link authenticated accounts
        return identity1.unified_user_id == identity2.unified_user_id
    
    def get_rate_limit_key(self, identity: UserIdentity) -> str:
        """
        Get the rate limit key for a user identity.
        
        Args:
            identity: User identity
            
        Returns:
            Rate limit key for Redis
        """
        return identity.unified_user_id


# Global mapper instance
_user_mapper: Optional[CrossPlatformUserMapper] = None


def get_user_mapper() -> CrossPlatformUserMapper:
    """Get global user mapper instance (singleton pattern)."""
    global _user_mapper
    if _user_mapper is None:
        _user_mapper = CrossPlatformUserMapper()
    return _user_mapper