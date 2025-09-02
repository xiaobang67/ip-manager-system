import pytest
from unittest.mock import Mock, MagicMock
from app.services.query_builder import IPQueryBuilder, SearchHistoryService
from app.schemas.ip_address import IPSearchRequest
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.models.search_history import SearchHistory


class TestIPQueryBuilder:
    """测试IP查询构建器"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def query_builder(self, mock_db):
        """创建查询构建器实例"""
        return IPQueryBuilder(mock_db)
    
    def test_build_basic_search_query(self, query_builder, mock_db):
        """测试基本搜索查询构建"""
        # 模拟查询对象
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # 创建搜索请求
        search_request = IPSearchRequest(
            query="192.168.1",
            status="available",
            skip=0,
            limit=50
        )
        
        # 构建查询
        search_query, count_query = query_builder.build_search_query(search_request)
        
        # 验证查询构建
        assert search_query is not None
        assert count_query is not None
        mock_db.query.assert_called()
    
    def test_build_advanced_search_query(self, query_builder, mock_db):
        """测试高级搜索查询构建"""
        # 模拟查询对象
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # 创建高级搜索请求
        search_request = IPSearchRequest(
            query="server",
            subnet_id=1,
            status="allocated",
            device_type="server",
            location="datacenter",
            assigned_to="admin",
            hostname="web-server",
            mac_address="00:11:22",
            ip_range_start="192.168.1.1",
            ip_range_end="192.168.1.100",
            sort_by="ip_address",
            sort_order="asc",
            skip=0,
            limit=20
        )
        
        # 构建查询
        search_query, count_query = query_builder.build_search_query(search_request)
        
        # 验证查询构建
        assert search_query is not None
        assert count_query is not None
        mock_db.query.assert_called()


class TestSearchHistoryService:
    """测试搜索历史服务"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock()
        db.commit = Mock()
        db.add = Mock()
        db.refresh = Mock()
        return db
    
    @pytest.fixture
    def search_history_service(self, mock_db):
        """创建搜索历史服务实例"""
        return SearchHistoryService(mock_db)
    
    def test_save_new_search(self, search_history_service, mock_db):
        """测试保存新搜索"""
        # 模拟查询结果
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # 没有现有搜索
        
        # 模拟新创建的搜索历史对象
        mock_search_history = Mock()
        mock_search_history.id = 1
        
        # 测试保存搜索
        user_id = 1
        search_params = {"query": "test", "status": "available"}
        search_name = "测试搜索"
        
        # 由于我们在测试中模拟了数据库操作，这里主要测试方法调用
        # 实际的数据库操作会在集成测试中验证
        result_id = search_history_service.save_search(user_id, search_params, search_name)
        
        # 验证数据库操作被调用
        mock_db.query.assert_called()
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
    
    def test_save_existing_search(self, search_history_service, mock_db):
        """测试保存已存在的搜索（更新使用次数）"""
        # 模拟现有搜索记录
        existing_search = Mock()
        existing_search.id = 1
        existing_search.used_count = 5
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_search
        
        # 测试保存搜索
        user_id = 1
        search_params = {"query": "test", "status": "available"}
        
        result_id = search_history_service.save_search(user_id, search_params)
        
        # 验证使用次数增加
        assert existing_search.used_count == 6
        mock_db.commit.assert_called()
        assert result_id == 1
    
    def test_get_user_search_history(self, search_history_service, mock_db):
        """测试获取用户搜索历史"""
        # 模拟搜索历史记录
        mock_history = [Mock(), Mock(), Mock()]
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_history
        
        # 测试获取搜索历史
        user_id = 1
        limit = 20
        
        result = search_history_service.get_user_search_history(user_id, limit)
        
        # 验证结果
        assert result == mock_history
        mock_db.query.assert_called()
    
    def test_toggle_favorite(self, search_history_service, mock_db):
        """测试切换收藏状态"""
        # 模拟搜索记录
        search_record = Mock()
        search_record.is_favorite = False
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = search_record
        
        # 测试切换收藏
        user_id = 1
        search_id = 1
        
        result = search_history_service.toggle_favorite(user_id, search_id)
        
        # 验证收藏状态改变
        assert search_record.is_favorite == True
        assert result == True
        mock_db.commit.assert_called()


class TestSearchValidation:
    """测试搜索参数验证"""
    
    def test_valid_search_request(self):
        """测试有效的搜索请求"""
        search_request = IPSearchRequest(
            query="192.168.1",
            subnet_id=1,
            status="available",
            device_type="server",
            sort_by="ip_address",
            sort_order="asc",
            skip=0,
            limit=50
        )
        
        assert search_request.query == "192.168.1"
        assert search_request.subnet_id == 1
        assert search_request.status == "available"
        assert search_request.sort_by == "ip_address"
        assert search_request.sort_order == "asc"
    
    def test_invalid_sort_field(self):
        """测试无效的排序字段"""
        with pytest.raises(ValueError):
            IPSearchRequest(
                sort_by="invalid_field",
                skip=0,
                limit=50
            )
    
    def test_invalid_sort_order(self):
        """测试无效的排序方向"""
        with pytest.raises(ValueError):
            IPSearchRequest(
                sort_order="invalid_order",
                skip=0,
                limit=50
            )
    
    def test_invalid_ip_range(self):
        """测试无效的IP范围"""
        with pytest.raises(ValueError):
            IPSearchRequest(
                ip_range_start="invalid_ip",
                skip=0,
                limit=50
            )


if __name__ == "__main__":
    pytest.main([__file__])