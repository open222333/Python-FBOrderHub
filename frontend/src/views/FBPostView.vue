<template>
  <div>
    <h4 class="fw-bold mb-4"><i class="bi bi-facebook me-2"></i>FB 社團發文</h4>

    <div class="row g-4">
      <!-- 左欄：模板管理 -->
      <div class="col-lg-4">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header d-flex align-items-center justify-content-between">
            <span class="fw-semibold">發文模板</span>
            <button class="btn btn-sm btn-outline-primary" @click="openTemplateEditor()">
              <i class="bi bi-plus-circle me-1"></i>新增
            </button>
          </div>
          <div class="card-body p-0">
            <div v-if="loadingTemplates" class="text-center py-4 text-muted small">載入中...</div>
            <div v-else-if="!templates.length" class="text-center py-4 text-muted small">尚無模板</div>
            <ul v-else class="list-group list-group-flush">
              <li v-for="t in templates" :key="t._id"
                class="list-group-item list-group-item-action d-flex align-items-center gap-2 py-2 px-3">
                <div class="flex-grow-1 overflow-hidden">
                  <div class="fw-semibold small text-truncate">{{ t.name }}</div>
                  <div class="text-muted" style="font-size:.75rem;line-height:1.3;
                    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">
                    {{ t.content }}
                  </div>
                </div>
                <div class="d-flex gap-1 flex-shrink-0">
                  <button class="btn btn-xs btn-outline-primary" @click="applyTemplate(t)" title="套用至編輯區">
                    <i class="bi bi-clipboard-check"></i>
                  </button>
                  <button class="btn btn-xs btn-outline-secondary" @click="openTemplateEditor(t)" title="編輯">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn btn-xs btn-outline-danger" @click="confirmDeleteTemplate(t)" title="刪除">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 右欄：發文編輯器 -->
      <div class="col-lg-8">
        <div class="card border-0 shadow-sm">
          <div class="card-header fw-semibold">發文編輯器</div>
          <div class="card-body">
            <!-- 套用產品資訊 -->
            <div class="row g-2 mb-3">
              <div class="col">
                <select v-model="selectedProductId" class="form-select">
                  <option value="">選擇產品（套用到文章）</option>
                  <option v-for="p in products" :key="p._id" :value="p._id">
                    {{ p.name }} — NT${{ Number(p.price).toLocaleString() }}
                  </option>
                </select>
              </div>
              <div class="col-auto">
                <button class="btn btn-outline-primary" :disabled="!selectedProductId" @click="applyProduct">
                  <i class="bi bi-magic me-1"></i>套用產品
                </button>
              </div>
            </div>

            <div class="form-text mb-3 text-muted">
              模板占位符：<code>{name}</code> <code>{price}</code> <code>{description}</code> <code>{stock}</code>
            </div>

            <!-- 文章內容 -->
            <textarea v-model="postMessage" class="form-control font-monospace mb-3"
              rows="10" placeholder="在此輸入或套用模板內容..."></textarea>

            <div v-if="postResult" class="alert mb-3"
              :class="postResult.success ? 'alert-success' : 'alert-danger'">
              <i :class="postResult.success ? 'bi-check-circle-fill' : 'bi-x-circle-fill'" class="bi me-2"></i>
              {{ postResult.success ? `發文成功！Post ID: ${postResult.post_id}` : postResult.error }}
            </div>

            <div class="d-flex justify-content-end gap-2">
              <button class="btn btn-outline-secondary" @click="postMessage = ''">清除</button>
              <button class="btn btn-primary" :disabled="!postMessage.trim() || posting" @click="doPost">
                <span v-if="posting" class="spinner-border spinner-border-sm me-1"></span>
                <i v-else class="bi bi-send-fill me-1"></i>
                發文至社團
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 模板編輯 Modal -->
    <div class="modal fade" id="templateEditorModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ editingTemplate?._id ? '編輯模板' : '新增模板' }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <label class="form-label fw-semibold">模板名稱</label>
            <input v-model="tmplForm.name" class="form-control mb-3" placeholder="例：新品上架公告" />
            <label class="form-label fw-semibold">模板內容</label>
            <textarea v-model="tmplForm.content" class="form-control font-monospace" rows="8"
              placeholder="可使用 {name} {price} {description} {stock}"></textarea>
            <div v-if="tmplError" class="alert alert-danger mt-2 mb-0">{{ tmplError }}</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-primary" :disabled="tmplSaving" @click="saveTemplate">
              <span v-if="tmplSaving" class="spinner-border spinner-border-sm me-1"></span>
              儲存
            </button>
          </div>
        </div>
      </div>
    </div>

    <ConfirmModal ref="confirmRef" @confirm="doDeleteTemplate" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fbApi, productApi } from '@/api/index'
import ConfirmModal from '@/components/ConfirmModal.vue'

const templates         = ref([])
const products          = ref([])
const loadingTemplates  = ref(false)
const selectedProductId = ref('')
const postMessage       = ref('')
const posting           = ref(false)
const postResult        = ref(null)

const editingTemplate   = ref(null)
const tmplForm          = ref({ name: '', content: '' })
const tmplError         = ref('')
const tmplSaving        = ref(false)
const deletingTmplId    = ref(null)
const confirmRef        = ref(null)

async function loadTemplates() {
  loadingTemplates.value = true
  const res = await fbApi.listTemplates()
  loadingTemplates.value = false
  if (res) {
    const data = await res.json()
    if (data.success) templates.value = data.data
  }
}

async function loadProducts() {
  const res = await productApi.list()
  if (res) {
    const data = await res.json()
    if (data.success) products.value = data.data
  }
}

function applyTemplate(t) {
  postMessage.value = t.content
}

function applyProduct() {
  if (!selectedProductId.value) return
  const p = products.value.find(x => x._id === selectedProductId.value)
  if (!p) return
  postMessage.value = postMessage.value
    .replace(/\{name\}/g, p.name)
    .replace(/\{price\}/g, `NT$ ${Number(p.price).toLocaleString()}`)
    .replace(/\{description\}/g, p.description || '')
    .replace(/\{stock\}/g, p.stock ?? '')
}

async function doPost() {
  posting.value  = true
  postResult.value = null
  const res = await fbApi.post(postMessage.value)
  posting.value = false
  if (res) postResult.value = await res.json()
}

function openTemplateEditor(t = null) {
  editingTemplate.value = t
  tmplForm.value = { name: t?.name || '', content: t?.content || '' }
  tmplError.value = ''
  new window.bootstrap.Modal(document.getElementById('templateEditorModal')).show()
}

async function saveTemplate() {
  if (!tmplForm.value.name.trim() || !tmplForm.value.content.trim()) {
    tmplError.value = '名稱與內容不得為空'; return
  }
  tmplSaving.value = true
  const res = editingTemplate.value?._id
    ? await fbApi.updateTemplate(editingTemplate.value._id, tmplForm.value)
    : await fbApi.createTemplate(tmplForm.value)
  tmplSaving.value = false
  if (!res) return
  const data = await res.json()
  if (!data.success) { tmplError.value = data.message || '操作失敗'; return }
  window.bootstrap.Modal.getInstance(document.getElementById('templateEditorModal')).hide()
  loadTemplates()
}

function confirmDeleteTemplate(t) {
  deletingTmplId.value = t._id
  confirmRef.value.open({ title: '刪除模板', message: `確定要刪除模板「${t.name}」嗎？` })
}

async function doDeleteTemplate() {
  if (!deletingTmplId.value) return
  const res = await fbApi.deleteTemplate(deletingTmplId.value)
  if (res && (await res.json()).success) loadTemplates()
  deletingTmplId.value = null
}

onMounted(() => { loadTemplates(); loadProducts() })
</script>

<style scoped>
.btn-xs {
  padding: .15rem .4rem;
  font-size: .75rem;
}
</style>
