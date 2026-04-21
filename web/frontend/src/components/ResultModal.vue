<template>
  <Transition name="modal">
    <div v-if="show" class="modal-mask" @click="$emit('close')">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <div class="header-title">
            <span class="icon">✨</span>
            <h2>生成结果预览</h2>
          </div>
          <button class="close-button" @click="$emit('close')">&times;</button>
        </div>

        <div class="modal-body">
          <div class="results-grid">
            <div class="result-item" v-if="stage1Url">
              <h3>Stage 1 预览 (LCM)</h3>
              <div class="image-wrapper">
                <img :src="stage1Url" alt="Stage 1">
              </div>
            </div>

            <div class="result-item" v-if="cannyUrl">
              <h3>Canny 边缘检测</h3>
              <div class="image-wrapper">
                <img :src="cannyUrl" alt="Canny">
              </div>
            </div>

            <div class="result-item highlight" v-if="finalUrl">
              <h3>最终生成结果</h3>
              <div class="image-wrapper main">
                <img :src="finalUrl" alt="Final Result">
              </div>
              <div class="actions">
                <button class="download-btn" @click="downloadImage(finalUrl)">
                  <span>💾</span> 下载高清原图
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
defineProps({
  show: Boolean,
  stage1Url: String,
  cannyUrl: String,
  finalUrl: String
})

defineEmits(['close'])

const downloadImage = (url) => {
  const link = document.createElement('a')
  link.href = url
  link.download = `pic2pic_${Date.now()}.png`
  link.click()
}
</script>

<style scoped>
.modal-mask {
  position: fixed;
  z-index: 9998;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.3s ease;
}

.modal-container {
  width: 90%;
  max-width: 1100px;
  max-height: 90vh;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.3);
  animation: modalScale 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalScale {
  from { transform: scale(0.9) translateY(20px); opacity: 0; }
  to { transform: scale(1) translateY(0); opacity: 1; }
}

.modal-header {
  padding: 20px 32px;
  background: white;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.close-button {
  background: #f1f5f9;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 24px;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-button:hover {
  background: #ef4444;
  color: white;
  transform: rotate(90deg);
}

.modal-body {
  padding: 32px;
  overflow-y: auto;
  background: #f8fafc;
}

.results-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.result-item {
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #f1f5f9;
}

.result-item h3 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.highlight {
  grid-column: span 2;
}

.image-wrapper {
  width: 100%;
  background: #f1f5f9;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.image-wrapper.main {
  min-height: 400px;
}

.image-wrapper img {
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
  transition: transform 0.3s;
}

.image-wrapper img:hover {
  transform: scale(1.05);
}

.actions {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.download-btn {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  border: none;
  padding: 14px 32px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 10px 20px rgba(79, 70, 229, 0.3);
  transition: all 0.3s;
}

.download-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 30px rgba(79, 70, 229, 0.4);
}

/* Transitions */
.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
}
</style>
