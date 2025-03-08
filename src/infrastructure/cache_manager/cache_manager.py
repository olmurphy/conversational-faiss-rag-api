import threading
import time
from collections import OrderedDict, deque
from typing import Optional

from configurations.service_model import ConfigSchema


class LRUCache:
    """
    A time-based Least Recently Used (LRU) cache with automatic expiration and thread safety.

    This cache stores k-p pairs (session IDs and chat_history) and enforces a max
    capacity. It employs an LRU eviction policy, removing the least recently accessed item
    when the capacity is exceeded. Additionally, it implements time-based expiration, where
    items older than a specified expiry_time are automatically removed.

    Key Features:
        - LRU Eviction: Maintains an OrderedDict to track item access order, ensuring that
          the least recently accessed item is evicted when the cache is full.
        - Time-Based Expiration: Uses a deque to track item insertion timestamps and a
          dedicated cleanup thread to periodically remove expired items.
        - Automatic Cleanup: A background thread executes the cleanup method at a
          configurable cleanup_interval, ensuring that expired items are removed without
          relying on get or put calls.
        - Thread Safety: Employs a threading.Lock to protect the cache's data structures
          from concurrent access, preventing race conditions and ensuring data integrity.
        - Configurable Parameters:
            - capacity: The maximum number of items the cache can hold.
            - expiry_time: The time in seconds after which an item expires.
            - cleanup_interval: The time in seconds between automatic cleanup runs.

    Complexity Analysis:
        - get(key): O(1) average case, as OrderedDict provides constant-time access.
        - put(key, value): O(1) average case, due to OrderedDict and deque operations.
        - cleanup(): O(n) in the worst case, where n is the number of items in the cache,
          as it iterates through the expiry_queue and cache to identify and remove
          expired items. However, in practice, the number of expired items is usually
          much smaller than the total number of items, resulting in better average-case
          performance.
        - _cleanup_task(): Runs periodically based on cleanup_interval, adding minimal
          overhead to the main program's execution.

    Usage:
        1.  Initialize the cache with desired capacity, expiry time, and cleanup interval.
        2.  Use put(key, value) to add or update items in the cache.
        3.  Use get(key) to retrieve items from the cache.
        4.  The cache will automatically handle LRU eviction and time-based expiration.
        5.  print_cache() is available for debugging.

    Example:
        cache = LRUCache(capacity=100, expiry_time=3600, cleanup_interval=60)
        cache.put("session1", [{"user": "Hello", "bot": "Hi"}])
        result = cache.get("session1")
        cache.print_cache()
    """

    def __init__(self, configurations: ConfigSchema):
        self.configurations = configurations

        lru_config = self.configurations.cache
        self.capacity = lru_config.capacity
        self.expiry_time = lru_config.expiry_time
        self.cache = OrderedDict()
        self.expiry_queue = deque()  # Stores (timestamp, session_id) in insertion order
        self.lock = (
            threading.Lock()
        )  # Protects cache from concurrent access avoiding race conditions
        self.cleanup_interval = (
            lru_config.cleanup_interval
        )  # time to check the cache again
        self._start_cleanup_thread()

    def get(self, key: str) -> Optional[list[dict]]:
        """
        Retrieves chat history if session is valid, else removes and returns None.

        Args:
            key: The session ID.

        Returns:
            The chat history if found and valid, otherwise None.
        """

        with self.lock:
            if key not in self.cache:
                return None

            self.cache.move_to_end(key)
            self.cache[key] = (self.cache[key][0], time.time())  # Refresh timestamp
            self.expiry_queue.append((time.time(), key))  # Update expiry tracking
            return self.cache[key][0]

    def put(self, key: str, value: list[dict]) -> None:
        """Add or update a session with a new timestamp."""

        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)

            self.cache[key] = (value, time.time())
            self.expiry_queue.append((time.time(), key))

            if len(self.cache) > self.capacity:
                self.cache.popitem(False)

    def cleanup(self) -> None:
        """Remove sessions older than expiry_time."""
        with self.lock:
            current_time = time.time()

            while self.expiry_queue and (
                current_time - self.expiry_queue[0][0] > self.expiry_time
            ):
                _, key = self.expiry_queue.popleft()  # Remove oldest entry
                self.cache.pop(key, None)  # Remove session from cache if still present

            keys_to_delete = [
                key
                for key, (_, timestamp) in self.cache.items()
                if current_time - timestamp > self.expiry_time
            ]

            for key in keys_to_delete:
                del self.cache[key]

    def print_cache(self) -> None:
        """Print the current cache contents."""
        with self.lock:
            print("-" * 50)
            print("Current LRU Cache (Time-Based):")
            for key, (value, timestamp) in self.cache.items():
                print(
                    f"Session ID: {key} | Last Accessed: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}"
                )
                for entry in value:
                    print(f"  {entry}")
            print("-" * 50)

    def _cleanup_task(self):
        """
        Periodically calls the cleanup method.
        """
        while True:
            time.sleep(self.cleanup_interval)
            self.cleanup()
            self.print_cache()

    def _start_cleanup_thread(self):
        """
        Starts the cleanup thread.
        """
        cleanup_thread = threading.Thread(
            target=self._cleanup_task, daemon=True
        )  # daemon causes thread to stop when program stops
        cleanup_thread.start()  # start thread in background


# # Example usage:
# cache = LRUCache(capacity=100) # set the capacity.
