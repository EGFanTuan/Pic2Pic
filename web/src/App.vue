<template>
  <div id="app">
    <header class="header">
      <h1>Pic2Pic Web UI</h1>
      <div class="status" :class="statusClass">{{ statusText }}</div>
    </header>
    
    <main class="main">
      <div class="canvas-section">
        <CanvasComponent 
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
        
        <div class="preview-section">
          <PreviewPanel 
            :stage1Url="stage1Url"
            :cannyUrl="cannyUrl"
            :finalUrl="finalUrl"
            :isGenerating="isGenerating"
            :progress="progress"
          />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CanvasComponent from './components/CanvasComponent.vue'
import ControlPanel from './components/ControlPanel.vue'
import PreviewPanel from './components/PreviewPanel.vue'
import StyleSelector from './components/StyleSelector.vue'
import ProgressBar from './components/ProgressBar.vue'
import { useApiStore } from './stores/api'

const apiStore = useApiStore()

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

const handlePreviewUpdate = (previewData) => {
  stage1Url.value = previewData.stage1
  cannyUrl.value = previewData.canny
}

const handlePreview = async () => {
  try {
    const result = await apiStore.preview({
      width: canvasWidth.value,
      height: canvasHeight.value,
      prompt: prompt.value,
      negative_prompt: negativePrompt.value,
      seed: seed.value,
      output_format: outputFormat.value
    })
    
    if (result.preview_urls) {
      stage1Url.value = result.preview_urls.stage1
      cannyUrl.value = result.preview_urls.canny
    }
    
    statusText.value = '预览已更新'
  } catch (error) {
    statusText.value = `预览失败：${error.message}`
  }
}

const handleStyleUpdate = (stylePrompt) => {
  selectedStyles.value = stylePrompt
}

const handleLoraUpdate = (loraConfig) => {
  selectedLora.value = loraConfig
}

const handleGenerate = async () => {
  try {
    isGenerating.value = true
    progress.value = 0
    statusText.value = '生成中...'
    progressDetails.value = '正在初始化模型...'
    
    const fullPrompt = [prompt.value, selectedStyles.value].filter(Boolean).join(', ')
    
    const params = {
      width: canvasWidth.value,
      height: canvasHeight.value,
      prompt: fullPrompt,
      negative_prompt: negativePrompt.value,
      seed: seed.value,
      output_format: outputFormat.value
    }
    
    if (selectedLora.value) {
      params.lora_id = selectedLora.value.id
      params.lora_weight = selectedLora.value.weight
    }
    
    const result = await apiStore.generate(params, (progressValue) => {
      progress.value = progressValue
      
      if (progressValue < 30) {
        progressDetails.value = 'Stage 1: 快速预览生成中...'
      } else if (progressValue < 70) {
        progressDetails.value = 'Stage 2: 精修生成中...'
      } else {
        progressDetails.value = '最终处理中...'
      }
    })
    
    if (result.preview_urls) {
      stage1Url.value = result.preview_urls.stage1
      cannyUrl.value = result.preview_urls.canny
      finalUrl.value = result.preview_urls.final
    }
    
    statusText.value = '生成完成'
  } catch (error) {
    statusText.value = `生成失败：${error.message}`
  } finally {
    isGenerating.value = false
  }
}

onMounted(async () => {
  try {
    await apiStore.fetchStatus()
    const defaults = apiStore.getDefaults
    if (defaults) {
      prompt.value = defaults.prompt || ''
      negativePrompt.value = defaults.negative_prompt || ''
      seed.value = defaults.seed || 143
      outputFormat.value = defaults.output_format || 'png'
      canvasWidth.value = defaults.width || 400
      canvasHeight.value = defaults.height || 600
    }
    statusText.value = `就绪（${apiStore.device || 'CPU'}）`
  } catch (error) {
    statusText.value = `初始化失败：${error.message}`
  }
})
</script>

<style scoped>
#app {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px 32px;
  border-bottom: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header:hover {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
}

.header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 12px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.status {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.status-ready {
  background: #dcfce7;
  color: #166534;
}

.status-generating {
  background: #dbeafe;
  color: #1e40af;
}

.status-error {
  background: #fee2e2;
  color: #991b1b;
}

.status-normal {
  background: #f3f4f6;
  color: #4b5563;
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
</style>
