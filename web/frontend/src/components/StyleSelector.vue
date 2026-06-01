<template>
  <div class="style-selector">
    <div class="style-header">
      <h3>🎨 风格选择</h3>
      <button @click="resetStyles" class="reset-btn" title="重置风格">↺</button>
    </div>

    <div class="style-grid">
      <div 
        v-for="style in styles" 
        :key="style.id"
        :class="['style-card', { active: selectedStyles.includes(style.id) }]"
        @click="toggleStyle(style.id)"
      >
        <div class="style-icon">{{ style.icon }}</div>
        <div class="style-info">
          <div class="style-name">{{ style.name }}</div>
          <div class="style-description">{{ style.description }}</div>
        </div>
        <div v-if="selectedStyles.includes(style.id)" class="style-check">✓</div>
      </div>
    </div>

    <div v-if="selectedStyles.length > 0" class="selected-styles-summary">
      <div class="summary-header">
        <span>已选择 {{ selectedStyles.length }} 个风格</span>
        <button @click="clearAllStyles" class="clear-btn">清除全部</button>
      </div>
      <div class="selected-tags">
        <span 
          v-for="styleId in selectedStyles" 
          :key="styleId"
          class="style-tag"
        >
          {{ getStyleById(styleId)?.name }}
          <button @click.stop="toggleStyle(styleId)" class="tag-remove">×</button>
        </span>
      </div>
    </div>

    <div class="lora-section">
      <h3>🔮 LoRA 模型</h3>
      <div class="lora-list">
        <div 
          v-for="lora in loras" 
          :key="lora.id"
          :class="['lora-item', { active: activeLora === lora.id }]"
          @click="selectLora(lora.id)"
        >
          <div class="lora-info">
            <div class="lora-name">{{ lora.name }}</div>
            <div class="lora-description">{{ lora.description }}</div>
          </div>
          <div v-if="activeLora === lora.id" class="lora-check">✓</div>
        </div>
      </div>
      
      <div v-if="activeLora" class="lora-controls">
        <label>LoRA 权重: {{ loraWeight.toFixed(2) }}</label>
        <input 
          type="range" 
          v-model.number="loraWeight" 
          min="0" 
          max="1" 
          step="0.05"
          class="lora-weight-slider"
        >
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const emit = defineEmits(['update:styles', 'update:lora'])

const selectedStyles = ref([])
const activeLora = ref(null)
const loraWeight = ref(0.7)

const styles = ref([
  {
    id: 'anime',
    name: '动漫风格',
    description: '日式动漫插画风格',
    icon: '🎌',
    prompt: 'anime style, manga, illustration'
  },
  {
    id: 'realistic',
    name: '写实风格',
    description: '照片级真实感',
    icon: '📷',
    prompt: 'photorealistic, realistic, highly detailed'
  },
  {
    id: 'oil-painting',
    name: '油画风格',
    description: '经典油画质感',
    icon: '🖼️',
    prompt: 'oil painting, classical art, brushstrokes'
  },
  {
    id: 'watercolor',
    name: '水彩风格',
    description: '柔和水彩效果',
    icon: '💧',
    prompt: 'watercolor painting, soft colors, artistic'
  },
  {
    id: 'cyberpunk',
    name: '赛博朋克',
    description: '未来科技风格',
    icon: '🤖',
    prompt: 'cyberpunk, futuristic, neon lights, sci-fi'
  },
  {
    id: 'fantasy',
    name: '奇幻风格',
    description: '魔法与幻想',
    icon: '🧙',
    prompt: 'fantasy art, magical, ethereal, mystical'
  },
  {
    id: 'minimalist',
    name: '极简主义',
    description: '简洁现代设计',
    icon: '◻️',
    prompt: 'minimalist, clean, simple, modern'
  },
  {
    id: 'vintage',
    name: '复古风格',
    description: '怀旧复古质感',
    icon: '📻',
    prompt: 'vintage, retro, nostalgic, old film'
  }
])

const loras = ref([
  {
    id: 'portrait-enhance',
    name: '人像增强',
    description: '提升人物面部细节'
  },
  {
    id: 'detail-enhance',
    name: '细节增强',
    description: '增加整体细节丰富度'
  },
  {
    id: 'anime-lineart',
    name: '动漫线稿',
    description: '强化线条和轮廓'
  },
  {
    id: 'color-enhance',
    name: '色彩增强',
    description: '提升色彩饱和度和对比度'
  }
])

const getStyleById = (id) => {
  return styles.value.find(style => style.id === id)
}

const toggleStyle = (styleId) => {
  const index = selectedStyles.value.indexOf(styleId)
  if (index > -1) {
    selectedStyles.value.splice(index, 1)
  } else {
    selectedStyles.value.push(styleId)
  }
  emitUpdate()
}

const resetStyles = () => {
  selectedStyles.value = []
  emitUpdate()
}

const clearAllStyles = () => {
  selectedStyles.value = []
  emitUpdate()
}

const selectLora = (loraId) => {
  if (activeLora.value === loraId) {
    activeLora.value = null
  } else {
    activeLora.value = loraId
  }
  emitUpdate()
}

const emitUpdate = () => {
  const stylePrompts = selectedStyles.value
    .map(id => getStyleById(id)?.prompt)
    .filter(Boolean)
    .join(', ')

  const loraConfig = activeLora.value ? {
    id: activeLora.value,
    weight: loraWeight.value
  } : null

  emit('update:styles', stylePrompts)
  emit('update:lora', loraConfig)
}

watch(loraWeight, () => {
  emitUpdate()
})
</script>

<style scoped>
.style-selector {
  background: var(--panel);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.style-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.style-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--text);
}

.reset-btn {
  padding: 4px 8px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--line);
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.style-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 2px solid var(--line);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.style-card:hover {
  border-color: #b6ccff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.style-card.active {
  border-color: var(--primary);
  background: rgba(79, 70, 229, 0.15);
}

.style-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.style-info {
  flex: 1;
  min-width: 0;
}

.style-name {
  font-weight: 500;
  color: var(--text);
  margin-bottom: 4px;
}

.style-description {
  font-size: 12px;
  color: var(--sub);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.style-check {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  background: var(--primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.selected-styles-summary {
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  margin-bottom: 16px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--sub);
}

.clear-btn {
  padding: 4px 8px;
  font-size: 11px;
  background: rgba(239, 68, 68, 0.1);
  color: #991b1b;
  border: 1px solid #fecaca;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.style-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--primary);
  color: white;
  border-radius: 4px;
  font-size: 12px;
}

.tag-remove {
  background: none;
  border: none;
  color: white;
  padding: 0;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.lora-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--line);
}

.lora-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: var(--text);
}

.lora-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.lora-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 2px solid var(--line);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.lora-item:hover {
  border-color: #b6ccff;
}

.lora-item.active {
  border-color: var(--primary);
  background: rgba(79, 70, 229, 0.15);
}

.lora-info {
  flex: 1;
}

.lora-name {
  font-weight: 500;
  color: var(--text);
  margin-bottom: 4px;
}

.lora-description {
  font-size: 12px;
  color: var(--sub);
}

.lora-check {
  width: 20px;
  height: 20px;
  background: var(--primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.lora-controls {
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
}

.lora-controls label {
  margin-bottom: 8px;
}

.lora-weight-slider {
  width: 100%;
}
</style>
