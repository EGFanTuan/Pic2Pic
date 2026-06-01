<template>
  <div class="preview-panel">
    <div class="panel-header">
      <h2>预览面板</h2>
      <div v-if="isGenerating" class="generating-indicator">
        <div class="spinner"></div>
        <span>生成中 {{ progress }}%</span>
      </div>
    </div>

    <div class="panel-body">
      <div class="preview-section">
        <h3>Stage 1 预览</h3>
        <div class="preview-container">
          <img 
            v-if="stage1Url" 
            :src="stage1Url" 
            alt="Stage 1 Preview"
            @click="openImage(stage1Url)"
          >
          <div v-else class="placeholder">
            <span>暂无预览</span>
          </div>
        </div>
      </div>

      <div class="preview-section">
        <h3>Canny 边缘</h3>
        <div class="preview-container">
          <img 
            v-if="cannyUrl" 
            :src="cannyUrl" 
            alt="Canny Preview"
            @click="openImage(cannyUrl)"
          >
          <div v-else class="placeholder">
            <span>暂无预览</span>
          </div>
        </div>
      </div>

      <div class="preview-section">
        <h3>最终结果</h3>
        <div class="preview-container">
          <img 
            v-if="finalUrl" 
            :src="finalUrl" 
            alt="Final Result"
            @click="openImage(finalUrl)"
          >
          <div v-else class="placeholder">
            <span>暂无结果</span>
          </div>
        </div>
      </div>

      <div v-if="finalUrl" class="download-actions">
        <button @click="downloadImage(finalUrl, 'final_result')" class="primary">
          💾 下载最终结果
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

defineProps({
  stage1Url: String,
  cannyUrl: String,
  finalUrl: String,
  isGenerating: Boolean,
  progress: {
    type: Number,
    default: 0
  }
})

const openImage = (url) => {
  window.open(url, '_blank')
}

const downloadImage = (url, filename) => {
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}.png`
  link.click()
}
</script>

<style scoped>
.preview-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  color: var(--text);
}

.generating-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--primary);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--line);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.preview-section {
  margin-bottom: 20px;
}

.preview-section h3 {
  font-size: 14px;
  color: var(--text);
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
}

.preview-container {
  background: rgba(255, 255, 255, 0.02);
  border: 2px dashed var(--line);
  border-radius: 8px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.preview-container img {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
  cursor: pointer;
  transition: transform 0.2s;
}

.preview-container img:hover {
  transform: scale(1.02);
}

.placeholder {
  color: var(--sub);
  font-size: 14px;
  text-align: center;
  padding: 20px;
}

.download-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
}

.download-actions button {
  width: 100%;
  padding: 12px;
}
</style>
