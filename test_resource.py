import psutil
from utils.resource_manager import ResourceManager

def test_resource_manager():
    manager = ResourceManager()
    # Test memory usage
    memory_usage = manager.get_memory_usage()
    print("Memory Usage:", memory_usage)
    
    # Test CPU usage
    cpu_usage = manager.get_cpu_usage()
    print("CPU Usage:", cpu_usage)

if __name__ == "__main__":
    test_resource_manager()
