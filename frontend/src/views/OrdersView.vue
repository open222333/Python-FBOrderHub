<template>
  <div>
    <h4 class="fw-bold mb-4"><i class="bi bi-receipt me-2"></i>訂單管理</h4>

    <!-- 狀態篩選 -->
    <div class="card border-0 shadow-sm mb-4">
      <div class="card-body pb-0">
        <ul class="nav nav-tabs card-header-tabs">
          <li class="nav-item" v-for="tab in TABS" :key="tab.value">
            <button class="nav-link" :class="{ active: filterStatus === tab.value }"
              @click="filterStatus = tab.value">
              {{ tab.label }}
              <span class="badge ms-1" :class="tab.badge">{{ tabCount(tab.value) }}</span>
            </button>
          </li>
        </ul>
      </div>
    </div>

    <!-- 訂單列表 -->
    <div class="card border-0 shadow-sm">
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5 text-muted">
          <span class="spinner-border spinner-border-sm me-2"></span>載入中...
        </div>
        <div v-else-if="!filteredOrders.length" class="text-center py-5 text-muted">
          <i class="bi bi-inbox fs-2 d-block mb-2"></i>無訂單資料
        </div>
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>顧客</th>
                <th>電話</th>
                <th>商品</th>
                <th class="text-end">總金額</th>
                <th class="text-center">狀態</th>
                <th class="text-center">下單時間</th>
                <th class="text-center" style="width:160px">更新狀態</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="o in filteredOrders" :key="o._id">
                <td class="fw-semibold">{{ o.customer_name }}</td>
                <td class="text-muted small">{{ o.customer_phone }}</td>
                <td>
                  <ul class="mb-0 ps-3 small">
                    <li v-for="(item, i) in o.items" :key="i">
                      {{ item.product_name }} × {{ item.quantity }}
                    </li>
                  </ul>
                  <div v-if="o.note" class="text-muted small mt-1">備註：{{ o.note }}</div>
                </td>
                <td class="text-end fw-semibold">NT$ {{ Number(o.total).toLocaleString() }}</td>
                <td class="text-center">
                  <span class="badge" :class="statusBadge(o.status)">
                    {{ STATUS_LABELS[o.status] || o.status }}
                  </span>
                </td>
                <td class="text-center small text-muted">{{ formatDt(o.created_at) }}</td>
                <td class="text-center">
                  <select class="form-select form-select-sm"
                    :value="o.status"
                    :disabled="updating === o._id"
                    @change="updateStatus(o, $event.target.value)">
                    <option v-for="s in ORDER_STATUSES" :key="s" :value="s">
                      {{ STATUS_LABELS[s] }}
                    </option>
                  </select>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { orderApi } from '@/api/index'

const ORDER_STATUSES = ['pending', 'processing', 'completed', 'cancelled']
const STATUS_LABELS  = { pending: '待處理', processing: '處理中', completed: '已完成', cancelled: '已取消' }

const TABS = [
  { label: '全部',   value: '',           badge: 'bg-primary' },
  { label: '待處理', value: 'pending',    badge: 'bg-warning text-dark' },
  { label: '處理中', value: 'processing', badge: 'bg-info text-dark' },
  { label: '已完成', value: 'completed',  badge: 'bg-success' },
  { label: '已取消', value: 'cancelled',  badge: 'bg-secondary' },
]

const orders       = ref([])
const loading      = ref(false)
const filterStatus = ref('')
const updating     = ref(null)

const filteredOrders = computed(() =>
  filterStatus.value ? orders.value.filter(o => o.status === filterStatus.value) : orders.value
)

function tabCount(status) {
  return status ? orders.value.filter(o => o.status === status).length : orders.value.length
}

function statusBadge(s) {
  return { pending: 'bg-warning text-dark', processing: 'bg-info text-dark', completed: 'bg-success', cancelled: 'bg-secondary' }[s] || 'bg-secondary'
}

function formatDt(iso) {
  return iso ? new Date(iso).toLocaleString('zh-TW', { dateStyle: 'short', timeStyle: 'short' }) : ''
}

async function load() {
  loading.value = true
  const res = await orderApi.list()
  loading.value = false
  if (res) {
    const data = await res.json()
    if (data.success) orders.value = data.data
  }
}

async function updateStatus(o, status) {
  if (status === o.status) return
  updating.value = o._id
  const res = await orderApi.updateStatus(o._id, status)
  updating.value = null
  if (res && (await res.json()).success) o.status = status
}

onMounted(load)
</script>
