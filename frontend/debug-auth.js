/**
 * 认证调试脚本
 * 用于测试和调试认证相关问题
 */

// 检查localStorage中的认证数据
function checkAuthData() {
  console.log('=== 认证数据检查 ===')
  
  const accessToken = localStorage.getItem('access_token')
  const refreshToken = localStorage.getItem('refresh_token')
  const user = localStorage.getItem('user')
  
  console.log('Access Token:', accessToken ? '存在' : '不存在')
  console.log('Refresh Token:', refreshToken ? '存在' : '不存在')
  console.log('User Data:', user ? '存在' : '不存在')
  
  if (accessToken) {
    try {
      const tokenPayload = JSON.parse(atob(accessToken.split('.')[1]))
      console.log('Token Payload:', tokenPayload)
      console.log('Token Username:', tokenPayload.username)
      console.log('Token Role:', tokenPayload.role)
      console.log('Token Expiry:', new Date(tokenPayload.exp * 1000))
    } catch (error) {
      console.error('Token解析失败:', error)
    }
  }
  
  if (user) {
    try {
      const userData = JSON.parse(user)
      console.log('Stored User:', userData)
      console.log('Stored Username:', userData.username)
      console.log('Stored Role:', userData.role)
    } catch (error) {
      console.error('用户数据解析失败:', error)
    }
  }
  
  // 检查一致性
  if (accessToken && user) {
    try {
      const tokenPayload = JSON.parse(atob(accessToken.split('.')[1]))
      const userData = JSON.parse(user)
      
      if (tokenPayload.username === userData.username) {
        console.log('✅ Token与用户数据一致')
      } else {
        console.log('❌ Token与用户数据不一致!')
        console.log('Token用户名:', tokenPayload.username)
        console.log('存储用户名:', userData.username)
      }
    } catch (error) {
      console.error('一致性检查失败:', error)
    }
  }
}

// 清除所有认证数据
function clearAllAuthData() {
  console.log('=== 清除所有认证数据 ===')
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
  sessionStorage.clear()
  console.log('认证数据已清除')
}

// 模拟用户切换问题
function simulateUserSwitchIssue() {
  console.log('=== 模拟用户切换问题 ===')
  
  // 模拟admin用户的token和数据
  const adminToken = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTk5OTk5OTk5OSwidHlwZSI6ImFjY2VzcyJ9.fake'
  const adminUser = {
    id: 1,
    username: 'admin',
    role: 'admin',
    email: 'admin@example.com'
  }
  
  // 模拟普通用户的数据但使用admin的token
  const normalUser = {
    id: 2,
    username: 'user1',
    role: 'user',
    email: 'user1@example.com'
  }
  
  localStorage.setItem('access_token', adminToken)
  localStorage.setItem('user', JSON.stringify(normalUser))
  
  console.log('已设置不一致的认证数据')
  console.log('Token用户: admin')
  console.log('存储用户: user1')
  
  // 检查我们的修复是否能检测到这个问题
  checkAuthData()
}

// 在浏览器控制台中可用的全局函数
window.debugAuth = {
  check: checkAuthData,
  clear: clearAllAuthData,
  simulate: simulateUserSwitchIssue
}

console.log('认证调试工具已加载')
console.log('使用方法:')
console.log('- debugAuth.check() - 检查当前认证数据')
console.log('- debugAuth.clear() - 清除所有认证数据')
console.log('- debugAuth.simulate() - 模拟用户切换问题')