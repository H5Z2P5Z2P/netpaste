from redis.asyncio import Redis
import json
from typing import Optional, Tuple

import os

class RedisClient:
    def __init__(self):
        # Decode responses=True ensures we get strings back
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        self.client = Redis(host=host, port=port, db=0, decode_responses=True)
        
        # Lua script for atomic compare-and-swap (CAS) on token
        # KEYS[1]: note key
        # ARGV[1]: old token (to verify)
        # ARGV[2]: new data (JSON string)
        # ARGV[3]: expire time (or -1 if no change/no expire)
        # Returns: 1 if success, 0 if token mismatch, -1 if key doesn't exist (optional logic)
        self.update_script = self.client.register_script("""
            local current_data = redis.call('get', KEYS[1])
            if not current_data then
                return -1
            end
            
            local json_data = cjson.decode(current_data)
            if json_data.note_token ~= ARGV[1] then
                return 0
            end
            
            redis.call('set', KEYS[1], ARGV[2])
            
            local expire = tonumber(ARGV[3])
            if expire and expire > 0 then
                redis.call('expire', KEYS[1], expire)
            end
            
            return 1
        """)
    
    async def get_note(self, note_name: str) -> Optional[dict]:
        """获取剪贴板数据"""
        try:
            data = await self.client.get(f"note:{note_name}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def save_note(self, note_name: str, note_data: dict, expire_time: int = None) -> bool:
        """保存剪贴板数据 (Create or Force Overwrite)"""
        try:
            key = f"note:{note_name}"
            # await method call
            await self.client.set(key, json.dumps(note_data))
            
            if expire_time and expire_time > 0:
                await self.client.expire(key, expire_time)
            
            return True
        except Exception as e:
            print(f"Redis save error: {e}")
            return False

    async def update_note_atomic(self, note_name: str, old_token: str, new_data: dict, expire_time: int = None) -> Tuple[bool, str]:
        """
        Atomically update note if token matches.
        Returns: (success, error_message)
        """
        try:
            key = f"note:{note_name}"
            expire = expire_time if expire_time is not None else -1
            
            # Execute Lua script
            result = await self.update_script(keys=[key], args=[old_token, json.dumps(new_data), expire])
            
            if result == 1:
                return True, ""
            elif result == 0:
                return False, "Token has changed, please refresh"
            elif result == -1:
                return False, "Note does not exist"
            return False, "Unknown error"
            
        except Exception as e:
            print(f"Redis atomic update error: {e}")
            return False, f"System error: {str(e)}"

    async def close(self):
        await self.client.close()

redis_client = RedisClient()