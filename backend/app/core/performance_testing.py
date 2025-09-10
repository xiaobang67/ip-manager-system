"""
性能测试和负载测试工具
用于验证系统性能优化效果
"""
import asyncio
import time
import statistics
import logging
from typing import Dict, List, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from app.core.timezone_config import now_beijing
import requests
import json

from .database import SessionLocal
from .redis_client import cache_service
from .query_optimizer import query_monitor

logger = logging.getLogger(__name__)


@dataclass
class PerformanceTestResult:
    """性能测试结果"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    errors: List[str]


class PerformanceTester:
    """性能测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "IPAM-Performance-Tester/1.0"
        })
    
    def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        ramp_up_time: int = 5
    ) -> PerformanceTestResult:
        """运行负载测试"""
        logger.info(f"Starting load test: {method} {endpoint}")
        logger.info(f"Concurrent users: {concurrent_users}, Requests per user: {requests_per_user}")
        
        start_time = time.time()
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        # 计算每个用户的启动延迟
        user_delay = ramp_up_time / concurrent_users if concurrent_users > 0 else 0
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            # 提交所有任务
            futures = []
            for user_id in range(concurrent_users):
                delay = user_id * user_delay
                future = executor.submit(
                    self._user_simulation,
                    endpoint, method, payload, headers,
                    requests_per_user, delay, user_id
                )
                futures.append(future)
            
            # 收集结果
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    response_times.extend(user_results['response_times'])
                    errors.extend(user_results['errors'])
                    successful_requests += user_results['successful']
                    failed_requests += user_results['failed']
                except Exception as e:
                    logger.error(f"User simulation failed: {e}")
                    failed_requests += requests_per_user
        
        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests
        
        # 计算统计信息
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        result = PerformanceTestResult(
            test_name=f"{method} {endpoint}",
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors[:10]  # 只保留前10个错误
        )
        
        logger.info(f"Load test completed: {result.requests_per_second:.2f} RPS, "
                   f"{result.error_rate:.2%} error rate")
        
        return result
    
    def _user_simulation(
        self,
        endpoint: str,
        method: str,
        payload: Optional[Dict],
        headers: Optional[Dict],
        requests_count: int,
        delay: float,
        user_id: int
    ) -> Dict[str, Any]:
        """模拟单个用户的请求"""
        # 等待启动延迟
        if delay > 0:
            time.sleep(delay)
        
        response_times = []
        errors = []
        successful = 0
        failed = 0
        
        url = f"{self.base_url}{endpoint}"
        request_headers = headers or {}
        
        for i in range(requests_count):
            try:
                start_time = time.time()
                
                if method.upper() == "GET":
                    response = self.session.get(url, headers=request_headers, timeout=30)
                elif method.upper() == "POST":
                    response = self.session.post(url, json=payload, headers=request_headers, timeout=30)
                elif method.upper() == "PUT":
                    response = self.session.put(url, json=payload, headers=request_headers, timeout=30)
                elif method.upper() == "DELETE":
                    response = self.session.delete(url, headers=request_headers, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code < 400:
                    successful += 1
                else:
                    failed += 1
                    errors.append(f"HTTP {response.status_code}: {response.text[:100]}")
                
            except Exception as e:
                failed += 1
                errors.append(f"Request failed: {str(e)}")
                response_times.append(30.0)  # 超时时间
        
        return {
            'response_times': response_times,
            'errors': errors,
            'successful': successful,
            'failed': failed
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def run_stress_test(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        max_users: int = 100,
        step_size: int = 10,
        step_duration: int = 30
    ) -> List[PerformanceTestResult]:
        """运行压力测试"""
        logger.info(f"Starting stress test: {method} {endpoint}")
        logger.info(f"Max users: {max_users}, Step size: {step_size}, Step duration: {step_duration}s")
        
        results = []
        
        for users in range(step_size, max_users + 1, step_size):
            logger.info(f"Testing with {users} concurrent users...")
            
            result = self.run_load_test(
                endpoint=endpoint,
                method=method,
                payload=payload,
                headers=headers,
                concurrent_users=users,
                requests_per_user=step_duration,  # 每秒1个请求
                ramp_up_time=5
            )
            
            results.append(result)
            
            # 检查是否达到性能瓶颈
            if result.error_rate > 0.1 or result.avg_response_time > 5.0:
                logger.warning(f"Performance degradation detected at {users} users")
                break
            
            # 短暂休息
            time.sleep(2)
        
        return results


class DatabasePerformanceTester:
    """数据库性能测试器"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def test_query_performance(self, query_func: Callable, iterations: int = 100) -> Dict[str, Any]:
        """测试查询性能"""
        response_times = []
        errors = []
        
        for i in range(iterations):
            try:
                start_time = time.time()
                result = query_func(self.db)
                response_time = time.time() - start_time
                response_times.append(response_time)
            except Exception as e:
                errors.append(str(e))
                response_times.append(0)
        
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = self._percentile(response_times, 95)
        else:
            avg_time = min_time = max_time = p95_time = 0
        
        return {
            "iterations": iterations,
            "avg_response_time": avg_time,
            "min_response_time": min_time,
            "max_response_time": max_time,
            "p95_response_time": p95_time,
            "error_count": len(errors),
            "errors": errors[:5]  # 只保留前5个错误
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


class CachePerformanceTester:
    """缓存性能测试器"""
    
    def __init__(self):
        self.cache = cache_service
    
    def test_cache_performance(self, key_prefix: str = "perf_test", iterations: int = 1000) -> Dict[str, Any]:
        """测试缓存性能"""
        set_times = []
        get_times = []
        errors = []
        
        test_data = {"test": "data", "timestamp": now_beijing().isoformat()}
        
        # 测试写入性能
        for i in range(iterations):
            try:
                key = f"{key_prefix}:{i}"
                start_time = time.time()
                self.cache.set(key, test_data, ttl=300)
                set_time = time.time() - start_time
                set_times.append(set_time)
            except Exception as e:
                errors.append(f"Set error: {str(e)}")
        
        # 测试读取性能
        for i in range(iterations):
            try:
                key = f"{key_prefix}:{i}"
                start_time = time.time()
                result = self.cache.get(key)
                get_time = time.time() - start_time
                get_times.append(get_time)
            except Exception as e:
                errors.append(f"Get error: {str(e)}")
        
        # 清理测试数据
        try:
            self.cache.clear_pattern(f"{key_prefix}:*")
        except Exception as e:
            logger.warning(f"Failed to clean up test data: {e}")
        
        return {
            "iterations": iterations,
            "set_performance": {
                "avg_time": statistics.mean(set_times) if set_times else 0,
                "min_time": min(set_times) if set_times else 0,
                "max_time": max(set_times) if set_times else 0,
                "p95_time": self._percentile(set_times, 95) if set_times else 0
            },
            "get_performance": {
                "avg_time": statistics.mean(get_times) if get_times else 0,
                "min_time": min(get_times) if get_times else 0,
                "max_time": max(get_times) if get_times else 0,
                "p95_time": self._percentile(get_times, 95) if get_times else 0
            },
            "error_count": len(errors),
            "errors": errors[:5]
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


def run_comprehensive_performance_test() -> Dict[str, Any]:
    """运行综合性能测试"""
    logger.info("Starting comprehensive performance test...")
    
    results = {
        "timestamp": now_beijing().isoformat(),
        "tests": {}
    }
    
    try:
        # API负载测试
        api_tester = PerformanceTester()
        
        # 测试主要API端点
        api_endpoints = [
            {"endpoint": "/api/v1/ips", "method": "GET"},
            {"endpoint": "/api/v1/subnets", "method": "GET"},
            {"endpoint": "/api/v1/users", "method": "GET"},
            {"endpoint": "/health", "method": "GET"}
        ]
        
        for endpoint_config in api_endpoints:
            try:
                result = api_tester.run_load_test(
                    endpoint=endpoint_config["endpoint"],
                    method=endpoint_config["method"],
                    concurrent_users=20,
                    requests_per_user=10
                )
                results["tests"][f"api_{endpoint_config['endpoint'].replace('/', '_')}"] = {
                    "type": "api_load_test",
                    "result": result.__dict__
                }
            except Exception as e:
                logger.error(f"API test failed for {endpoint_config['endpoint']}: {e}")
        
        # 缓存性能测试
        cache_tester = CachePerformanceTester()
        cache_result = cache_tester.test_cache_performance(iterations=500)
        results["tests"]["cache_performance"] = {
            "type": "cache_performance",
            "result": cache_result
        }
        
        # 数据库性能测试
        db_tester = DatabasePerformanceTester()
        
        # 简单查询测试
        def simple_query(db):
            return db.execute("SELECT 1").fetchone()
        
        db_result = db_tester.test_query_performance(simple_query, iterations=100)
        results["tests"]["database_simple_query"] = {
            "type": "database_performance",
            "result": db_result
        }
        
    except Exception as e:
        logger.error(f"Comprehensive performance test failed: {e}")
        results["error"] = str(e)
    
    logger.info("Comprehensive performance test completed")
    return results