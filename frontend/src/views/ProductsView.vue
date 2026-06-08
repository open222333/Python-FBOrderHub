<template>
  <div>
    <div class="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-2">
      <h4 class="fw-bold mb-0"><i class="bi bi-box-seam me-2"></i>產品庫存管理</h4>
      <button class="btn btn-primary" @click="openCreate">
        <i class="bi bi-plus-circle me-1"></i>新增產品
      </button>
    </div>

    <!-- 狀態篩選 -->
    <div class="card border-0 shadow-sm mb-4">
      <div class="card-body pb-0">
        <ul class="nav nav-tabs card-header-tabs">
          <li class="nav-item" v-for="tab in TABS" :key="tab.value">
            <button class="nav-link" :class="{ active: filterStatus === tab.value }"
              @click="filterStatus = tab.value">
              {{ tab.label }}
              <span class="badge ms-1"
                :class="tab.value === 'listed' ? 'bg-success' : tab.value === 'unlisted' ? 'bg-secondary' : 'bg-primary'">
                {{ tabCount(tab.value) }}
              </span>
            </button>
          </li>
        </ul>
      </div>
    </div>

    <!-- 產品列表 -->
    <div class="card border-0 shadow-sm">
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5 text-muted">
          <span class="spinner-border spinner-border-sm me-2"></span>載入中...
        </div>
        <div v-else-if="!filteredProducts.length" class="text-center py-5 text-muted">
          <i class="bi bi-inbox fs-2 d-block mb-2"></i>無產品資料
        </div>
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th style="width:60px">圖片</th>
                <th>產品名稱</th>
                <th class="text-end">價格</th>
                <th class="text-center">庫存</th>
                <th class="text-center">狀態</th>
                <th class="text-center">排程下架</th>
                <th class="text-center" style="width:160px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in filteredProducts" :key="p._id">
                <td>
                  <img v-if="p.images?.length" :src="p.images[0]" class="rounded"
                    style="width:44px;height:44px;object-fit:cover" />
                  <div v-else class="rounded bg-secondary-subtle d-flex align-items-center justify-content-center"
                    style="width:44px;height:44px">
                    <i class="bi bi-image text-secondary"></i>
                  </div>
                </td>
                <td>
                  <div class="fw-semibold">{{ p.name }}</div>
                  <div class="text-muted small text-truncate" style="max-width:220px">{{ p.description }}</div>
                </td>
                <td class="text-end fw-semibold">{{ formatPrice(p.price) }}</td>
                <td class="text-center">{{ p.stock }}</td>
                <td class="text-center">
                  <span :class="`badge ${p.status === 'listed' ? 'bg-success' : 'bg-secondary'}`">
                    {{ p.status === 'listed' ? '上架' : '下架' }}
                  </span>
                </td>
                <td class="text-center small text-muted">
                  {{ p.scheduled_unpublish_at ? formatDt(p.scheduled_unpublish_at) : '—' }}
                </td>
                <td class="text-center">
                  <div class="d-flex gap-1 justify-content-center">
                    <button class="btn btn-sm"
                      :class="p.status === 'listed' ? 'btn-outline-secondary' : 'btn-outline-success'"
                      :disabled="toggling === p._id"
                      @click="toggleStatus(p)">
                      <span v-if="toggling === p._id" class="spinner-border spinner-border-sm"></span>
                      <i v-else :class="p.status === 'listed' ? 'bi-eye-slash' : 'bi-eye'" class="bi"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary" @click="openEdit(p)">
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" @click="confirmDelete(p)">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 產品 Modal -->
    <ProductModal ref="productModalRef" modal-id="productModal" @saved="load" />

    <!-- 刪除確認 Modal -->
    <ConfirmModal ref="confirmRef" @confirm="doDelete" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { productApi } from '@/api/index'
import ProductModal from '@/components/ProductModal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'

const TABS = [
  { label: '全部', value: '' },
  { label: '上架', value: 'listed' },
  { label: '下架', value: 'unlisted' },
]

const products       = ref([])
const loading        = ref(false)
const filterStatus   = ref('')
const toggling       = ref(null)
const deletingId     = ref(null)
const productModalRef = ref(null)
const confirmRef     = ref(null)

const filteredProducts = computed(() =>
  filterStatus.value ? products.value.filter(p => p.status === filterStatus.value) : products.value
)

function tabCount(status) {
  if (!status) return products.value.length
  return products.value.filter(p => p.status === status).length
}

function formatPrice(v) {
  return `NT$ ${Number(v).toLocaleString()}`
}

function formatDt(iso) {
  return iso ? new Date(iso).toLocaleString('zh-TW', { dateStyle: 'short', timeStyle: 'short' }) : ''
}

async function load() {
  loading.value = true
  const res = await productApi.list()
  loading.value = false
  if (!res) return
  const data = await res.json()
  if (data.success) products.value = data.data
}

function openCreate() {
  productModalRef.value.open()
  new window.bootstrap.Modal(document.getElementById('productModal')).show()
}

function openEdit(p) {
  productModalRef.value.open(p)
  new window.bootstrap.Modal(document.getElementById('productModal')).show()
}

async function toggleStatus(p) {
  toggling.value = p._id
  const newStatus = p.status === 'listed' ? 'unlisted' : 'listed'
  const res = await productApi.setStatus(p._id, newStatus)
  toggling.value = null
  if (res && (await res.json()).success) {
    p.status = newStatus
  }
}

function confirmDelete(p) {
  deletingId.value = p._id
  confirmRef.value.open({ title: '刪除產品', message: `確定要刪除「${p.name}」嗎？此操作無法復原。` })
}

async function doDelete() {
  if (!deletingId.value) return
  const res = await productApi.remove(deletingId.value)
  if (res && (await res.json()).success) load()
  deletingId.value = null
}

onMounted(load)
</script>
