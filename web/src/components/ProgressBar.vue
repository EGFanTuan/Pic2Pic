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
  background: #ffffff;
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
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), #60a5fa);
  border-radius: 4px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.progress-complete {
  background: linear-gradient(90deg, var(--ok), #34d399);
}

.progress-details {
  margin-top: 8px;
  font-size: 12px;
  color: var(--sub);
  text-align: center;
}
</style>
