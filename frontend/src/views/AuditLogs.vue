<template>
  <AppLayout>
    <div class="audit-logs-page">
      <AuditLogsManagement />
    </div>
  </AppLayout>
</template>

<script>
import AppLayout from '@/components/AppLayout.vue'
import AuditLogsManagement from '@/components/AuditLogsManagement.vue'

export default {
  name: 'AuditLogs',
  components: {
    AppLayout,
    AuditLogsManagement
  }
}
</script>

<style scoped>
.audit-logs-page {
  background-color: var(--bg-primary-page);
  color: var(--text-primary);
}
</style>