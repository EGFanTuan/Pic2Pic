<template>
  <div class="progress-bar-container">
    <div class="progress-info">
      <span class="progress-label">{{ label }}</span>
      <span class="progress-percentage">{{ progress }}%</span>
    </div>
    <div class="progress-track">
      <div 
        class="progress-fill" 
        :style="{ width: `${progress}%` }"
        :class="{ 'progress-complete': progress >= 100 }"
      ></div>
    </div>
    <div v-if="showDetails && details" class="progress-details">
      {{ details }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  progress: {
    type: Number,
    default: 0,
    validator: (value) => value >= 0 && value <= 100
  },
  label: {
    type: String,
    default: '进度'
  },
  details: {
    type: String,
    default: ''
  },
  showDetails: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.progress-bar-container {
  width: 100%;
  padding: 16px;
  background: var(--panel);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}

.progress-percentage {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary);
}

.progress-track {
  width: 100%;
  height: 12px;
  background: var(--line);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #6366f1 100%);
  background-size: 200% 100%;
  border-radius: 10px;
  transition: width 0.4s ease;
  position: relative;
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.3);
  animation: progressShimmer 2s linear infinite;
}

@keyframes progressShimmer {
  0% { background-position: 100% 0%; }
  100% { background-position: -100% 0%; }
}

.progress-complete {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.progress-details {
  margin-top: 8px;
  font-size: 12px;
  color: var(--sub);
  text-align: center;
}
</style>
