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
  background-color: var(--bg-color-page);
  color: var(--text-color-primary);
}
</style>