"""
Graph Cache

Caches compiled graphs to improve performance by avoiding rebuilding on every execution.
"""

import logging
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class GraphCache:
    """
    Caches compiled graphs with TTL and invalidation support.
    """

    def __init__(self, ttl_minutes: int = 30, max_size: int = 100):
        """
        Initialize graph cache.

        Args:
            ttl_minutes: Time to live for cached graphs in minutes
            max_size: Maximum number of graphs to cache
        """
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_size = max_size
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.lock = Lock()

    def get_cache_key(self, graph_id: str, nodes_hash: str, edges_hash: str) -> str:
        """
        Generate cache key for a graph configuration.

        Args:
            graph_id: Graph ID
            nodes_hash: Hash of nodes configuration
            edges_hash: Hash of edges configuration

        Returns:
            str: Cache key
        """
        combined = f"{graph_id}:{nodes_hash}:{edges_hash}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get_nodes_hash(self, nodes: list) -> str:
        """
        Generate hash for nodes configuration.

        Args:
            nodes: List of graph nodes

        Returns:
            str: Hash of nodes configuration
        """
        # Create a deterministic string representation of nodes
        nodes_data = []
        for node in nodes:
            node_data = {
                "id": node.node_id,
                "type": node.node_type,
                "config": node.configuration or {},
                "position": getattr(node, "position", None),
            }
            nodes_data.append(str(sorted(node_data.items())))

        combined = "|".join(sorted(nodes_data))
        return hashlib.md5(combined.encode()).hexdigest()

    def get_edges_hash(self, edges: list) -> str:
        """
        Generate hash for edges configuration.

        Args:
            edges: List of graph edges

        Returns:
            str: Hash of edges configuration
        """
        # Create a deterministic string representation of edges
        edges_data = []
        for edge in edges:
            edge_data = {
                "from": edge.from_node_id,
                "to": edge.to_node_id,
                "type": edge.condition_type,
                "config": edge.condition_config or {},
            }
            edges_data.append(str(sorted(edge_data.items())))

        combined = "|".join(sorted(edges_data))
        return hashlib.md5(combined.encode()).hexdigest()

    def get(self, cache_key: str) -> Optional[Any]:
        """
        Get cached graph if it exists and is not expired.

        Args:
            cache_key: Cache key

        Returns:
            Optional[Any]: Cached graph or None
        """
        with self.lock:
            if cache_key not in self.cache:
                return None

            graph, cached_at = self.cache[cache_key]

            # Check if expired
            if datetime.utcnow() - cached_at > self.ttl:
                del self.cache[cache_key]
                logger.debug(f"Cache expired for key: {cache_key}")
                return None

            logger.debug(f"Cache hit for key: {cache_key}")
            return graph

    def put(self, cache_key: str, graph: Any) -> None:
        """
        Cache a compiled graph.

        Args:
            cache_key: Cache key
            graph: Compiled graph to cache
        """
        with self.lock:
            # Implement LRU eviction if cache is full
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
                logger.debug(f"Evicted cache entry: {oldest_key}")

            self.cache[cache_key] = (graph, datetime.utcnow())
            logger.debug(f"Cached graph with key: {cache_key}")

    def invalidate(self, cache_key: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            cache_key: Cache key to invalidate

        Returns:
            bool: True if entry was found and removed
        """
        with self.lock:
            if cache_key in self.cache:
                del self.cache[cache_key]
                logger.debug(f"Invalidated cache entry: {cache_key}")
                return True
            return False

    def invalidate_all(self) -> None:
        """
        Clear all cache entries.
        """
        with self.lock:
            self.cache.clear()
            logger.debug("Cleared all cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict[str, Any]: Cache statistics
        """
        with self.lock:
            now = datetime.utcnow()
            expired_count = sum(
                1 for _, cached_at in self.cache.values() if now - cached_at > self.ttl
            )

            return {
                "total_entries": len(self.cache),
                "expired_entries": expired_count,
                "active_entries": len(self.cache) - expired_count,
                "max_size": self.max_size,
                "ttl_minutes": self.ttl.total_seconds() / 60,
            }

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            int: Number of entries removed
        """
        with self.lock:
            now = datetime.utcnow()
            expired_keys = [
                key
                for key, (_, cached_at) in self.cache.items()
                if now - cached_at > self.ttl
            ]

            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

            return len(expired_keys)
