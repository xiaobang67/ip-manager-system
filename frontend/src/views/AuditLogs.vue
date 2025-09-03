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
  background-color: var(--bg-color-page);
  color: var(--text-color-primary);
}
</style>