"""
操作系统类型API路由
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_os_types():
    """获取操作系统类型选项"""
    return [
        {"label": "Windows Server 2019", "value": "Windows Server 2019"},
        {"label": "Windows Server 2022", "value": "Windows Server 2022"},
        {"label": "Windows 10", "value": "Windows 10"},
        {"label": "Windows 11", "value": "Windows 11"},
        {"label": "Ubuntu 20.04", "value": "Ubuntu 20.04"},
        {"label": "Ubuntu 22.04", "value": "Ubuntu 22.04"},
        {"label": "CentOS 7", "value": "CentOS 7"},
        {"label": "CentOS 8", "value": "CentOS 8"},
        {"label": "Debian 10", "value": "Debian 10"},
        {"label": "Debian 11", "value": "Debian 11"},
        {"label": "Red Hat Enterprise Linux 8", "value": "Red Hat Enterprise Linux 8"},
        {"label": "Red Hat Enterprise Linux 9", "value": "Red Hat Enterprise Linux 9"},
        {"label": "SUSE Linux Enterprise 15", "value": "SUSE Linux Enterprise 15"},
        {"label": "macOS Monterey", "value": "macOS Monterey"},
        {"label": "macOS Ventura", "value": "macOS Ventura"},
        {"label": "macOS Sonoma", "value": "macOS Sonoma"},
        {"label": "VMware vSphere ESXi 7", "value": "VMware vSphere ESXi 7"},
        {"label": "VMware vSphere ESXi 8", "value": "VMware vSphere ESXi 8"},
        {"label": "其他", "value": "其他"}
    ]