<template>
  <div id="app">
    <header class="header">
      <div class="logo-area">
        <div class="logo-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 4L26 10V22L16 28L6 22V10L16 4Z" fill="url(#paint0_linear)" stroke="white" stroke-width="1.5"/>
            <path d="M16 8L22 11.5V20.5L16 24L10 20.5V11.5L16 8Z" fill="white" fill-opacity="0.2"/>
            <circle cx="16" cy="16" r="4" fill="white"/>
            <defs>
              <linearGradient id="paint0_linear" x1="6" y1="4" x2="26" y2="28" gradientUnits="userSpaceOnUse">
                <stop stop-color="#667eea"/>
                <stop offset="1" stop-color="#764ba2"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div class="logo-text">
          <span class="brand">Pic2Pic</span>
          <span class="version">v1.2 Pro</span>
        </div>
      </div>

      <div class="header-right">
        <div class="status-bar">
          <div class="device-info" :title="apiStore.gpu_name">
            <span class="device-label">硬件加速:</span>
            <div class="device-toggle-group">
              <button 
                class="device-toggle" 
                :class="{ 'active': apiStore.device === 'cuda' }"
                @click="handleDeviceSwitch('cuda')"
                :disabled="apiStore.status !== 'ready' || apiStore.busy"
              >GPU</button>
              <button 
                class="device-toggle" 
                :class="{ 'active': apiStore.device === 'cpu' }"
                @click="handleDeviceSwitch('cpu')"
                :disabled="apiStore.status !== 'ready' || apiStore.busy"
              >CPU</button>
            </div>
          </div>
          <div class="status-content" :class="statusClass">
            <span class="status-indicator"></span>
            <span class="status-text">{{ statusText }}</span>
          </div>
        </div>
      </div>
    </header>

    <div v-if="isGenerating" class="global-progress">
      <div class="progress-info">
        <span class="progress-label">{{ progressDetails }}</span>
        <span class="progress-percent">{{ Math.round(progress) }}%</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
    </div>
    
    <main class="main">
      <!-- Loading Overlay -->
      <div v-if="apiStore.status === 'initializing'" class="loading-overlay">
        <div class="loading-content">
          <div class="spinner"></div>
          <h2>正在加载模型...</h2>
          <p>首次加载可能需要几分钟，请稍候</p>
          <div class="loading-details">{{ statusText }}</div>
        </div>
      </div>

      <div class="canvas-section">
        <CanvasComponent 
          ref="canvasRef"
          :width="canvasWidth"
          :height="canvasHeight"
          :autoResize="true"
          @update:width="(newWidth) => canvasWidth = newWidth"
          @update:height="(newHeight) => canvasHeight = newHeight"
          @update:preview="handlePreviewUpdate"
        />
      </div>
      
      <div class="sidebar">
        <div class="controls-section">
          <ControlPanel 
            v-model:prompt="prompt"
            v-model:negativePrompt="negativePrompt"
            v-model:seed="seed"
            v-model:outputFormat="outputFormat"
            v-model:settingsMode="settingsMode"
            :canvasWidth="canvasWidth"
            :canvasHeight="canvasHeight"
            :isGenerating="isGenerating"
            @generate="handleGenerate"
            @preview="handlePreview"
          />
          
          <StyleSelector 
            @update:styles="handleStyleUpdate"
            @update:lora="handleLoraUpdate"
          />
          
          <ProgressBar 
            v-if="isGenerating"
            :progress="progress"
            label="生成进度"
            :details="progressDetails"
            :showDetails="true"
          />
        </div>
      </div>
    </main>

    <ResultModal 
      :show="showResultModal"
      :stage1Url="stage1Url"
      :cannyUrl="cannyUrl"
      :finalUrl="finalUrl"
      @close="showResultModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CanvasComponent from './components/CanvasComponent.vue'
import ControlPanel from './components/ControlPanel.vue'
import ResultModal from './components/ResultModal.vue'
import StyleSelector from './components/StyleSelector.vue'
import ProgressBar from './components/ProgressBar.vue'
import { useApiStore } from './stores/api'

const apiStore = useApiStore()
const canvasRef = ref(null)

const canvasWidth = ref(400)
const canvasHeight = ref(600)
const prompt = ref('')
const negativePrompt = ref('')
const seed = ref(143)
const outputFormat = ref('png')
const settingsMode = ref('basic')

const stage1Url = ref('')
const cannyUrl = ref('')
const finalUrl = ref('')
const isGenerating = ref(false)
const showResultModal = ref(false)
const progress = ref(0)
const progressDetails = ref('')
const selectedStyles = ref('')
const selectedLora = ref(null)

const statusText = ref('初始化中...')
const statusClass = computed(() => {
  if (isGenerating.value) return 'status-generating'
  if (statusText.value.includes('就绪')) return 'status-ready'
  if (statusText.value.includes('错误')) return 'status-error'
  return 'status-normal'
})

const pollProgress = async () => {
  if (!isGenerating.value) return
  try {
    await apiStore.fetchStatus()
    if (apiStore.progress && apiStore.progress.status !== 'idle') {
      progress.value = apiStore.progress.percentage
      progressDetails.value = apiStore.progress.details || 
        (apiStore.progress.status === 'previewing' ? '正在预览...' : '正在生成...')
    }
  } catch (e) {
    console.error('Polling progress failed:', e)
  }
  
  if (isGenerating.value) {
    setTimeout(pollProgress, 500)
  }
}

const handlePreviewUpdate = (previewData) => {
  stage1Url.value = previewData.stage1
  cannyUrl.value = previewData.canny
}

const handlePreview = async (extraParams = {}) => {
  try {
    isGenerating.value = true
    progress.value = 0
    progressDetails.value = '准备预览...'
    pollProgress()
    
    const imageBlob = await canvasRef.value.getImageBlob()
    const result = await apiStore.preview(imageBlob, {
      width: Math.floor(canvasWidth.value / 8) * 8,
      height: Math.floor(canvasHeight.value / 8) * 8,
      prompt: prompt.value,
      negative_prompt: negativePrompt.value,
      seed: seed.value,
      output_format: outputFormat.value,
      ...extraParams
    })
    
    if (result.preview_urls) {
      stage1Url.value = result.preview_urls.stage1
      cannyUrl.value = result.preview_urls.canny
      showResultModal.value = true
    }
    
    statusText.value = '预览已更新'
  } catch (error) {
    statusText.value = `预览失败：${error.message}`
  } finally {
    isGenerating.value = false
  }
}

const handleStyleUpdate = (stylePrompt) => {
  selectedStyles.value = stylePrompt
}

const handleLoraUpdate = (loraConfig) => {
  selectedLora.value = loraConfig
}

const handleGenerate = async (extraParams = {}) => {
  try {
    isGenerating.value = true
    progress.value = 0
    statusText.value = '生成中...'
    progressDetails.value = '正在初始化...'
    pollProgress()
    
    const fullPrompt = [prompt.value, selectedStyles.value].filter(Boolean).join(', ')
    
    const imageBlob = await canvasRef.value.getImageBlob()
    
    const params = {
      width: Math.floor(canvasWidth.value / 8) * 8,
      height: Math.floor(canvasHeight.value / 8) * 8,
      prompt: fullPrompt,
      negative_prompt: negativePrompt.value,
      seed: seed.value,
      output_format: outputFormat.value,
      ...extraParams
    }
    
    if (selectedLora.value) {
      params.lora_id = selectedLora.value.id
      params.lora_weight = selectedLora.value.weight
    }
    
    const result = await apiStore.generate(imageBlob, params)
    
    if (result.preview_urls) {
      stage1Url.value = result.preview_urls.stage1
      cannyUrl.value = result.preview_urls.canny
      finalUrl.value = result.preview_urls.final
      showResultModal.value = true
    }
    
    statusText.value = '生成完成'
  } catch (error) {
    statusText.value = `生成失败：${error.message}`
  } finally {
    isGenerating.value = false
  }
}

const handleDeviceSwitch = async (target) => {
  if (target === apiStore.device) return
  try {
    statusText.value = `正在切换到 ${target.toUpperCase()}...`
    await apiStore.switchDevice(target)
    const deviceDisplay = (apiStore.device === 'cuda' && apiStore.gpu_name) ? apiStore.gpu_name : target.toUpperCase()
    statusText.value = `切换成功（${deviceDisplay}）`
  } catch (error) {
    statusText.value = `切换失败：${error.message}`
  }
}

onMounted(async () => {
  const pollStatus = async () => {
    try {
      await apiStore.fetchStatus()
      const defaults = apiStore.getDefaults
      if (defaults) {
        prompt.value = prompt.value || defaults.prompt || ''
        negativePrompt.value = negativePrompt.value || defaults.negative_prompt || ''
        seed.value = seed.value || defaults.seed || 143
        outputFormat.value = outputFormat.value || defaults.output_format || 'png'
        canvasWidth.value = canvasWidth.value || defaults.width || 400
        canvasHeight.value = canvasHeight.value || defaults.height || 600
      }
      
      if (apiStore.status === 'ready') {
        const deviceDisplay = (apiStore.device === 'cuda' && apiStore.gpu_name) ? apiStore.gpu_name : (apiStore.device || 'CPU')
        statusText.value = `就绪（${deviceDisplay}）`
      } else {
        statusText.value = '模型加载中...'
        setTimeout(pollStatus, 3000)
      }
    } catch (error) {
      statusText.value = '等待服务器响应...'
      setTimeout(pollStatus, 3000)
    }
  }
  
  pollStatus()
})
</script>

<style scoped>
#app {
  min-height: 100vh;
  background: #0f172a;
  color: #f1f5f9;
  font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
}

.header {
  padding: 12px 32px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  filter: drop-shadow(0 4px 8px rgba(102, 126, 234, 0.3));
  transition: transform 0.3s ease;
}

.logo-icon:hover {
  transform: rotate(10deg) scale(1.1);
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.brand {
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}

.version {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: -4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #ffffff;
  padding: 4px 4px 4px 16px;
  border-radius: 30px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
}

.device-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.device-label {
  font-weight: 600;
  font-size: 12px;
  color: #64748b;
}

.device-toggle-group {
  display: flex;
  background: #f1f5f9;
  padding: 3px;
  border-radius: 8px;
  gap: 2px;
}

.device-toggle {
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.device-toggle.active {
  background: #ffffff;
  color: #667eea;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.status-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: #f8fafc;
  border-radius: 20px;
  min-width: 120px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
}

.status-ready .status-indicator { background: #10b981; box-shadow: 0 0 8px rgba(16, 185, 129, 0.5); }
.status-generating .status-indicator { background: #6366f1; box-shadow: 0 0 8px rgba(99, 102, 241, 0.5); animation: pulse 1.5s infinite; }
.status-error .status-indicator { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.5); }

.status-text {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  white-space: nowrap;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}

.global-progress {
  padding: 16px 32px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(15px);
  border-bottom: 2px solid rgba(102, 126, 234, 0.2);
  animation: slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  z-index: 90;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  align-items: center;
}

.progress-label {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-label::before {
  content: '';
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  box-shadow: 0 0 8px #667eea;
  animation: pulse 1.5s infinite;
}

.progress-percent {
  font-size: 18px;
  font-weight: 900;
  color: #4f46e5;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 10px rgba(79, 70, 229, 0.2);
}

.progress-track {
  height: 12px;
  background: #f1f5f9;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.03);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #6366f1 100%);
  background-size: 200% 100%;
  border-radius: 20px;
  transition: width 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
  animation: progressShimmer 2s linear infinite;
}

@keyframes progressShimmer {
  0% { background-position: 100% 0%; }
  100% { background-position: -100% 0%; }
}

@keyframes slideDown {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}


.main {
  display: flex;
  gap: 20px;
  padding: 24px;
  max-width: 1920px;
  margin: 0 auto;
  min-height: calc(100vh - 100px);
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  transition: all 0.3s ease;
}

.canvas-section {
  flex: 1;
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  min-width: 400px;
  transition: all 0.3s ease;
}

.canvas-section:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.sidebar {
  width: 380px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-shrink: 0;
}

.controls-section,
.preview-section {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  flex: 1;
  min-height: 400px;
  transition: all 0.3s ease;
}

.controls-section:hover,
.preview-section:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

@media (max-width: 1200px) {
  .main {
    flex-direction: column;
  }
  
  .canvas-section {
    min-height: 600px;
  }
  
  .sidebar {
    width: 100%;
    flex-direction: row;
  }
  
  .controls-section,
  .preview-section {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .sidebar {
    flex-direction: column;
  }
  
  .canvas-section {
    min-width: unset;
  }
  
  .main {
    padding: 16px;
    gap: 12px;
  }
  
  .header {
    padding: 16px 20px;
  }
  
  .header h1 {
    font-size: 20px;
  }
}

/* 全局动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.canvas-section,
.controls-section,
.preview-section {
  animation: fadeIn 0.5s ease-out;
}

/* 滚动条样式优化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #64748b;
  background: #f8fafc;
  padding: 6px 12px;
  border-radius: 20px;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-right: 8px;
  padding-right: 12px;
  border-right: 1px solid #e2e8f0;
}

.device-label {
  font-weight: 600;
  font-size: 12px;
  color: #94a3b8;
}

.device-toggle {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.device-toggle.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.device-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.gpu-name-text {
  font-size: 11px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 加载遮罩层样式 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  border-radius: 16px;
}

.loading-content {
  text-align: center;
  animation: fadeIn 0.5s ease-out;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 5px solid #f3f4f6;
  border-top: 5px solid #667eea;
  border-radius: 50%;
  margin: 0 auto 20px;
  animation: spin 1s linear infinite;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-details {
  margin-top: 15px;
  font-size: 14px;
  color: #667eea;
  font-weight: 600;
  background: #eef2ff;
  padding: 6px 16px;
  border-radius: 20px;
  display: inline-block;
}
</style>
