"""
报告服务 - 处理报告生成和导出
"""
import os
import uuid
import json
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.models.user import User
from app.services.monitoring_service import MonitoringService
from app.schemas.monitoring import ReportRequest, ReportResponse, ReportFormat
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.reports_dir = "reports"
        self.ensure_reports_directory()

    def ensure_reports_directory(self):
        """确保报告目录存在"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)

    def generate_report(
        self, 
        report_request: ReportRequest, 
        user_id: int, 
        background_tasks: BackgroundTasks
    ) -> ReportResponse:
        """
        生成报告
        """
        report_id = str(uuid.uuid4())
        
        # 在后台任务中生成报告
        background_tasks.add_task(
            self._generate_report_task,
            report_id,
            report_request,
            user_id
        )

        return ReportResponse(
            report_id=report_id,
            report_type=report_request.report_type,
            format=report_request.format.value,
            file_url=f"/api/v1/monitoring/reports/{report_id}/download",
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

    def _generate_report_task(
        self, 
        report_id: str, 
        report_request: ReportRequest, 
        user_id: int
    ):
        """
        后台任务：生成报告文件
        """
        try:
            monitoring_service = MonitoringService(self.db)
            
            # 根据报告类型获取数据
            if report_request.report_type == "utilization":
                data = self._get_utilization_report_data(monitoring_service, report_request)
            elif report_request.report_type == "inventory":
                data = self._get_inventory_report_data(monitoring_service, report_request)
            elif report_request.report_type == "subnet_planning":
                data = self._get_subnet_planning_report_data(monitoring_service, report_request)
            else:
                raise ValueError(f"不支持的报告类型: {report_request.report_type}")

            # 根据格式生成文件
            if report_request.format == ReportFormat.PDF:
                file_path = self._generate_pdf_report(report_id, data, report_request)
            elif report_request.format == ReportFormat.CSV:
                file_path = self._generate_csv_report(report_id, data, report_request)
            elif report_request.format == ReportFormat.EXCEL:
                file_path = self._generate_excel_report(report_id, data, report_request)
            elif report_request.format == ReportFormat.JSON:
                file_path = self._generate_json_report(report_id, data, report_request)
            else:
                raise ValueError(f"不支持的报告格式: {report_request.format}")

            # 保存报告元数据（这里可以扩展为数据库存储）
            self._save_report_metadata(report_id, report_request, user_id, file_path)

        except Exception as e:
            # 记录错误日志
            print(f"报告生成失败 {report_id}: {str(e)}")

    def _get_utilization_report_data(
        self, 
        monitoring_service: MonitoringService, 
        report_request: ReportRequest
    ) -> Dict[str, Any]:
        """
        获取使用率报告数据
        """
        ip_stats = monitoring_service.calculate_ip_utilization_stats()
        subnet_stats = monitoring_service.calculate_subnet_utilization_stats()
        
        # 如果指定了特定网段，过滤数据
        if report_request.subnet_ids:
            subnet_stats = [s for s in subnet_stats if s['subnet_id'] in report_request.subnet_ids]

        # 获取趋势数据
        trends = monitoring_service.get_ip_allocation_trends(30)

        return {
            "report_type": "IP地址使用率报告",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": ip_stats,
            "subnet_details": subnet_stats,
            "allocation_trends": trends
        }

    def _get_inventory_report_data(
        self, 
        monitoring_service: MonitoringService, 
        report_request: ReportRequest
    ) -> Dict[str, Any]:
        """
        获取清单报告数据
        """
        # 获取IP地址清单
        query = self.db.query(IPAddress)
        
        if report_request.subnet_ids:
            query = query.filter(IPAddress.subnet_id.in_(report_request.subnet_ids))

        ip_addresses = query.all()

        # 转换为字典格式
        ip_list = []
        for ip in ip_addresses:
            ip_data = {
                "ip_address": ip.ip_address,
                "subnet_network": ip.subnet.network if ip.subnet else "",
                "status": ip.status.value,
                "mac_address": ip.mac_address or "",
                "hostname": ip.hostname or "",
                "device_type": ip.device_type or "",
                "location": ip.location or "",
                "assigned_to": ip.assigned_to or "",
                "description": ip.description or "",
                "allocated_at": ip.allocated_at.isoformat() if ip.allocated_at else "",
                "created_at": ip.created_at.isoformat()
            }
            ip_list.append(ip_data)

        return {
            "report_type": "IP地址清单报告",
            "generated_at": datetime.utcnow().isoformat(),
            "total_count": len(ip_list),
            "ip_addresses": ip_list
        }

    def _get_subnet_planning_report_data(
        self, 
        monitoring_service: MonitoringService, 
        report_request: ReportRequest
    ) -> Dict[str, Any]:
        """
        获取网段规划报告数据
        """
        subnet_stats = monitoring_service.calculate_subnet_utilization_stats()
        
        if report_request.subnet_ids:
            subnet_stats = [s for s in subnet_stats if s['subnet_id'] in report_request.subnet_ids]

        # 添加规划建议
        for subnet in subnet_stats:
            subnet['planning_recommendation'] = self._get_subnet_planning_recommendation(subnet)

        return {
            "report_type": "网段规划报告",
            "generated_at": datetime.utcnow().isoformat(),
            "subnet_analysis": subnet_stats
        }

    def _get_subnet_planning_recommendation(self, subnet_stats: Dict[str, Any]) -> str:
        """
        获取网段规划建议
        """
        utilization = subnet_stats['utilization_rate']
        
        if utilization >= 90:
            return "紧急：使用率过高，建议立即扩容或添加新网段"
        elif utilization >= 80:
            return "警告：使用率较高，建议规划扩容"
        elif utilization >= 60:
            return "注意：使用率中等，可考虑未来扩容计划"
        elif utilization >= 30:
            return "正常：使用率适中，继续监控"
        else:
            return "良好：使用率较低，资源充足"

    def _generate_pdf_report(
        self, 
        report_id: str, 
        data: Dict[str, Any], 
        report_request: ReportRequest
    ) -> str:
        """
        生成PDF报告
        """
        file_path = os.path.join(self.reports_dir, f"{report_id}.pdf")
        
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # 标题
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # 居中
        )
        story.append(Paragraph(data['report_type'], title_style))
        story.append(Spacer(1, 12))

        # 生成时间
        story.append(Paragraph(f"生成时间: {data['generated_at']}", styles['Normal']))
        story.append(Spacer(1, 12))

        if report_request.report_type == "utilization":
            self._add_utilization_content_to_pdf(story, data, styles)
        elif report_request.report_type == "inventory":
            self._add_inventory_content_to_pdf(story, data, styles)
        elif report_request.report_type == "subnet_planning":
            self._add_subnet_planning_content_to_pdf(story, data, styles)

        doc.build(story)
        return file_path

    def _add_utilization_content_to_pdf(self, story, data, styles):
        """添加使用率报告内容到PDF"""
        # 汇总统计
        story.append(Paragraph("使用率汇总", styles['Heading2']))
        summary = data['summary']
        
        summary_data = [
            ['指标', '数值'],
            ['总IP数量', str(summary['total_ips'])],
            ['已分配IP', str(summary['allocated_ips'])],
            ['保留IP', str(summary['reserved_ips'])],
            ['可用IP', str(summary['available_ips'])],
            ['使用率', f"{summary['utilization_rate']}%"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 12))

        # 网段详情
        if data['subnet_details']:
            story.append(Paragraph("网段使用率详情", styles['Heading2']))
            
            subnet_data = [['网段', 'VLAN', '总IP', '已用IP', '使用率']]
            for subnet in data['subnet_details'][:10]:  # 限制显示数量
                subnet_data.append([
                    subnet['network'],
                    str(subnet['vlan_id']) if subnet['vlan_id'] else 'N/A',
                    str(subnet['total_ips']),
                    str(subnet['allocated_ips'] + subnet['reserved_ips']),
                    f"{subnet['utilization_rate']}%"
                ])
            
            subnet_table = Table(subnet_data)
            subnet_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(subnet_table)

    def _add_inventory_content_to_pdf(self, story, data, styles):
        """添加清单报告内容到PDF"""
        story.append(Paragraph(f"总计: {data['total_count']} 个IP地址", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # IP地址列表（限制显示数量）
        ip_data = [['IP地址', '网段', '状态', '主机名', '设备类型']]
        for ip in data['ip_addresses'][:50]:  # 限制显示50个
            ip_data.append([
                ip['ip_address'],
                ip['subnet_network'],
                ip['status'],
                ip['hostname'][:20] if ip['hostname'] else 'N/A',
                ip['device_type'][:15] if ip['device_type'] else 'N/A'
            ])
        
        ip_table = Table(ip_data)
        ip_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(ip_table)

    def _add_subnet_planning_content_to_pdf(self, story, data, styles):
        """添加网段规划报告内容到PDF"""
        for subnet in data['subnet_analysis']:
            story.append(Paragraph(f"网段: {subnet['network']}", styles['Heading3']))
            
            planning_data = [
                ['指标', '值'],
                ['使用率', f"{subnet['utilization_rate']}%"],
                ['总IP数', str(subnet['total_ips'])],
                ['已分配IP', str(subnet['allocated_ips'])],
                ['可用IP', str(subnet['available_ips'])],
                ['规划建议', subnet['planning_recommendation']]
            ]
            
            planning_table = Table(planning_data)
            planning_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(planning_table)
            story.append(Spacer(1, 12))

    def _generate_csv_report(
        self, 
        report_id: str, 
        data: Dict[str, Any], 
        report_request: ReportRequest
    ) -> str:
        """
        生成CSV报告
        """
        file_path = os.path.join(self.reports_dir, f"{report_id}.csv")
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            if report_request.report_type == "inventory":
                fieldnames = [
                    'ip_address', 'subnet_network', 'status', 'mac_address', 
                    'hostname', 'device_type', 'location', 'assigned_to', 
                    'description', 'allocated_at', 'created_at'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data['ip_addresses'])
            
            elif report_request.report_type == "utilization":
                fieldnames = [
                    'subnet_id', 'network', 'total_ips', 'allocated_ips', 
                    'reserved_ips', 'available_ips', 'utilization_rate'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data['subnet_details'])

        return file_path

    def _generate_excel_report(
        self, 
        report_id: str, 
        data: Dict[str, Any], 
        report_request: ReportRequest
    ) -> str:
        """
        生成Excel报告
        """
        file_path = os.path.join(self.reports_dir, f"{report_id}.xlsx")
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            if report_request.report_type == "inventory":
                df = pd.DataFrame(data['ip_addresses'])
                df.to_excel(writer, sheet_name='IP地址清单', index=False)
            
            elif report_request.report_type == "utilization":
                # 汇总数据
                summary_df = pd.DataFrame([data['summary']])
                summary_df.to_excel(writer, sheet_name='使用率汇总', index=False)
                
                # 网段详情
                subnet_df = pd.DataFrame(data['subnet_details'])
                subnet_df.to_excel(writer, sheet_name='网段详情', index=False)
                
                # 趋势数据
                trends_df = pd.DataFrame(data['allocation_trends'])
                trends_df.to_excel(writer, sheet_name='分配趋势', index=False)
            
            elif report_request.report_type == "subnet_planning":
                df = pd.DataFrame(data['subnet_analysis'])
                df.to_excel(writer, sheet_name='网段规划分析', index=False)

        return file_path

    def _generate_json_report(
        self, 
        report_id: str, 
        data: Dict[str, Any], 
        report_request: ReportRequest
    ) -> str:
        """
        生成JSON报告
        """
        file_path = os.path.join(self.reports_dir, f"{report_id}.json")
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2, default=str)

        return file_path

    def _save_report_metadata(
        self, 
        report_id: str, 
        report_request: ReportRequest, 
        user_id: int, 
        file_path: str
    ):
        """
        保存报告元数据
        """
        metadata = {
            "report_id": report_id,
            "report_type": report_request.report_type,
            "format": report_request.format.value,
            "user_id": user_id,
            "file_path": file_path,
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        metadata_path = os.path.join(self.reports_dir, f"{report_id}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def get_report_status(self, report_id: str) -> Dict[str, Any]:
        """
        获取报告状态
        """
        metadata_path = os.path.join(self.reports_dir, f"{report_id}_metadata.json")
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="报告不存在")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 检查文件是否存在
        file_exists = os.path.exists(metadata['file_path'])
        
        return {
            "report_id": report_id,
            "status": "completed" if file_exists else "failed",
            "generated_at": metadata['generated_at'],
            "expires_at": metadata['expires_at'],
            "download_url": f"/api/v1/monitoring/reports/{report_id}/download" if file_exists else None
        }

    def download_report(self, report_id: str):
        """
        下载报告文件
        """
        metadata_path = os.path.join(self.reports_dir, f"{report_id}_metadata.json")
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="报告不存在")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        file_path = metadata['file_path']
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="报告文件不存在")
        
        # 检查是否过期
        expires_at = datetime.fromisoformat(metadata['expires_at'])
        if datetime.utcnow() > expires_at:
            raise HTTPException(status_code=410, detail="报告已过期")
        
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type='application/octet-stream'
        )