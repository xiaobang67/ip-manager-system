#!/usr/bin/env python3
"""
企业IP地址管理系统 - 前端数据读取测试脚本
"""
import requests
import json
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api/v1"

class FrontendDataTester:
    """前端数据读取测试类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.headers = {}
        
    def login(self, username: str = "admin", password: str = "admin123") -> bool:
        """用户登录"""
        print("用户登录...")
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.access_token}"}
                print("✓ 登录成功")
                # 输出认证令牌以便调试
                print(f"认证令牌: {self.access_token}")
                return True
            else:
                print(f"✗ 登录失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 登录异常: {e}")
            return False
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """测试所有API端点的数据读取"""
        results = {}
        
        # 测试获取网段列表
        print("\n1. 测试获取网段列表...")
        try:
            response = self.session.get(
                f"{API_BASE_URL}/network-segments",
                headers=self.headers,
                params={"limit": 100}
            )
            
            if response.status_code == 200:
                data = response.json()
                results["network_segments"] = {
                    "success": True,
                    "count": data.get("total", 0),
                    "data": data.get("items", [])[:3]  # 只显示前3个
                }
                print(f"✓ 获取网段列表成功，共 {data.get('total', 0)} 个网段")
            else:
                results["network_segments"] = {
                    "success": False,
                    "error": f"状态码: {response.status_code}",
                    "response": response.text
                }
                print(f"✗ 获取网段列表失败: {response.text}")
        except Exception as e:
            results["network_segments"] = {
                "success": False,
                "error": str(e)
            }
            print(f"✗ 获取网段列表异常: {e}")
        
        # 测试获取IP地址列表
        print("\n2. 测试获取IP地址列表...")
        try:
            response = self.session.get(
                f"{API_BASE_URL}/ip-addresses",
                headers=self.headers,
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                results["ip_addresses"] = {
                    "success": True,
                    "count": len(data),
                    "data": data[:3]  # 只显示前3个
                }
                print(f"✓ 获取IP地址列表成功，共 {len(data)} 个IP地址")
            else:
                results["ip_addresses"] = {
                    "success": False,
                    "error": f"状态码: {response.status_code}",
                    "response": response.text
                }
                print(f"✗ 获取IP地址列表失败: {response.text}")
        except Exception as e:
            results["ip_addresses"] = {
                "success": False,
                "error": str(e)
            }
            print(f"✗ 获取IP地址列表异常: {e}")
        
        # 测试获取用户列表
        print("\n3. 测试获取用户列表...")
        try:
            response = self.session.get(
                f"{API_BASE_URL}/users",
                headers=self.headers,
                params={"limit": 100}
            )
            
            if response.status_code == 200:
                data = response.json()
                # 修复：用户API返回的是列表，不是分页对象
                results["users"] = {
                    "success": True,
                    "count": len(data),
                    "data": data[:3]  # 只显示前3个
                }
                print(f"✓ 获取用户列表成功，共 {len(data)} 个用户")
            else:
                results["users"] = {
                    "success": False,
                    "error": f"状态码: {response.status_code}",
                    "response": response.text
                }
                print(f"✗ 获取用户列表失败: {response.text}")
        except Exception as e:
            results["users"] = {
                "success": False,
                "error": str(e)
            }
            print(f"✗ 获取用户列表异常: {e}")
        
        # 测试获取部门列表
        print("\n4. 测试获取部门列表...")
        try:
            response = self.session.get(
                f"{API_BASE_URL}/departments",
                headers=self.headers,
                params={"limit": 100}
            )
            
            if response.status_code == 200:
                data = response.json()
                # 修复：部门API返回的是列表，不是分页对象
                results["departments"] = {
                    "success": True,
                    "count": len(data),
                    "data": data[:3]  # 只显示前3个
                }
                print(f"✓ 获取部门列表成功，共 {len(data)} 个部门")
            else:
                results["departments"] = {
                    "success": False,
                    "error": f"状态码: {response.status_code}",
                    "response": response.text
                }
                print(f"✗ 获取部门列表失败: {response.text}")
        except Exception as e:
            results["departments"] = {
                "success": False,
                "error": str(e)
            }
            print(f"✗ 获取部门列表异常: {e}")
        
        # 测试仪表盘统计数据
        print("\n5. 测试获取仪表盘统计数据...")
        try:
            response = self.session.get(
                f"{API_BASE_URL}/dashboard/stats",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                results["dashboard_stats"] = {
                    "success": True,
                    "data": data
                }
                print("✓ 获取仪表盘统计数据成功")
            else:
                results["dashboard_stats"] = {
                    "success": False,
                    "error": f"状态码: {response.status_code}",
                    "response": response.text
                }
                print(f"✗ 获取仪表盘统计数据失败: {response.text}")
        except Exception as e:
            results["dashboard_stats"] = {
                "success": False,
                "error": str(e)
            }
            print(f"✗ 获取仪表盘统计数据异常: {e}")
        
        return results
    
    def print_detailed_results(self, results: Dict[str, Any]):
        """打印详细测试结果"""
        print("\n" + "=" * 60)
        print("详细测试结果")
        print("=" * 60)
        
        for endpoint, result in results.items():
            print(f"\n{endpoint.upper()}:")
            print("-" * 40)
            
            if result["success"]:
                print(f"状态: ✓ 成功")
                # 特殊处理仪表盘统计数据
                if endpoint == "dashboard_stats":
                    print("数据:")
                    print(json.dumps(result["data"], ensure_ascii=False, indent=2))
                else:
                    print(f"数量: {result['count']}")
                    if "data" in result and result["data"]:
                        print("示例数据:")
                        for i, item in enumerate(result["data"], 1):
                            print(f"  {i}. {json.dumps(item, ensure_ascii=False, indent=2)}")
                    else:
                        print("数据: 无")
            else:
                print(f"状态: ✗ 失败")
                print(f"错误: {result['error']}")
                if "response" in result:
                    print(f"响应: {result['response']}")
    
    def run_test(self) -> bool:
        """运行完整的前端数据读取测试"""
        print("=" * 60)
        print("企业IP地址管理系统 - 前端数据读取测试")
        print("=" * 60)
        
        # 登录
        if not self.login():
            print("登录失败，无法继续测试")
            return False
        
        # 测试所有API端点
        results = self.test_api_endpoints()
        
        # 打印详细结果
        self.print_detailed_results(results)
        
        # 统计结果
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result["success"])
        
        print("\n" + "=" * 60)
        print("测试结果摘要")
        print("=" * 60)
        print(f"通过: {passed_tests}/{total_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 所有测试通过！前端数据读取功能正常。")
            return True
        else:
            print(f"\n❌ {total_tests - passed_tests} 个测试失败，请检查系统配置。")
            return False

def main():
    """主函数"""
    tester = FrontendDataTester()
    success = tester.run_test()
    
    if success:
        print("\n系统数据读取功能正常，前端应该能够正确显示数据。")
    else:
        print("\n系统存在数据读取问题，请检查日志和配置。")

if __name__ == "__main__":
    main()