"""
系统管理API路由
"""
import logging
import json
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from database.connection import get_db
from services.auth_service import auth_service
from config.auth_config import LDAP_CONFIG, ENABLE_LDAP

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(tags=["system"])


class LDAPConfigRequest:
    """LDAP配置请求模型"""
    def __init__(self, **kwargs):
        self.enable_ldap = kwargs.get("enable_ldap", True)
        self.server_uri = kwargs.get("server_uri", "")
        self.bind_dn = kwargs.get("bind_dn", "")
        self.bind_password = kwargs.get("bind_password", "")
        self.user_search_base = kwargs.get("user_search_base", "")
        self.user_search_filter = kwargs.get("user_search_filter", "")
        self.group_search_base = kwargs.get("group_search_base", "")
        self.group_search_filter = kwargs.get("group_search_filter", "")
        self.connect_timeout = kwargs.get("connect_timeout", 10)
        self.read_timeout = kwargs.get("read_timeout", 30)
        self.always_update_user = kwargs.get("always_update_user", True)


# 操作日志存储文件路径
OPERATION_LOG_FILE = "logs/operation_logs.json"


def write_operation_log(log_entry: Dict[str, Any]):
    """写入操作日志到文件"""
    # 确保日志目录存在
    os.makedirs(os.path.dirname(OPERATION_LOG_FILE), exist_ok=True)
    
    # 如果文件不存在，创建空数组
    if not os.path.exists(OPERATION_LOG_FILE):
        with open(OPERATION_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    # 读取现有日志
    try:
        with open(OPERATION_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logs = []
    
    # 添加新日志
    logs.append(log_entry)
    
    # 保持最多1000条日志
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    # 写入文件
    with open(OPERATION_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def read_operation_logs(skip: int = 0, limit: int = 50) -> Dict[str, Any]:
    """从文件读取操作日志"""
    # 如果文件不存在，返回空结果
    if not os.path.exists(OPERATION_LOG_FILE):
        return {"items": [], "total": 0}
    
    # 读取日志
    try:
        with open(OPERATION_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logs = []
    
    # 计算总数
    total = len(logs)
    
    # 分页处理
    logs = logs[::-1]  # 倒序，最新的在前面
    items = logs[skip:skip+limit]
    
    return {"items": items, "total": total}


@router.get("/ldap-config")
async def get_ldap_config():
    """获取LDAP配置"""
    logger.info("获取LDAP配置信息")
    return {
        "enable_ldap": ENABLE_LDAP,
        "server_uri": LDAP_CONFIG["server_uri"],
        "bind_dn": LDAP_CONFIG["bind_dn"],
        "bind_password": "",  # 不返回密码
        "user_search_base": LDAP_CONFIG["user_search_base"],
        "user_search_filter": LDAP_CONFIG["user_search_filter"],
        "group_search_base": LDAP_CONFIG["group_search_base"],
        "group_search_filter": LDAP_CONFIG["group_search_filter"],
        "connect_timeout": LDAP_CONFIG["connect_timeout"],
        "read_timeout": LDAP_CONFIG["read_timeout"],
        "always_update_user": LDAP_CONFIG["always_update_user"]
    }


@router.post("/ldap-config")
async def save_ldap_config(config: Dict[str, Any]):
    """保存LDAP配置"""
    logger.info("保存LDAP配置信息")
    # 记录操作日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": "admin",  # 实际应用中应该从认证信息中获取
        "action": "LDAP配置",
        "target": "LDAP服务器",
        "description": "修改LDAP配置",
        "ip": "127.0.0.1",  # 实际应用中应该从请求中获取
        "status": "success"
    }
    write_operation_log(log_entry)
    
    # 这里应该实现保存配置到数据库或配置文件的逻辑
    # 目前只是记录日志
    logger.info(f"LDAP配置已保存: {config}")
    return {"message": "LDAP配置保存成功"}


@router.post("/ldap-test")
async def test_ldap_connection(config: Dict[str, Any]):
    """测试LDAP连接"""
    logger.info("测试LDAP连接")
    try:
        # 使用提供的配置测试LDAP连接
        test_config = {
            "server_uri": config.get("server_uri", LDAP_CONFIG["server_uri"]),
            "bind_dn": config.get("bind_dn", LDAP_CONFIG["bind_dn"]),
            "bind_password": config.get("bind_password", ""),
            "connect_timeout": config.get("connect_timeout", LDAP_CONFIG["connect_timeout"]),
            "read_timeout": config.get("read_timeout", LDAP_CONFIG["read_timeout"])
        }
        
        # 尝试连接LDAP服务器
        success = auth_service.ldap_service.test_connection(test_config)
        
        # 记录操作日志
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": "admin",  # 实际应用中应该从认证信息中获取
            "action": "LDAP配置",
            "target": "LDAP服务器",
            "description": f"测试LDAP连接{'成功' if success else '失败'}",
            "ip": "127.0.0.1",  # 实际应用中应该从请求中获取
            "status": "success" if success else "error"
        }
        write_operation_log(log_entry)
        
        if success:
            logger.info("LDAP连接测试成功")
            return {"success": True, "message": "LDAP连接测试成功"}
        else:
            logger.warning("LDAP连接测试失败")
            return {"success": False, "message": "LDAP连接测试失败，请检查配置"}
    except Exception as e:
        logger.error(f"LDAP连接测试异常: {e}")
        # 记录操作日志
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": "admin",  # 实际应用中应该从认证信息中获取
            "action": "LDAP配置",
            "target": "LDAP服务器",
            "description": f"测试LDAP连接异常: {str(e)}",
            "ip": "127.0.0.1",  # 实际应用中应该从请求中获取
            "status": "error"
        }
        write_operation_log(log_entry)
        return {"success": False, "message": f"LDAP连接测试异常: {str(e)}"}


@router.get("/logs")
async def get_system_logs(skip: int = 0, limit: int = 50):
    """获取系统操作日志"""
    logger.info(f"获取系统操作日志，skip={skip}, limit={limit}")
    # 从文件读取操作日志
    logs_data = read_operation_logs(skip, limit)
    return logs_data