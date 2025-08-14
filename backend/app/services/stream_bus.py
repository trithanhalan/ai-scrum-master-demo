<file>
      <absolute_file_name>/app/backend/app/services/stream_bus.py</absolute_file_name>
      <content">import redis
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.config import settings

class RedisStreamBus:
    """Redis Streams event bus for webhook processing"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.events_stream = "events:ingress"
        self.processed_stream = "events:processed"
    
    def publish_event(self, event_type: str, source: str, payload: Dict[Any, Any]) -> str:
        """Publish event to Redis Stream"""
        event_id = str(uuid.uuid4())
        
        event_data = {
            "event_id": event_id,
            "event_type": event_type,
            "source": source,
            "payload": json.dumps(payload),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add to ingress stream
        stream_id = self.redis_client.xadd(self.events_stream, event_data)
        
        return event_id
    
    def consume_events(self, consumer_group: str, consumer_name: str, count: int = 10) -> List[Dict]:
        """Consume events from Redis Stream"""
        try:
            # Create consumer group if it doesn't exist
            try:
                self.redis_client.xgroup_create(
                    self.events_stream, consumer_group, id='0', mkstream=True
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
            
            # Read messages
            messages = self.redis_client.xreadgroup(
                consumer_group,
                consumer_name,
                {self.events_stream: '>'},
                count=count,
                block=1000  # Block for 1 second
            )
            
            events = []
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    event = {
                        'stream_id': msg_id.decode(),
                        'event_id': fields[b'event_id'].decode(),
                        'event_type': fields[b'event_type'].decode(),
                        'source': fields[b'source'].decode(),
                        'payload': json.loads(fields[b'payload'].decode()),
                        'timestamp': fields[b'timestamp'].decode()
                    }
                    events.append(event)
            
            return events
            
        except Exception as e:
            print(f"Error consuming events: {e}")
            return []
    
    def acknowledge_event(self, consumer_group: str, stream_id: str):
        """Acknowledge event processing"""
        self.redis_client.xack(self.events_stream, consumer_group, stream_id)
    
    def publish_processed_event(self, original_event_id: str, result: Dict[Any, Any]):
        """Publish processed event result"""
        processed_data = {
            "original_event_id": original_event_id,
            "result": json.dumps(result),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        self.redis_client.xadd(self.processed_stream, processed_data)
    
    def get_stream_info(self, stream_name: str) -> Dict:
        """Get Redis Stream information"""
        try:
            return self.redis_client.xinfo_stream(stream_name)
        except:
            return {}

# Global instance
stream_bus = RedisStreamBus()
</content>
    </file>