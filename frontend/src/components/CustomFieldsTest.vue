<template>
  <div class="custom-fields-test">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>自定义字段测试</span>
          <el-button type="primary" @click="runTests">运行测试</el-button>
        </div>
      </template>

      <div class="test-results">
        <el-alert
          v-if="testStatus"
          :title="testStatus.title"
          :type="testStatus.type"
          :description="testStatus.description"
          show-icon
          :closable="false"
        />

        <div v-if="testResults.length > 0" class="results-list">
          <h3>测试结果：</h3>
          <el-timeline>
            <el-timeline-item
              v-for="(result, index) in testResults"
              :key="index"
              :type="result.success ? 'success' : 'danger'"
              :timestamp="result.timestamp"
            >
              <h4>{{ result.test }}</h4>
              <p>{{ result.message }}</p>
              <pre v-if="result.data" class="test-data">{{ JSON.stringify(result.data, null, 2) }}</pre>
            </el-timeline-item>
          </el-timeline>
        </div>

        <div v-if="customFields.length > 0" class="fields-preview">
          <h3>自定义字段预览：</h3>
          <el-table :data="customFields" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="field_name" label="字段名称" />
            <el-table-column prop="field_type" label="字段类型" />
            <el-table-column prop="entity_type" label="实体类型" />
            <el-table-column prop="is_required" label="必填">
              <template #default="scope">
                <el-tag :type="scope.row.is_required ? 'danger' : 'info'">
                  {{ scope.row.is_required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import customFieldsAPI from '@/api/customFields'
import { 
  customFieldsDebugger, 
  safeGetCustomFields, 
  safeGetEntityCustomFields 
} from '@/utils/customFieldsDebug'

export default {
  name: 'CustomFieldsTest',
  setup() {
    const testStatus = ref(null)
    const testResults = ref([])
    const customFields = ref([])

    const addTestResult = (test, success, message, data = null) => {
      testResults.value.push({
        test,
        success,
        message,
        data,
        timestamp: new Date().toLocaleString()
      })
    }

    const runTests = async () => {
      testStatus.value = {
        title: '正在运行测试...',
        type: 'info',
        description: '请稍候，正在检查自定义字段功能'
      }
      
      testResults.value = []
      customFields.value = []

      try {
        // 测试1: API健康检查
        console.log('开始API健康检查...')
        const healthCheck = await customFieldsDebugger.checkApiHealth()
        addTestResult(
          'API健康检查',
          healthCheck,
          healthCheck ? 'API连接正常' : 'API连接失败'
        )

        if (!healthCheck) {
          testStatus.value = {
            title: '测试失败',
            type: 'error',
            description: 'API连接失败，无法继续测试'
          }
          return
        }

        // 测试2: 获取所有自定义字段
        console.log('测试获取所有自定义字段...')
        try {
          const allFields = await safeGetCustomFields()
          addTestResult(
            '获取所有自定义字段',
            true,
            `成功获取 ${allFields.length} 个字段`,
            allFields
          )
          customFields.value = allFields
        } catch (error) {
          addTestResult(
            '获取所有自定义字段',
            false,
            `获取失败: ${error.message}`,
            error
          )
        }

        // 测试3: 获取IP类型字段
        console.log('测试获取IP类型字段...')
        try {
          const ipFields = await safeGetCustomFields('ip')
          addTestResult(
            '获取IP类型字段',
            true,
            `成功获取 ${ipFields.length} 个IP字段`,
            ipFields
          )
        } catch (error) {
          addTestResult(
            '获取IP类型字段',
            false,
            `获取失败: ${error.message}`,
            error
          )
        }

        // 测试4: 获取网段类型字段
        console.log('测试获取网段类型字段...')
        try {
          const subnetFields = await safeGetCustomFields('subnet')
          addTestResult(
            '获取网段类型字段',
            true,
            `成功获取 ${subnetFields.length} 个网段字段`,
            subnetFields
          )
        } catch (error) {
          addTestResult(
            '获取网段类型字段',
            false,
            `获取失败: ${error.message}`,
            error
          )
        }

        // 测试5: 获取实体字段（如果有IP地址的话）
        console.log('测试获取实体字段...')
        try {
          const entityFields = await safeGetEntityCustomFields('ip', 1)
          addTestResult(
            '获取实体字段',
            true,
            `成功获取实体字段，包含 ${entityFields.fields.length} 个字段`,
            entityFields
          )
        } catch (error) {
          addTestResult(
            '获取实体字段',
            false,
            `获取失败: ${error.message}`,
            error
          )
        }

        // 测试6: 直接API调用测试
        console.log('测试直接API调用...')
        try {
          const directResponse = await customFieldsAPI.getFields()
          addTestResult(
            '直接API调用',
            true,
            '直接API调用成功',
            directResponse
          )
        } catch (error) {
          addTestResult(
            '直接API调用',
            false,
            `直接API调用失败: ${error.message}`,
            {
              error: error.message,
              response: error.response?.data,
              status: error.response?.status
            }
          )
        }

        // 计算测试结果
        const successCount = testResults.value.filter(r => r.success).length
        const totalCount = testResults.value.length
        
        if (successCount === totalCount) {
          testStatus.value = {
            title: '所有测试通过',
            type: 'success',
            description: `${successCount}/${totalCount} 个测试成功通过`
          }
        } else {
          testStatus.value = {
            title: '部分测试失败',
            type: 'warning',
            description: `${successCount}/${totalCount} 个测试通过，请检查失败的测试项`
          }
        }

      } catch (error) {
        console.error('测试过程中发生错误:', error)
        testStatus.value = {
          title: '测试过程出错',
          type: 'error',
          description: `测试过程中发生错误: ${error.message}`
        }
        
        addTestResult(
          '测试过程',
          false,
          `测试过程出错: ${error.message}`,
          error
        )
      }
    }

    return {
      testStatus,
      testResults,
      customFields,
      runTests
    }
  }
}
</script>

<style scoped>
.custom-fields-test {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.test-results {
  margin-top: 20px;
}

.results-list {
  margin-top: 20px;
}

.fields-preview {
  margin-top: 30px;
}

.test-data {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}
</style>