// 通用接口定义
export interface BaseResponse<T = any> {
  code: number
  message: string
  success: boolean
  data?: T
}

export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// IP状态枚举
export enum IPStatus {
  Available = 'available',
  Allocated = 'allocated',
  Reserved = 'reserved',
  Blacklisted = 'blacklisted'
}

// 分配类型枚举
export enum AllocationType {
  Static = 'static',
  DHCP = 'dhcp',
  Reserved = 'reserved'
}

// 优先级枚举
export enum Priority {
  Low = 'low',
  Medium = 'medium',
  High = 'high',
  Critical = 'critical'
}

// 部门接口
export interface Department {
  id: number
  name: string
  code: string
  parent_id?: number
  description?: string
  created_at: string
  updated_at: string
  is_active: boolean
  children?: Department[]
  parent?: Department
}

export interface DepartmentCreate {
  name: string
  code: string
  parent_id?: number
  description?: string
  is_active?: boolean
}

export interface DepartmentUpdate {
  name?: string
  code?: string
  parent_id?: number
  description?: string
  is_active?: boolean
}

// 用户接口
export interface User {
  id: number
  username: string
  real_name: string
  email?: string
  phone?: string
  department_id?: number
  employee_id?: string
  position?: string
  created_at: string
  updated_at: string
  is_active: boolean
  department?: Department
  auth_source?: 'ldap' | 'local' // 添加认证来源字段
}

export interface UserCreate {
  username: string
  real_name: string
  email?: string
  phone?: string
  department_id?: number
  employee_id?: string
  position?: string
  is_active?: boolean
  auth_source?: 'ldap' | 'local' // 添加认证来源字段
}

export interface UserUpdate {
  username?: string
  real_name?: string
  email?: string
  phone?: string
  department_id?: number
  employee_id?: string
  position?: string
  is_active?: boolean
  auth_source?: 'ldap' | 'local' // 添加认证来源字段
}

// 网段接口
export interface NetworkSegment {
  id: number
  name: string
  network: string
  start_ip: string
  end_ip: string
  subnet_mask: string
  gateway?: string
  dns_servers?: string[]
  vlan_id?: number
  purpose?: string
  location?: string
  responsible_department_id?: number
  responsible_user_id?: number
  created_at: string
  updated_at: string
  is_active: boolean
  responsible_department?: Department
  responsible_user?: User
}

export interface NetworkSegmentCreate {
  name: string
  network: string
  start_ip: string
  end_ip: string
  subnet_mask: string
  gateway?: string
  dns_servers?: string[]
  vlan_id?: number
  purpose?: string
  location?: string
  responsible_department_id?: number
  responsible_user_id?: number
  is_active?: boolean
}

export interface NetworkSegmentUpdate {
  name?: string
  network?: string
  start_ip?: string
  end_ip?: string
  subnet_mask?: string
  gateway?: string
  dns_servers?: string[]
  vlan_id?: number
  purpose?: string
  location?: string
  responsible_department_id?: number
  responsible_user_id?: number
  is_active?: boolean
}

// IP地址接口
export interface IPAddress {
  id: number
  ip_address: string
  network_segment_id: number
  status: IPStatus
  allocation_type?: AllocationType
  device_name?: string
  device_type?: string
  mac_address?: string
  hostname?: string
  os_type?: string
  assigned_user_id?: number
  assigned_department_id?: number
  location?: string
  purpose?: string
  notes?: string
  allocated_at?: string
  expires_at?: string
  last_seen?: string
  created_at: string
  updated_at: string
  network_segment?: NetworkSegment
  assigned_user?: User
  assigned_department?: Department
}

export interface IPAddressCreate {
  ip_address: string
  network_segment_id: number
  status?: IPStatus
  allocation_type?: AllocationType
  device_name?: string
  device_type?: string
  mac_address?: string
  hostname?: string
  os_type?: string
  assigned_user_id?: number
  assigned_department_id?: number
  location?: string
  purpose?: string
  notes?: string
  allocated_at?: string
  expires_at?: string
  last_seen?: string
}

export interface IPAddressUpdate {
  status?: IPStatus
  allocation_type?: AllocationType
  device_name?: string
  device_type?: string
  mac_address?: string
  hostname?: string
  os_type?: string
  assigned_user_id?: number
  assigned_department_id?: number
  location?: string
  purpose?: string
  notes?: string
  allocated_at?: string
  expires_at?: string
  last_seen?: string
}

// 地址保留接口
export interface ReservedAddress {
  id: number
  ip_address: string
  network_segment_id: number
  reserved_for: string
  reserved_by_user_id: number
  reserved_by_department_id?: number
  start_date: string
  end_date?: string
  is_permanent: boolean
  priority: Priority
  notes?: string
  created_at: string
  updated_at: string
  is_active: boolean
  network_segment?: NetworkSegment
  reserved_by_user?: User
  reserved_by_department?: Department
}

export interface ReservedAddressCreate {
  ip_address: string
  network_segment_id: number
  reserved_for: string
  reserved_by_user_id: number
  reserved_by_department_id?: number
  start_date: string
  end_date?: string
  is_permanent?: boolean
  priority?: Priority
  notes?: string
  is_active?: boolean
}

export interface ReservedAddressUpdate {
  reserved_for?: string
  reserved_by_department_id?: number
  start_date?: string
  end_date?: string
  is_permanent?: boolean
  priority?: Priority
  notes?: string
  is_active?: boolean
}

// 统计数据接口
export interface NetworkSegmentStats {
  total_ips: number
  available_ips: number
  allocated_ips: number
  reserved_ips: number
  blacklisted_ips: number
  utilization_rate: number
}

export interface DashboardStats {
  total_segments: number
  total_ips: number
  allocated_ips: number
  available_ips: number
  reserved_ips: number
  total_users: number
  total_departments: number
}

// 查询参数接口
export interface QueryParams {
  skip?: number
  limit?: number
  search?: string
  [key: string]: any
}