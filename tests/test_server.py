from share import LRUCache


def test_lru_cache_basic():
    cache = LRUCache(capacity=2, timeout=3600)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
