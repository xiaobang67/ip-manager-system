<template>
  <AppLayout>
    <div class="dashboard">
      <MonitoringDashboard />
    </div>
  </AppLayout>
</template>

<script>
import AppLayout from '@/components/AppLayout.vue'
import MonitoringDashboard from '@/components/MonitoringDashboard.vue'

export default {
  name: 'Dashboard',
  components: {
    AppLayout,
    MonitoringDashboard
  }
}
</script>

<style scoped>
.dashboard {
  background-color: var(--bg-primary-page);
  color: var(--text-primary);
}
</style>