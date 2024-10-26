import os
import gc
import logging
import resource
from typing import Optional
import streamlit as st
from contextlib import contextmanager
import threading
import time
import psutil

logger = logging.getLogger(__name__)

class ResourceManager:
    def __init__(self):
        self._setup_limits()
        self._thread_count = 0
        self._thread_lock = threading.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 10  # Reduced to 10 seconds
        
    def _setup_limits(self):
        """Setup minimal resource limits"""
        try:
            # Set extremely conservative process limit
            resource.setrlimit(resource.RLIMIT_NPROC, (32, 64))
            
            # Set minimal memory limit (32MB soft, 64MB hard)
            memory_limit_soft = 32 * 1024 * 1024  # 32MB
            memory_limit_hard = 64 * 1024 * 1024  # 64MB
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit_soft, memory_limit_hard))
            
            # Set minimal CPU time limit (2 mins soft, 3 mins hard)
            resource.setrlimit(resource.RLIMIT_CPU, (120, 180))
            
            # Set process priority
            try:
                os.nice(19)  # Lowest priority
            except Exception:
                logger.warning("Failed to set process priority")
            
        except Exception as e:
            logger.warning(f"Failed to set resource limits: {str(e)}")

    def check_resources(self) -> bool:
        """Check if sufficient resources are available"""
        try:
            memory = self.get_memory_usage()
            if memory['rss'] > 50:  # Over 50MB
                self.cleanup()
                memory = self.get_memory_usage()
                if memory['rss'] > 50:
                    return False
            
            # Check thread count
            if self._thread_count >= 1:
                return False
            
            # Check CPU usage
            if self.get_cpu_usage() > 80:
                return False
                
            return True
        except Exception as e:
            logger.error(f"Resource check failed: {str(e)}")
            return False

    def get_memory_usage(self) -> dict:
        """Get current memory usage statistics"""
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return {
                'rss': usage.ru_maxrss / 1024,  # Convert KB to MB
                'shared': usage.ru_ixrss / 1024,
                'unshared': usage.ru_idrss / 1024,
                'stack': usage.ru_isrss / 1024
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {str(e)}")
            return {'rss': 0, 'shared': 0, 'unshared': 0, 'stack': 0}

    def get_cpu_usage(self) -> float:
        """Get CPU usage"""
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return (usage.ru_utime + usage.ru_stime) * 100
        except Exception as e:
            logger.error(f"Error getting CPU usage: {str(e)}")
            return 0.0

    def _should_cleanup(self) -> bool:
        """Check if cleanup should be performed"""
        current_time = time.time()
        if current_time - self._last_cleanup >= self._cleanup_interval:
            return True
            
        memory_usage = self.get_memory_usage()
        return memory_usage['rss'] > 25  # Ultra aggressive cleanup threshold (25MB)

    def cleanup(self):
        """Perform ultra aggressive cleanup"""
        try:
            # Force garbage collection multiple times
            for _ in range(5):
                gc.collect()
                gc.collect(2)  # Generation 2 collection
            
            # Clear all Streamlit caches
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
            if hasattr(st, 'cache_resource'):
                st.cache_resource.clear()
            
            # Clear session state cache
            if hasattr(st, 'session_state'):
                essential_keys = {'logged_in', 'account', 'tab_client'}
                for key in list(st.session_state.keys()):
                    if key not in essential_keys:
                        del st.session_state[key]
            
            # Clear module caches
            for module in list(sys.modules.keys()):
                if module not in sys.modules:
                    continue
                if hasattr(sys.modules[module], 'cache_clear'):
                    try:
                        sys.modules[module].cache_clear()
                    except:
                        pass
            
            # Update cleanup timestamp
            self._last_cleanup = time.time()
            logger.info("Performed ultra aggressive cleanup")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            
    def acquire_thread(self) -> bool:
        """Try to acquire the single thread slot"""
        with self._thread_lock:
            if self._thread_count < 1:  # Single thread only
                if self._should_cleanup():
                    self.cleanup()
                if self.check_resources():
                    self._thread_count += 1
                    return True
            return False
            
    def release_thread(self):
        """Release thread slot and cleanup"""
        with self._thread_lock:
            if self._thread_count > 0:
                self._thread_count -= 1
                self.cleanup()  # Always cleanup on release

    @contextmanager
    def monitor_resources(self, threshold_memory_mb: float = 25):
        """Monitor resource usage with minimal threshold"""
        try:
            if not self.check_resources():
                self.cleanup()
            yield
        finally:
            memory_usage = self.get_memory_usage()
            if memory_usage['rss'] > threshold_memory_mb:
                logger.warning(f"High memory usage detected: {memory_usage['rss']:.2f}MB")
                self.cleanup()

resource_manager = ResourceManager()

def optimize_streamlit_cache():
    """Optimize Streamlit cache aggressively"""
    try:
        if resource_manager._should_cleanup():
            resource_manager.cleanup()
            logger.info("Optimized Streamlit cache")
    except Exception as e:
        logger.error(f"Error optimizing cache: {str(e)}")

def monitor_performance(func):
    """Decorator for performance monitoring"""
    def wrapper(*args, **kwargs):
        with resource_manager.monitor_resources():
            try:
                if not resource_manager.check_resources():
                    logger.warning("Insufficient resources available")
                    resource_manager.cleanup()
                return func(*args, **kwargs)
            finally:
                resource_manager.cleanup()
    return wrapper

@contextmanager
def managed_thread_pool(max_workers: Optional[int] = None):
    """Single-threaded pool manager with backoff"""
    max_workers = 1  # Force single thread
    
    retry_count = 0
    while not resource_manager.acquire_thread() and retry_count < 3:
        logger.warning(f"Thread unavailable, attempt {retry_count + 1}/3")
        time.sleep(1.5 ** retry_count)  # Exponential backoff
        resource_manager.cleanup()
        retry_count += 1
    
    if retry_count >= 3:
        logger.error("Failed to acquire thread after retries")
        raise RuntimeError("Thread acquisition failed")
    
    try:
        yield max_workers
    finally:
        resource_manager.release_thread()
