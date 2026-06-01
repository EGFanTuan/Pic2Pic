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
    </div>

    <div class="canvas-info">
      <span>尺寸: {{ width }} × {{ height }}</span>
      <span>快捷键: B-画笔 | E-橡皮擦 | Ctrl+Z-撤销</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  width: {
    type: Number,
    default: 800
  },
  height: {
    type: Number,
    default: 1000
  },
  autoResize: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:width', 'update:height', 'update:preview'])

const canvas = ref(null)
const canvasWrapper = ref(null)
const uploadInput = ref(null)

const ctx = ref(null)
const mode = ref('draw')
const lineWidth = ref(3)

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
  clearCanvas()
  saveToHistory()
}

const clearCanvas = () => {
  if (!ctx.value || !canvas.value) return
  
  ctx.value.fillStyle = '#ffffff'
  ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height)
  ctx.value.lineCap = 'round'
  ctx.value.lineJoin = 'round'
  ctx.value.strokeStyle = 'rgba(0, 0, 0, 0.5)'
  ctx.value.lineWidth = lineWidth.value
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
  
  // 考虑到 object-fit: contain 引起的缩放和 letterboxing（留白）
  const scale = Math.min(rect.width / canvas.value.width, rect.height / canvas.value.height)
  const displayedWidth = canvas.value.width * scale
  const displayedHeight = canvas.value.height * scale
  
  // object-fit: contain 会使内容居中
  const offsetX = (rect.width - displayedWidth) / 2
  const offsetY = (rect.height - displayedHeight) / 2
  
  return {
    x: (event.clientX - rect.left - offsetX) / scale,
    y: (event.clientY - rect.top - offsetY) / scale
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
}

const handleMouseMove = (event) => {
  if (!drawing.value) return
  
  const coords = getCanvasCoordinates(event)
  
  ctx.value.lineWidth = lineWidth.value
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
    img.onload = () => {
      saveToHistory()
      
      const scale = Math.min(
        canvas.value.width / img.width,
        canvas.value.height / img.height
      )
      
      const drawWidth = img.width * scale
      const drawHeight = img.height * scale
      const offsetX = (canvas.value.width - drawWidth) / 2
      const offsetY = (canvas.value.height - drawHeight) / 2
      
      ctx.value.fillStyle = '#ffffff'
      ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height)
      ctx.value.drawImage(img, offsetX, offsetY, drawWidth, drawHeight)
      
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
  
  const wrapperRect = canvasWrapper.value.getBoundingClientRect()
    const availableWidth = Math.floor(wrapperRect.width)
    const availableHeight = Math.floor(wrapperRect.height)
    
    if (availableWidth > 0 && availableHeight > 0) {
      const imageData = ctx.value ? ctx.value.getImageData(0, 0, canvas.value.width, canvas.value.height) : null
      
      canvas.value.width = availableWidth
      canvas.value.height = availableHeight
    
    if (imageData) {
      clearCanvas()
      ctx.value.putImageData(imageData, 0, 0)
    } else {
      clearCanvas()
    }
    
    emit('update:width', availableWidth)
    emit('update:height', availableHeight)
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
  align-items: stretch;
  justify-content: stretch;
  background: rgba(255, 255, 255, 0.04);
  padding: 0;
  min-height: 400px;
}

canvas {
  background: var(--panel);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
  width: 100%;
  height: 100%;
  object-fit: contain;
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
</style>
