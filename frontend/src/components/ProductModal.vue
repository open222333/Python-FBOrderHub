<template>
  <div class="modal fade" :id="modalId" tabindex="-1" ref="modalEl">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ isEdit ? '編輯產品' : '新增產品' }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="row g-3">
            <div class="col-12">
              <label class="form-label fw-semibold">產品名稱 <span class="text-danger">*</span></label>
              <input v-model="form.name" type="text" class="form-control" placeholder="請輸入產品名稱" />
            </div>

            <div class="col-12">
              <label class="form-label fw-semibold">產品描述</label>
              <textarea v-model="form.description" class="form-control" rows="3" placeholder="產品說明"></textarea>
            </div>

            <div class="col-md-6">
              <label class="form-label fw-semibold">價格（元）</label>
              <input v-model.number="form.price" type="number" min="0" step="1" class="form-control" />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-semibold">庫存數量</label>
              <input v-model.number="form.stock" type="number" min="0" step="1" class="form-control" />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-semibold">上架狀態</label>
              <select v-model="form.status" class="form-select">
                <option value="unlisted">下架</option>
                <option value="listed">上架</option>
              </select>
            </div>

            <div class="col-md-6">
              <label class="form-label fw-semibold">排程下架時間</label>
              <input v-model="form.scheduled_unpublish_at" type="datetime-local" class="form-control" />
              <div class="form-text">留空表示不排程自動下架</div>
            </div>

            <div class="col-12">
              <label class="form-label fw-semibold">產品圖片 URL</label>
              <div v-for="(img, i) in form.images" :key="i" class="input-group mb-2">
                <input v-model="form.images[i]" type="url" class="form-control" placeholder="https://..." />
                <button class="btn btn-outline-danger" @click="removeImage(i)">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
              <button class="btn btn-outline-secondary btn-sm" @click="addImage">
                <i class="bi bi-plus-circle me-1"></i>新增圖片
              </button>
            </div>
          </div>

          <div v-if="error" class="alert alert-danger mt-3 mb-0">{{ error }}</div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
          <button type="button" class="btn btn-primary" :disabled="saving" @click="save">
            <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
            {{ isEdit ? '儲存' : '新增' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { productApi } from '@/api/index'

const props  = defineProps({ modalId: { type: String, default: 'productModal' } })
const emit   = defineEmits(['saved'])

const form  = ref(defaultForm())
const error = ref('')
const saving = ref(false)
const editId = ref(null)

const isEdit = computed(() => !!editId.value)

function defaultForm() {
  return { name: '', description: '', price: 0, stock: 0, status: 'unlisted', scheduled_unpublish_at: '', images: [] }
}

function open(product = null) {
  error.value = ''
  if (product) {
    editId.value = product._id
    form.value = {
      name:                   product.name || '',
      description:            product.description || '',
      price:                  product.price ?? 0,
      stock:                  product.stock ?? 0,
      status:                 product.status || 'unlisted',
      scheduled_unpublish_at: product.scheduled_unpublish_at
        ? product.scheduled_unpublish_at.slice(0, 16)
        : '',
      images: [...(product.images || [])],
    }
  } else {
    editId.value = null
    form.value = defaultForm()
  }
}

function addImage()       { form.value.images.push('') }
function removeImage(i)   { form.value.images.splice(i, 1) }

async function save() {
  error.value = ''
  if (!form.value.name.trim()) { error.value = '請輸入產品名稱'; return }

  saving.value = true
  const payload = {
    ...form.value,
    images: form.value.images.filter(u => u.trim()),
    scheduled_unpublish_at: form.value.scheduled_unpublish_at || null,
  }

  const res = isEdit.value
    ? await productApi.update(editId.value, payload)
    : await productApi.create(payload)

  saving.value = false
  if (!res) return
  const data = await res.json()
  if (!data.success) { error.value = data.message || '操作失敗'; return }

  emit('saved')
  const modal = window.bootstrap?.Modal.getInstance(document.getElementById(props.modalId))
  modal?.hide()
}

defineExpose({ open })
</script>
