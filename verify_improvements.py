#!/usr/bin/env python3
"""
Verification Script for Network Traffic Analyzer Improvements
Tests all new features and improvements to ensure they work correctly
"""

import sys
import os
from pathlib import Path

def check_imports():
    """Verify all new modules can be imported"""
    print("=" * 60)
    print("CHECKING IMPORTS")
    print("=" * 60)

    modules = [
        ('utils.validators', ['InputValidator', 'ValidationError']),
        ('utils.secure_pickle', ['safe_load', 'safe_save', 'SecurePickle']),
        ('utils.cache', ['LRUCache', 'TTLCache', 'DiskCache', 'cached']),
    ]

    all_passed = True
    for module_name, expected_attrs in modules:
        try:
            module = __import__(module_name, fromlist=expected_attrs)
            missing = [attr for attr in expected_attrs if not hasattr(module, attr)]
            if missing:
                print(f"❌ {module_name}: Missing {missing}")
                all_passed = False
            else:
                print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
            all_passed = False

    print()
    return all_passed

def check_files():
    """Verify all expected files exist"""
    print("=" * 60)
    print("CHECKING FILES")
    print("=" * 60)

    required_files = [
        # Utilities
        'utils/__init__.py',
        'utils/validators.py',
        'utils/secure_pickle.py',
        'utils/cache.py',

        # API
        'api/__init__.py',
        'api/main.py',

        # Configuration
        '.pylintrc',
        'mypy.ini',
        '.flake8',
        '.pre-commit-config.yaml',
        '.bandit.yaml',

        # Docker
        'Dockerfile',
        'docker-compose.yml',
        '.dockerignore',
        '.env.example',

        # Development
        'Makefile',
        'requirements-dev.txt',

        # Documentation
        'IMPROVEMENTS.md',
    ]

    all_exist = True
    for filepath in required_files:
        if Path(filepath).exists():
            print(f"✅ {filepath}")
        else:
            print(f"❌ {filepath} - NOT FOUND")
            all_exist = False

    print()
    return all_exist

def test_validators():
    """Test input validation system"""
    print("=" * 60)
    print("TESTING VALIDATORS")
    print("=" * 60)

    try:
        from utils.validators import InputValidator, ValidationError

        # Test network interface validation
        try:
            result = InputValidator.validate_network_interface('eth0')
            print("✅ Network interface validation works")
        except Exception as e:
            print(f"❌ Network interface validation failed: {e}")
            return False

        # Test invalid interface
        try:
            InputValidator.validate_network_interface('invalid!@#$')
            print("❌ Invalid interface should have raised ValidationError")
            return False
        except ValidationError:
            print("✅ Invalid interface correctly rejected")

        # Test BPF filter validation
        try:
            InputValidator.validate_bpf_filter('tcp port 80')
            print("✅ BPF filter validation works")
        except Exception as e:
            print(f"❌ BPF filter validation failed: {e}")
            return False

        # Test duration validation
        try:
            InputValidator.validate_duration(60)
            print("✅ Duration validation works")
        except Exception as e:
            print(f"❌ Duration validation failed: {e}")
            return False

        print()
        return True

    except Exception as e:
        print(f"❌ Validator tests failed: {e}")
        print()
        return False

def test_cache():
    """Test caching system"""
    print("=" * 60)
    print("TESTING CACHE")
    print("=" * 60)

    try:
        from utils.cache import LRUCache, TTLCache, DiskCache

        # Test LRU Cache
        lru = LRUCache(maxsize=10)
        lru.put('key1', 'value1')
        value = lru.get('key1')
        if value == 'value1':
            print("✅ LRU Cache works")
        else:
            print(f"❌ LRU Cache failed: expected 'value1', got {value}")
            return False

        # Test TTL Cache
        ttl = TTLCache(ttl_seconds=60, maxsize=10)
        ttl.put('key2', 'value2')
        value = ttl.get('key2')
        if value == 'value2':
            print("✅ TTL Cache works")
        else:
            print(f"❌ TTL Cache failed: expected 'value2', got {value}")
            return False

        # Test cache statistics
        stats = lru.get_stats()
        if 'hits' in stats and 'misses' in stats:
            print("✅ Cache statistics work")
        else:
            print("❌ Cache statistics missing required fields")
            return False

        print()
        return True

    except Exception as e:
        print(f"❌ Cache tests failed: {e}")
        print()
        return False

def test_secure_pickle():
    """Test secure pickle loading"""
    print("=" * 60)
    print("TESTING SECURE PICKLE")
    print("=" * 60)

    try:
        from utils.secure_pickle import SecurePickle, safe_save, safe_load
        import tempfile
        import os

        # Create a test object
        test_data = {'key': 'value', 'number': 42}

        # Test save and load
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
            temp_path = f.name

        try:
            # Save securely
            safe_save(test_data, temp_path)
            print("✅ Secure save works")

            # Load securely
            loaded_data = safe_load(temp_path, restricted=False)
            if loaded_data == test_data:
                print("✅ Secure load works")
            else:
                print(f"❌ Loaded data doesn't match: {loaded_data}")
                return False

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        print()
        return True

    except Exception as e:
        print(f"❌ Secure pickle tests failed: {e}")
        print()
        return False

def check_configuration():
    """Verify configuration files are valid"""
    print("=" * 60)
    print("CHECKING CONFIGURATION")
    print("=" * 60)

    try:
        import yaml

        yaml_files = [
            'config/alert_config.yaml',
            '.pre-commit-config.yaml',
            '.bandit.yaml',
            'docker-compose.yml',
        ]

        all_valid = True
        for filepath in yaml_files:
            if Path(filepath).exists():
                try:
                    with open(filepath, 'r') as f:
                        yaml.safe_load(f)
                    print(f"✅ {filepath}")
                except yaml.YAMLError as e:
                    print(f"❌ {filepath}: {e}")
                    all_valid = False
            else:
                print(f"⚠️  {filepath} not found")

        print()
        return all_valid

    except ImportError:
        print("⚠️  PyYAML not installed, skipping YAML validation")
        print()
        return True

def main():
    """Run all verification checks"""
    print("\n")
    print("*" * 60)
    print("NETWORK TRAFFIC ANALYZER - IMPROVEMENTS VERIFICATION")
    print("*" * 60)
    print()

    results = {
        'Imports': check_imports(),
        'Files': check_files(),
        'Validators': test_validators(),
        'Cache': test_cache(),
        'Secure Pickle': test_secure_pickle(),
        'Configuration': check_configuration(),
    }

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for check, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{check:20} {status}")

    print()

    if all(results.values()):
        print("🎉 All verification checks passed!")
        print()
        return 0
    else:
        print("⚠️  Some verification checks failed!")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
