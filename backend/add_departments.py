#!/usr/bin/env python3
"""
添加标准部门数据
"""
import pymysql
import os

DB_CONFIG = {
    'host': 'mysql',
    'user': 'ipam_user',
    'password': 'ipam_pass123',
    'database': 'ipam',
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def add_departments():
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            # 添加更多部门
            departments_data = [
                ('技术部', 'TECH'),
                ('运维部', 'OPS'),
                ('产品部', 'PRODUCT'),
                ('市场部', 'MARKETING'),
                ('人事部', 'HR'),
                ('客服部', 'SERVICE')
            ]
            
            for name, code in departments_data:
                cursor.execute('SELECT COUNT(*) as count FROM departments WHERE name = %s', (name,))
                if cursor.fetchone()['count'] == 0:
                    cursor.execute('INSERT INTO departments (name, code) VALUES (%s, %s)', (name, code))
                    print(f'添加部门: {name}')
            
            connection.commit()
            
            # 显示所有部门
            cursor.execute('SELECT * FROM departments ORDER BY name')
            departments = cursor.fetchall()
            print('\n当前所有部门:')
            for dept in departments:
                print(f'  ID: {dept["id"]}, 名称: {dept["name"]}, 编码: {dept["code"]}')
                
    finally:
        connection.close()

if __name__ == "__main__":
    add_departments()