<template>
  <div class="canvas-container">
    <div class="canvas-header">
      <h2>画布</h2>
    </div>

    <div class="canvas-toolbar">
      <button 
        :class="{ active: mode === 'draw' }" 
        @click="setMode('draw')"
        title="画笔 (B)"
      >
        🖊️ 画笔
      </button>
      <button 
        :class="{ active: mode === 'erase' }" 
        @click="setMode('erase')"
        title="橡皮擦 (E)"
      >
        🧹 橡皮擦
      </button>
      <button @click="undo" title="撤销 (Ctrl+Z)">↩️ 撤销</button>
      <button @click="clearCanvas" class="danger" title="清空画布">🗑️ 清空</button>
      <button @click="downloadCanvas" title="下载画布">💾 下载</button>
      <label class="upload-btn">
        <input type="file" accept="image/*" @change="handleUpload" ref="uploadInput">
        📁 上传
      </label>
      <select v-model="uploadScale" class="upload-scale-select">
        <option value="1">原始大小</option>
        <option value="0.75">0.75×</option>
        <option value="0.5">0.5×</option>
      </select>
    </div>

    <div class="brush-controls">
      <label>画笔大小: {{ lineWidth.toFixed(1) }}</label>
      <input 
        type="range" 
        v-model.number="lineWidth" 
        min="1" 
        max="50" 
        step="0.5"
        class="brush-size-slider"
      >
    </div>

    <div class="canvas-wrapper" ref="canvasWrapper">
      <canvas 
        ref="canvas"
        :width="width"
        :height="height"
        :style="canvasStyle"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
      ></canvas>
      <div class="canvas-size-indicator">
        {{ width }} × {{ height }}
      </div>
    </div>

    <div class="canvas-info">
      <span>尺寸: {{ width }} × {{ height }}</span>
      <span>快捷键: B-画笔 | E-橡皮擦 | Ctrl+Z-撤销</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  width: {
    type: Number,
    default: 512
  },
  height: {
    type: Number,
    default: 768
  },
  autoResize: {
    type: Boolean,
    default: false
  },
  maxWidth: {
    type: Number,
    default: 512
  },
  maxHeight: {
    type: Number,
    default: 768
  }
})

const emit = defineEmits(['update:width', 'update:height', 'update:preview'])

const canvas = ref(null)
const canvasWrapper = ref(null)
const uploadInput = ref(null)

const ctx = ref(null)
const mode = ref('draw')
const lineWidth = ref(3)
const uploadScale = ref('1')

const drawing = ref(false)
const lastX = ref(0)
const lastY = ref(0)

const history = ref([])
const maxHistory = 50

const canvasStyle = computed(() => ({
  cursor: mode.value === 'draw' ? 'crosshair' : 'cell'
}))

const initCanvas = () => {
  if (!canvas.value) return
  
  ctx.value = canvas.value.getContext('2d')
  drawGridBackground()
  saveToHistory()
}

const drawGridBackground = () => {
  if (!ctx.value || !canvas.value) return
  
  // Fill white background (no grid, to avoid interfering with ControlNet)
  ctx.value.fillStyle = '#ffffff'
  ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height)
}

const clearCanvas = () => {
  if (!ctx.value || !canvas.value) return
  
  drawGridBackground()
}

const saveToHistory = () => {
  if (!canvas.value) return
  
  const imageData = ctx.value.getImageData(0, 0, canvas.value.width, canvas.value.height)
  history.value.push(imageData)
  
  if (history.value.length > maxHistory) {
    history.value.shift()
  }
}

const undo = () => {
  if (history.value.length <= 1) return
  
  history.value.pop()
  const imageData = history.value[history.value.length - 1]
  ctx.value.putImageData(imageData, 0, 0)
  emit('update:preview')
}

const setMode = (newMode) => {
  mode.value = newMode
}

const getCanvasCoordinates = (event) => {
  const rect = canvas.value.getBoundingClientRect()
  
  const scaleX = canvas.value.width / rect.width
  const scaleY = canvas.value.height / rect.height
  
  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY
  }
}

const handleMouseDown = (event) => {
  event.preventDefault()
  drawing.value = true
  
  const coords = getCanvasCoordinates(event)
  lastX.value = coords.x
  lastY.value = coords.y
  
  ctx.value.beginPath()
  ctx.value.moveTo(coords.x, coords.y)
  ctx.value.lineCap = 'round'
  ctx.value.lineJoin = 'round'
  ctx.value.lineWidth = lineWidth.value
  
  if (mode.value === 'erase') {
    ctx.value.strokeStyle = '#ffffff'
  } else {
    ctx.value.strokeStyle = 'rgba(0, 0, 0, 0.5)'
  }
}

const handleMouseMove = (event) => {
  if (!drawing.value) return
  
  const coords = getCanvasCoordinates(event)
  
  ctx.value.lineWidth = lineWidth.value
  ctx.value.lineCap = 'round'
  ctx.value.lineJoin = 'round'
  ctx.value.globalCompositeOperation = 'source-over'
  
  if (mode.value === 'erase') {
    ctx.value.strokeStyle = '#ffffff'
  } else {
    ctx.value.strokeStyle = 'rgba(0, 0, 0, 0.5)'
  }
  
  ctx.value.lineTo(coords.x, coords.y)
  ctx.value.stroke()
  
  lastX.value = coords.x
  lastY.value = coords.y
}

const handleMouseUp = () => {
  if (drawing.value) {
    drawing.value = false
    ctx.value.closePath()
    ctx.value.globalCompositeOperation = 'source-over'
    saveToHistory()
    emit('update:preview')
  }
}

const getImageBlob = () => {
  return new Promise((resolve) => {
    if (!canvas.value) {
      resolve(null)
      return
    }
    canvas.value.toBlob((blob) => {
      resolve(blob)
    }, 'image/png')
  })
}

defineExpose({ getImageBlob })

const downloadCanvas = () => {
  const link = document.createElement('a')
  link.download = 'scribble_input.png'
  link.href = canvas.value.toDataURL('image/png')
  link.click()
}

const handleUpload = (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = (e) => {
    const img = new Image()
    img.onload = async () => {
      saveToHistory()
      
      // 将画布尺寸调整为上传图片的大小（对齐到8的倍数），应用缩放
      const scale = parseFloat(uploadScale.value)
      const scaledWidth = Math.round(img.width * scale)
      const scaledHeight = Math.round(img.height * scale)
      const newWidth = Math.max(64, Math.ceil(scaledWidth / 8) * 8)
      const newHeight = Math.max(64, Math.ceil(scaledHeight / 8) * 8)
      
      // 直接设置画布尺寸并绘制图片
      canvas.value.width = newWidth
      canvas.value.height = newHeight
      
      // 重获上下文（resize 后上下文状态被重置）
      ctx.value = canvas.value.getContext('2d')
      ctx.value.fillStyle = '#ffffff'
      ctx.value.fillRect(0, 0, newWidth, newHeight)
      
      // 居中绘制缩放后的图片（保持宽高比）
      const offsetX = Math.floor((newWidth - scaledWidth) / 2)
      const offsetY = Math.floor((newHeight - scaledHeight) / 2)
      ctx.value.drawImage(img, offsetX, offsetY, scaledWidth, scaledHeight)
      
      // 保存已绘制好的图像数据
      const savedImageData = ctx.value.getImageData(0, 0, newWidth, newHeight)
      
      // 发送尺寸变更（会触发 watcher → clearCanvas → putImageData）
      emit('update:width', newWidth)
      emit('update:height', newHeight)
      
      // 等 Vue 完成 watcher 处理后，确保图片正确恢复
      await nextTick()
      if (canvas.value.width === newWidth && canvas.value.height === newHeight) {
        ctx.value.putImageData(savedImageData, 0, 0)
      }
      
      emit('update:preview')
    }
    img.src = e.target.result
  }
  reader.readAsDataURL(file)
  
  event.target.value = ''
}

const handleKeyDown = (event) => {
  if (event.ctrlKey || event.metaKey) {
    if (event.key === 'z') {
      event.preventDefault()
      undo()
    }
  } else {
    if (event.key === 'b' || event.key === 'B') {
      setMode('draw')
    } else if (event.key === 'e' || event.key === 'E') {
      setMode('erase')
    }
  }
}

const resizeCanvas = () => {
  if (!props.autoResize || !canvasWrapper.value || !canvas.value) return
  
  const containerRect = canvasWrapper.value.getBoundingClientRect()
  
  // 获取画布容器的实际可用尺寸
  const availableWidth = Math.floor(containerRect.width)
  const availableHeight = Math.floor(containerRect.height)
  
  // 计算合适的画布尺寸，保持1:1.5的比例
  const targetWidth = Math.min(availableWidth, props.maxWidth)
  const targetHeight = Math.min(availableHeight, props.maxHeight)
  
  // 确保尺寸是8的倍数（SD要求）
  const finalWidth = Math.max(256, Math.floor(targetWidth / 8) * 8)
  const finalHeight = Math.max(256, Math.floor(targetHeight / 8) * 8)
  
  // 只有当尺寸确实变化时才更新
  if (finalWidth !== canvas.value.width || finalHeight !== canvas.value.height) {
    const imageData = ctx.value ? ctx.value.getImageData(0, 0, canvas.value.width, canvas.value.height) : null
    
    canvas.value.width = finalWidth
    canvas.value.height = finalHeight
    
    if (imageData) {
      clearCanvas()
      ctx.value.putImageData(imageData, 0, 0)
    } else {
      clearCanvas()
    }
    
    emit('update:width', finalWidth)
    emit('update:height', finalHeight)
  }
}

watch(() => props.width, () => {
  if (canvas.value) {
    const imageData = ctx.value.getImageData(0, 0, canvas.value.width, canvas.value.height)
    canvas.value.width = props.width
    canvas.value.height = props.height
    clearCanvas()
    ctx.value.putImageData(imageData, 0, 0)
  }
})

watch(() => props.height, () => {
  if (canvas.value) {
    const imageData = ctx.value.getImageData(0, 0, canvas.value.width, canvas.value.height)
    canvas.value.width = props.width
    canvas.value.height = props.height
    clearCanvas()
    ctx.value.putImageData(imageData, 0, 0)
  }
})

onMounted(() => {
  initCanvas()
  window.addEventListener('keydown', handleKeyDown)
  
  // 添加调整大小监听器
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<style scoped>
.canvas-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.canvas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.02);
}

.canvas-header h2 {
  margin: 0;
  font-size: 16px;
  color: var(--text);
}

.canvas-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.canvas-controls button {
  padding: 4px 8px;
  font-size: 12px;
}

.zoom-level {
  font-size: 12px;
  color: var(--sub);
  min-width: 50px;
  text-align: center;
}

.canvas-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
}

.brush-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.02);
}

.brush-controls label {
  margin: 0;
  font-size: 12px;
  white-space: nowrap;
}

.brush-size-slider {
  flex: 1;
  min-width: 100px;
}

.canvas-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecef 100%);
  padding: 20px;
  min-height: 400px;
  position: relative;
  border-radius: 8px;
}

canvas {
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15), 
              0 0 0 2px #667eea,
              inset 0 0 0 1px rgba(102, 126, 234, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  display: block;
  border-radius: 4px;
  cursor: crosshair;
}

canvas:hover {
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2), 
              0 0 0 3px #764ba2,
              inset 0 0 0 1px rgba(118, 75, 162, 0.1);
}

.canvas-size-indicator {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(102, 126, 234, 0.9);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  backdrop-filter: blur(8px);
}

.canvas-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-top: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.02);
  font-size: 12px;
  color: var(--sub);
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.upload-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}

.upload-btn input[type="file"] {
  display: none;
}

.upload-scale-select {
  padding: 8px 12px;
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: var(--border-radius);
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s;
}

.upload-scale-select:hover {
  border-color: var(--primary);
}
</style>
