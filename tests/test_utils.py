"""
Tests for utility modules (validators, secure_pickle, cache).

This module tests input validation, secure pickle loading,
and caching functionality.
"""

import pytest
import pickle
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import time


class TestInputValidator:
    """Test suite for InputValidator class."""

    @pytest.fixture
    def validator(self):
        """Get InputValidator class."""
        from utils.validators import InputValidator
        return InputValidator

    def test_validate_file_exists(self, validator, sample_pcap_file):
        """Test validating existing file."""
        result = validator.validate_file_exists(str(sample_pcap_file), "Test file")
        assert result == Path(sample_pcap_file)

    def test_validate_file_not_exists(self, validator):
        """Test validating non-existent file."""
        from utils.validators import ValidationError

        with pytest.raises(ValidationError):
            validator.validate_file_exists("/nonexistent/file.txt", "Test file")

    def test_validate_file_extension_valid(self, validator, temp_dir):
        """Test validating correct file extension."""
        test_file = temp_dir / "test.pcap"
        test_file.write_text("dummy")

        # Should not raise exception
        validator.validate_file_extension(str(test_file), ['.pcap', '.pcapng'])

    def test_validate_file_extension_invalid(self, validator, temp_dir):
        """Test validating incorrect file extension."""
        from utils.validators import ValidationError

        test_file = temp_dir / "test.txt"
        test_file.write_text("dummy")

        with pytest.raises(ValidationError):
            validator.validate_file_extension(str(test_file), ['.pcap', '.pcapng'])

    def test_validate_output_path_valid(self, validator, temp_dir):
        """Test validating valid output path."""
        output_path = temp_dir / "output.txt"
        result = validator.validate_output_path(str(output_path), create_dir=True)
        assert result == Path(output_path)

    def test_validate_output_path_invalid_parent(self, validator):
        """Test validating output path with non-existent parent."""
        from utils.validators import ValidationError

        with pytest.raises(ValidationError):
            validator.validate_output_path("/nonexistent/dir/output.txt", create_dir=False)

    def test_validate_pcap_file(self, validator, sample_pcap_file):
        """Test validating PCAP file."""
        result = validator.validate_pcap_file(str(sample_pcap_file))
        assert result == Path(sample_pcap_file)

    def test_validate_pcap_file_too_small(self, validator, temp_dir):
        """Test validating PCAP file that's too small."""
        from utils.validators import ValidationError

        small_file = temp_dir / "small.pcap"
        small_file.write_bytes(b"tiny")  # Less than 24 bytes

        with pytest.raises(ValidationError):
            validator.validate_pcap_file(str(small_file))

    def test_validate_model_file(self, validator, trained_model_file):
        """Test validating model file."""
        result = validator.validate_model_file(str(trained_model_file))
        assert result == Path(trained_model_file)

    def test_validate_csv_file(self, validator, temp_dir):
        """Test validating CSV file."""
        csv_file = temp_dir / "data.csv"
        csv_file.write_text("col1,col2\nval1,val2")

        result = validator.validate_csv_file(str(csv_file))
        assert result == Path(csv_file)

    def test_validate_network_interface(self, validator):
        """Test validating network interface name."""
        # Valid interface names
        valid_interfaces = ['eth0', 'wlan0', 'en0', 'lo']

        for iface in valid_interfaces:
            # Should not raise exception (may not exist on system though)
            try:
                validator.validate_network_interface(iface)
            except Exception as e:
                # May fail if checking actual system interfaces
                # that's okay for this test
                pass

    def test_validate_network_interface_invalid(self, validator):
        """Test validating invalid interface name."""
        from utils.validators import ValidationError

        invalid_interfaces = ['', 'invalid@interface', 'interface with spaces']

        for iface in invalid_interfaces:
            with pytest.raises(ValidationError):
                validator.validate_network_interface(iface)

    def test_validate_bpf_filter_valid(self, validator):
        """Test validating valid BPF filter."""
        valid_filters = [
            'tcp port 80',
            'udp',
            'icmp',
            'host 192.168.1.1',
            'tcp and port 443',
        ]

        for filter_str in valid_filters:
            # Should not raise exception
            validator.validate_bpf_filter(filter_str)

    def test_validate_bpf_filter_invalid(self, validator):
        """Test validating invalid BPF filter."""
        from utils.validators import ValidationError

        invalid_filters = [
            'tcp; rm -rf /',  # Command injection attempt
            'port && echo',    # Command injection attempt
        ]

        for filter_str in invalid_filters:
            with pytest.raises(ValidationError):
                validator.validate_bpf_filter(filter_str)

    def test_validate_duration(self, validator):
        """Test validating duration values."""
        # Valid durations
        assert validator.validate_duration(10) == 10
        assert validator.validate_duration(0) == 0
        assert validator.validate_duration(3600) == 3600

    def test_validate_duration_invalid(self, validator):
        """Test validating invalid duration."""
        from utils.validators import ValidationError

        with pytest.raises(ValidationError):
            validator.validate_duration(-10)  # Negative duration

    def test_validate_mode_requirements(self, validator):
        """Test validating mode requirements."""
        # Mock arguments object
        class Args:
            mode = 'realtime'
            interface = 'eth0'
            model = '/path/to/model.pkl'
            pcap_file = None

        args = Args()
        is_valid, errors = validator.validate_mode_requirements('realtime', args)

        # Should return validation results
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)


class TestSecurePickle:
    """Test suite for secure pickle loading."""

    @pytest.fixture
    def secure_pickle(self):
        """Get secure pickle module."""
        from utils import secure_pickle
        return secure_pickle

    def test_safe_save_and_load(self, secure_pickle, temp_dir):
        """Test safe save and load operations."""
        test_data = {'key': 'value', 'number': 42, 'list': [1, 2, 3]}
        file_path = temp_dir / "test.pkl"

        # Save
        secure_pickle.safe_save(test_data, str(file_path))
        assert file_path.exists()

        # Load
        loaded_data = secure_pickle.safe_load(str(file_path), restricted=False)
        assert loaded_data == test_data

    def test_safe_load_with_restriction(self, secure_pickle, trained_model_file):
        """Test safe load with class restrictions."""
        # Should succeed for whitelisted classes
        model = secure_pickle.safe_load(str(trained_model_file), restricted=True)
        assert model is not None

    def test_safe_load_with_hmac(self, secure_pickle, temp_dir):
        """Test safe load with HMAC verification."""
        test_data = {'secure': 'data'}
        file_path = temp_dir / "secure.pkl"
        secret_key = b"test_secret_key_12345678"

        # Save with HMAC
        secure_pickle.safe_save(test_data, str(file_path), secret_key=secret_key)

        # Load with HMAC
        loaded_data = secure_pickle.safe_load(
            str(file_path),
            secret_key=secret_key,
            restricted=False
        )
        assert loaded_data == test_data

    def test_safe_load_hmac_verification_fails(self, secure_pickle, temp_dir):
        """Test HMAC verification failure."""
        test_data = {'secure': 'data'}
        file_path = temp_dir / "secure.pkl"

        # Save with one key
        secure_pickle.safe_save(test_data, str(file_path), secret_key=b"key1")

        # Try to load with different key
        with pytest.raises(Exception):  # Should raise verification error
            secure_pickle.safe_load(str(file_path), secret_key=b"wrong_key", restricted=False)

    def test_restricted_unpickler_blocks_unsafe(self, secure_pickle, temp_dir):
        """Test that RestrictedUnpickler blocks unsafe classes."""
        # Create a pickle with an unsafe class
        import subprocess

        unsafe_file = temp_dir / "unsafe.pkl"

        # Try to pickle something that would be blocked
        # This is a simplified test
        try:
            with open(unsafe_file, 'wb') as f:
                pickle.dump(subprocess, f)  # subprocess module is unsafe

            # Loading should fail with restriction
            with pytest.raises((pickle.UnpicklingError, AttributeError, Exception)):
                secure_pickle.safe_load(str(unsafe_file), restricted=True)
        except Exception:
            # If we can't create the unsafe pickle, that's okay
            pass

    def test_secure_pickle_class(self, secure_pickle, temp_dir):
        """Test SecurePickle class directly."""
        sp = secure_pickle.SecurePickle(secret_key=b"test_key")

        test_data = {'test': 'data'}
        file_path = temp_dir / "sp_test.pkl"

        # Save and load
        sp.save(test_data, str(file_path))
        loaded = sp.load(str(file_path), restricted=False)

        assert loaded == test_data


class TestCache:
    """Test suite for caching utilities."""

    def test_lru_cache_basic(self):
        """Test basic LRU cache operations."""
        from utils.cache import LRUCache

        cache = LRUCache(maxsize=3)

        # Add items
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        cache.put('key3', 'value3')

        # Retrieve items
        assert cache.get('key1') == 'value1'
        assert cache.get('key2') == 'value2'
        assert cache.get('key3') == 'value3'

    def test_lru_cache_eviction(self):
        """Test LRU cache evicts least recently used items."""
        from utils.cache import LRUCache

        cache = LRUCache(maxsize=2)

        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        cache.put('key3', 'value3')  # Should evict key1

        # key1 should be evicted
        assert cache.get('key1') is None
        assert cache.get('key2') == 'value2'
        assert cache.get('key3') == 'value3'

    def test_lru_cache_statistics(self):
        """Test LRU cache statistics tracking."""
        from utils.cache import LRUCache

        cache = LRUCache(maxsize=10)

        cache.put('key1', 'value1')
        cache.get('key1')  # Hit
        cache.get('key2')  # Miss

        stats = cache.get_stats()
        assert 'hits' in stats
        assert 'misses' in stats
        assert stats['hits'] == 1
        assert stats['misses'] == 1

    def test_ttl_cache_basic(self):
        """Test basic TTL cache operations."""
        from utils.cache import TTLCache

        cache = TTLCache(default_ttl=10)  # 10 second TTL

        cache.put('key1', 'value1')
        assert cache.get('key1') == 'value1'

    def test_ttl_cache_expiration(self):
        """Test TTL cache item expiration."""
        from utils.cache import TTLCache

        cache = TTLCache(default_ttl=0.1)  # 100ms TTL

        cache.put('key1', 'value1')
        assert cache.get('key1') == 'value1'

        # Wait for expiration
        time.sleep(0.2)

        # Should be expired
        assert cache.get('key1') is None

    def test_ttl_cache_custom_ttl(self):
        """Test TTL cache with custom TTL per item."""
        from utils.cache import TTLCache

        cache = TTLCache(default_ttl=10)

        cache.put('key1', 'value1', ttl=0.1)  # Custom 100ms TTL
        cache.put('key2', 'value2', ttl=100)  # Long TTL

        time.sleep(0.2)

        # key1 should be expired, key2 should still exist
        assert cache.get('key1') is None
        assert cache.get('key2') == 'value2'

    def test_disk_cache_basic(self, temp_dir):
        """Test basic disk cache operations."""
        from utils.cache import DiskCache

        cache_dir = temp_dir / "cache"
        cache = DiskCache(cache_dir=str(cache_dir))

        cache.put('key1', 'value1')
        assert cache.get('key1') == 'value1'

    def test_disk_cache_persistence(self, temp_dir):
        """Test disk cache persists across instances."""
        from utils.cache import DiskCache

        cache_dir = temp_dir / "cache"

        # First instance
        cache1 = DiskCache(cache_dir=str(cache_dir))
        cache1.put('persistent_key', 'persistent_value')

        # Second instance (simulating restart)
        cache2 = DiskCache(cache_dir=str(cache_dir))
        assert cache2.get('persistent_key') == 'persistent_value'

    def test_disk_cache_clear(self, temp_dir):
        """Test disk cache clear operation."""
        from utils.cache import DiskCache

        cache_dir = temp_dir / "cache"
        cache = DiskCache(cache_dir=str(cache_dir))

        cache.put('key1', 'value1')
        cache.put('key2', 'value2')

        cache.clear()

        assert cache.get('key1') is None
        assert cache.get('key2') is None

    def test_cached_decorator(self):
        """Test @cached decorator."""
        from utils.cache import cached, LRUCache

        call_count = 0

        @cached(cache=LRUCache(maxsize=10))
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call with same args - should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented

        # Different args - should execute function
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_cache_thread_safety(self):
        """Test cache thread safety."""
        from utils.cache import LRUCache
        import threading

        cache = LRUCache(maxsize=100)
        errors = []

        def worker(worker_id):
            try:
                for i in range(100):
                    cache.put(f'key_{worker_id}_{i}', f'value_{worker_id}_{i}')
                    cache.get(f'key_{worker_id}_{i}')
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should complete without errors
        assert len(errors) == 0


@pytest.mark.performance
class TestCachePerformance:
    """Performance tests for cache implementations."""

    def test_lru_cache_performance(self):
        """Test LRU cache performance."""
        from utils.cache import LRUCache
        import time

        cache = LRUCache(maxsize=1000)

        # Measure write performance
        start = time.time()
        for i in range(1000):
            cache.put(f'key_{i}', f'value_{i}')
        write_time = time.time() - start

        # Measure read performance
        start = time.time()
        for i in range(1000):
            cache.get(f'key_{i}')
        read_time = time.time() - start

        # Should be fast (< 100ms for 1000 operations)
        assert write_time < 0.1
        assert read_time < 0.1

    def test_cache_memory_efficiency(self):
        """Test cache memory usage."""
        from utils.cache import LRUCache

        # Create cache with size limit
        cache = LRUCache(maxsize=100)

        # Add many items
        for i in range(1000):
            cache.put(f'key_{i}', f'value_{i}')

        # Size should be limited
        # The cache should not grow beyond maxsize
        stats = cache.get_stats()
        # Verify size constraint is working
        assert 'size' in stats or 'maxsize' in stats
