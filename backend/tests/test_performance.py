"""
性能测试
测试系统在高负载下的性能表现
"""
import pytest
import asyncio
import time
from httpx import AsyncClient
from concurrent.futures import ThreadPoolExecutor
from app.main import app
from app.models import Subnet, IPAddress, User
import statistics


class TestAPIPerformance:
    """API性能测试"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_subnet_list_performance(self, client: AsyncClient, auth_headers, performance_test_data):
        """测试网段列表API性能"""
        # 预热请求
        await client.get("/api/subnets", headers=auth_headers)
        
        # 性能测试
        start_time = time.time()
        response = await client.get("/api/subnets", headers=auth_headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # 响应时间应小于1秒
        
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, concurrent_clients, auth_headers):
        """测试并发请求性能"""
        async def make_request(client):
            start_time = time.time()
            response = await client.get("/api/subnets", headers=auth_headers)
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time
            }
        
        # 并发执行请求
        tasks = [make_request(client) for client in concurrent_clients]
        results = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功
        for result in results:
            assert result['status_code'] == 200
        
        # 计算性能指标
        response_times = [result['response_time'] for result in results]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 2.0  # 平均响应时间小于2秒
        assert max_response_time < 5.0  # 最大响应时间小于5秒
        
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_dataset_query(self, client: AsyncClient, auth_headers, db_session):
        """测试大数据集查询性能"""
        # 创建大量测试数据
        subnets = []
        for i in range(100):
            subnet = Subnet(
                network=f"10.{i}.0.0/16",
                netmask="255.255.0.0",
                gateway=f"10.{i}.0.1",
                description=f"Performance Test Network {i}",
                created_by=1
            )
            subnets.append(subnet)
        
        db_session.add_all(subnets)
        await db_session.commit()
        
        # 测试查询性能
        start_time = time.time()
        response = await client.get("/api/subnets?size=100", headers=auth_headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0  # 大数据集查询应在2秒内完成
        
        data = response.json()
        assert len(data['items']) <= 100
        
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_search_performance(self, client: AsyncClient, auth_headers, db_session):
        """测试搜索功能性能"""
        # 创建测试数据
        ips = []
        for i in range(1000):
            ip = IPAddress(
                ip_address=f"192.168.{i//256}.{i%256}",
                subnet_id=1,
                status="available",
                hostname=f"host-{i:04d}" if i % 3 == 0 else None,
                description=f"Performance test IP {i}"
            )
            ips.append(ip)
        
        db_session.add_all(ips)
        await db_session.commit()
        
        # 测试搜索性能
        search_queries = [
            "192.168.1",
            "host-0001",
            "Performance test",
            "available"
        ]
        
        for query in search_queries:
            start_time = time.time()
            response = await client.get(f"/api/ips/search?query={query}", headers=auth_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.5  # 搜索应在1.5秒内完成
            
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_operations_performance(self, client: AsyncClient, auth_headers, test_subnet_with_ips):
        """测试批量操作性能"""
        # 获取可用IP列表
        response = await client.get("/api/ips?status=available&size=50", headers=auth_headers)
        available_ips = response.json()['items']
        
        if len(available_ips) < 10:
            pytest.skip("Not enough available IPs for batch test")
        
        # 批量分配IP
        allocation_tasks = []
        for ip in available_ips[:10]:
            task = client.post("/api/ips/allocate", 
                headers=auth_headers,
                json={
                    "ip_address": ip['ip_address'],
                    "hostname": f"batch-host-{ip['id']}",
                    "description": "Batch allocation test"
                }
            )
            allocation_tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*allocation_tasks)
        end_time = time.time()
        
        batch_time = end_time - start_time
        
        # 验证所有分配都成功
        for response in responses:
            assert response.status_code == 200
        
        assert batch_time < 5.0  # 批量操作应在5秒内完成
        
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage(self, client: AsyncClient, auth_headers):
        """测试内存使用情况"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行多次请求
        for _ in range(100):
            await client.get("/api/subnets", headers=auth_headers)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内
        assert memory_increase < 50  # 内存增长不应超过50MB


class TestDatabasePerformance:
    """数据库性能测试"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_query_optimization(self, db_session):
        """测试查询优化"""
        # 创建测试数据
        users = []
        for i in range(100):
            user = User(
                username=f"perfuser{i}",
                email=f"perfuser{i}@test.com",
                password_hash="hashed_password",
                role="user"
            )
            users.append(user)
        
        db_session.add_all(users)
        await db_session.commit()
        
        # 测试索引查询性能
        start_time = time.time()
        result = await db_session.execute(
            "SELECT * FROM users WHERE username = 'perfuser50'"
        )
        user = result.fetchone()
        end_time = time.time()
        
        query_time = end_time - start_time
        
        assert user is not None
        assert query_time < 0.1  # 索引查询应在100ms内完成
        
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, db_session):
        """测试批量插入性能"""
        # 准备大量数据
        ips = []
        for i in range(1000):
            ip = IPAddress(
                ip_address=f"10.0.{i//256}.{i%256}",
                subnet_id=1,
                status="available"
            )
            ips.append(ip)
        
        # 测试批量插入
        start_time = time.time()
        db_session.add_all(ips)
        await db_session.commit()
        end_time = time.time()
        
        insert_time = end_time - start_time
        
        assert insert_time < 5.0  # 1000条记录应在5秒内插入完成
        
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_complex_query_performance(self, db_session, test_subnet_with_ips):
        """测试复杂查询性能"""
        # 复杂查询：统计每个网段的IP使用情况
        start_time = time.time()
        result = await db_session.execute("""
            SELECT 
                s.network,
                COUNT(ip.id) as total_ips,
                SUM(CASE WHEN ip.status = 'allocated' THEN 1 ELSE 0 END) as allocated_ips,
                SUM(CASE WHEN ip.status = 'available' THEN 1 ELSE 0 END) as available_ips
            FROM subnets s
            LEFT JOIN ip_addresses ip ON s.id = ip.subnet_id
            GROUP BY s.id, s.network
        """)
        stats = result.fetchall()
        end_time = time.time()
        
        query_time = end_time - start_time
        
        assert len(stats) >= 1
        assert query_time < 1.0  # 复杂查询应在1秒内完成


class TestCachePerformance:
    """缓存性能测试"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, client: AsyncClient, auth_headers, mock_redis):
        """测试缓存命中性能"""
        # 第一次请求（缓存未命中）
        start_time = time.time()
        response1 = await client.get("/api/subnets", headers=auth_headers)
        first_request_time = time.time() - start_time
        
        # 第二次请求（缓存命中）
        start_time = time.time()
        response2 = await client.get("/api/subnets", headers=auth_headers)
        second_request_time = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # 缓存命中的请求应该更快
        assert second_request_time < first_request_time * 0.5
        
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_invalidation_performance(self, client: AsyncClient, auth_headers, mock_redis):
        """测试缓存失效性能"""
        # 预热缓存
        await client.get("/api/subnets", headers=auth_headers)
        
        # 创建新网段（应该使缓存失效）
        start_time = time.time()
        response = await client.post("/api/subnets",
            headers=auth_headers,
            json={
                "network": "172.20.0.0/16",
                "netmask": "255.255.0.0",
                "gateway": "172.20.0.1"
            }
        )
        invalidation_time = time.time() - start_time
        
        assert response.status_code == 201
        assert invalidation_time < 2.0  # 缓存失效操作应在2秒内完成


class TestLoadTesting:
    """负载测试"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_sustained_load(self, concurrent_clients, auth_headers):
        """测试持续负载"""
        async def sustained_requests(client, duration=30):
            """持续发送请求指定时间"""
            end_time = time.time() + duration
            request_count = 0
            response_times = []
            
            while time.time() < end_time:
                start_time = time.time()
                response = await client.get("/api/subnets", headers=auth_headers)
                request_time = time.time() - start_time
                
                response_times.append(request_time)
                request_count += 1
                
                if response.status_code != 200:
                    break
                
                # 短暂休息避免过度负载
                await asyncio.sleep(0.1)
            
            return {
                'request_count': request_count,
                'avg_response_time': statistics.mean(response_times),
                'max_response_time': max(response_times),
                'min_response_time': min(response_times)
            }
        
        # 并发执行负载测试
        tasks = [sustained_requests(client, 10) for client in concurrent_clients[:3]]
        results = await asyncio.gather(*tasks)
        
        # 验证性能指标
        total_requests = sum(result['request_count'] for result in results)
        avg_response_times = [result['avg_response_time'] for result in results]
        
        assert total_requests > 0
        assert all(avg_time < 3.0 for avg_time in avg_response_times)  # 平均响应时间小于3秒
        
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_stress_testing(self, concurrent_clients, auth_headers):
        """压力测试"""
        async def stress_request(client):
            """压力测试请求"""
            try:
                response = await client.get("/api/subnets", headers=auth_headers)
                return response.status_code == 200
            except Exception:
                return False
        
        # 高并发压力测试
        tasks = []
        for _ in range(50):  # 50个并发请求
            for client in concurrent_clients:
                tasks.append(stress_request(client))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        success_count = sum(1 for result in results if result is True)
        success_rate = success_count / len(results)
        
        # 验证系统在压力下的表现
        assert success_rate > 0.9  # 成功率应大于90%
        assert total_time < 30.0   # 总时间应在30秒内


class TestResourceUsage:
    """资源使用测试"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cpu_usage(self, client: AsyncClient, auth_headers):
        """测试CPU使用率"""
        import psutil
        
        # 获取初始CPU使用率
        initial_cpu = psutil.cpu_percent(interval=1)
        
        # 执行密集操作
        tasks = []
        for _ in range(20):
            task = client.get("/api/subnets", headers=auth_headers)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # 获取最终CPU使用率
        final_cpu = psutil.cpu_percent(interval=1)
        
        # CPU使用率不应过高
        assert final_cpu < 80  # CPU使用率应小于80%
        
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_connection_pool(self, concurrent_clients, auth_headers):
        """测试数据库连接池性能"""
        async def db_intensive_request(client):
            """数据库密集型请求"""
            response = await client.get("/api/reports/dashboard", headers=auth_headers)
            return response.status_code == 200
        
        # 并发执行数据库密集型操作
        tasks = []
        for _ in range(10):
            for client in concurrent_clients:
                tasks.append(db_intensive_request(client))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        success_count = sum(results)
        
        assert success_count == len(results)  # 所有请求都应成功
        assert total_time < 15.0  # 应在15秒内完成


# 性能测试报告生成
class PerformanceReporter:
    """性能测试报告生成器"""
    
    def __init__(self):
        self.results = []
    
    def add_result(self, test_name, metrics):
        """添加测试结果"""
        self.results.append({
            'test_name': test_name,
            'timestamp': time.time(),
            **metrics
        })
    
    def generate_report(self):
        """生成性能测试报告"""
        report = {
            'summary': {
                'total_tests': len(self.results),
                'timestamp': time.time()
            },
            'results': self.results
        }
        
        # 保存报告到文件
        import json
        with open('performance_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return report


@pytest.fixture
def performance_reporter():
    """性能报告器fixture"""
    return PerformanceReporter()