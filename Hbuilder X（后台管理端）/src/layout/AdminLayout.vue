<template>
  <el-container class="admin-layout" :class="{ 'admin-layout--collapsed': isCollapsed, 'admin-layout--mobile': isMobile }">
    <transition name="mobile-mask">
      <div v-if="mobileMenuVisible" class="mobile-mask" @click="mobileMenuVisible = false"></div>
    </transition>

    <el-aside class="admin-layout__aside" :class="{ 'is-mobile-open': mobileMenuVisible }" :width="asideWidth">
      <div class="brand-panel" :class="{ 'brand-panel--collapsed': isCollapsed && !isMobile }">
        <div class="brand-mark">CC</div>
        <transition name="brand-fade">
          <div v-if="!isCollapsed || isMobile" class="brand-copy">
          <h1>校园食堂后台</h1>
            <p>Canteen Control Center</p>
          </div>
        </transition>
        </div>

      <div class="aside-toggle-wrap">
        <el-button
          v-if="!isMobile"
          class="aside-toggle"
          circle
          plain
          :icon="isCollapsed ? Expand : Fold"
          @click="isCollapsed = !isCollapsed"
        />
        <el-button
          v-else
          class="aside-toggle"
          circle
          plain
          :icon="Close"
          @click="mobileMenuVisible = false"
        />
      </div>

      <el-scrollbar>
        <div class="menu-group-list">
          <section v-for="group in filteredMenuGroups" :key="group.title" class="menu-group">
            <p v-if="(!isCollapsed || isMobile) && group.items.length" class="menu-group__title">{{ group.title }}</p>
        <el-menu
          router
          :default-active="route.path"
              :collapse="isCollapsed && !isMobile"
              :collapse-transition="false"
          class="admin-menu"
          background-color="transparent"
          text-color="#b5c0da"
          active-text-color="#ffffff"
              @select="handleMenuSelect"
        >
              <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
            <el-icon><component :is="icons[item.icon]" /></el-icon>
                <template #title>{{ item.title }}</template>
          </el-menu-item>
        </el-menu>
          </section>
        </div>
      </el-scrollbar>
    </el-aside>

    <el-container class="admin-layout__content">
      <el-header class="admin-layout__header">
        <div class="header-primary">
          <div class="header-topline">
            <el-button
              v-if="isMobile"
              class="header-icon-btn"
              circle
              plain
              :icon="Menu"
              @click="mobileMenuVisible = true"
            />
            <div class="header-title-row">
          <h2>{{ route.meta?.title || '管理后台' }}</h2>
              <span class="header-status">系统在线</span>
            </div>
          </div>
          <el-breadcrumb separator="/" class="admin-breadcrumb">
            <el-breadcrumb-item>管理后台</el-breadcrumb-item>
            <el-breadcrumb-item>{{ route.meta?.title || '当前页面' }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-actions">
          <div class="global-search">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索页面、功能、模块"
              clearable
              :prefix-icon="Search"
              @focus="searchOpen = true"
              @input="searchOpen = true"
              @keyup.enter="handleSearchEnter"
            />
            <transition name="search-panel-fade">
              <div v-if="searchOpen && searchKeyword.trim()" class="search-panel">
                <div v-if="searchResults.length" class="search-results">
                  <button
                    v-for="item in searchResults"
                    :key="item.path"
                    type="button"
                    class="search-item"
                    @click="goToSearchResult(item.path)"
                  >
                    <strong>{{ item.title }}</strong>
                    <span>{{ item.groupTitle }}</span>
                  </button>
                </div>
                <div v-else class="search-empty">未找到相关页面</div>
              </div>
            </transition>
          </div>
          <el-badge :value="notificationCount" :hidden="!notificationCount">
            <el-button class="header-icon-btn" circle plain :icon="Bell" @click="router.push('/notifications')" />
          </el-badge>
          <el-button class="header-icon-btn" circle plain :icon="RefreshRight" @click="router.go(0)" />
          <el-dropdown>
            <div class="user-chip">
              <div class="avatar">{{ authStore.userName.slice(0, 1) }}</div>
              <div class="user-copy">
                <strong>{{ authStore.userName }}</strong>
                <p>{{ authStore.roleLabel }}</p>
              </div>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/dashboard')">返回看板</el-dropdown-item>
                <el-dropdown-item @click="router.push('/notifications')">查看通知</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <div class="admin-tabs-wrap">
        <div class="admin-tabs">
          <button
            v-for="tab in openTabs"
            :key="tab.path"
            type="button"
            class="admin-tab"
            :class="{ 'is-active': tab.path === route.path }"
            @click="router.push(tab.path)"
          >
            <span>{{ tab.title }}</span>
            <i v-if="tab.path !== '/dashboard'" @click.stop="closeTab(tab.path)">×</i>
          </button>
        </div>
      </div>

      <el-main class="admin-layout__main">
        <router-view v-slot="{ Component }">
          <transition name="page-fade-slide" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as icons from '@element-plus/icons-vue'
import { Bell, Close, Expand, Fold, Menu, RefreshRight, Search } from '@element-plus/icons-vue'
import { menuGroups, menuItems } from '@/router/menu'
import { useAuthStore } from '@/stores/auth'
import { notificationApi } from '@/api/modules/notifications'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationCount = ref(0)
const isCollapsed = ref(false)
const isMobile = ref(false)
const mobileMenuVisible = ref(false)
const searchKeyword = ref('')
const searchOpen = ref(false)
const openTabs = ref([{ path: '/dashboard', title: '数据看板' }])

const asideWidth = computed(() => {
  if (isMobile.value) return '280px'
  return isCollapsed.value ? '88px' : '256px'
})

const filteredMenuGroups = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return menuGroups

  return menuGroups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => item.title.toLowerCase().includes(keyword))
    }))
    .filter((group) => group.items.length)
})

const searchResults = computed(() =>
  filteredMenuGroups.value.flatMap((group) =>
    group.items.map((item) => ({
      ...item,
      groupTitle: group.title
    }))
  ).slice(0, 8)
)

const syncResponsiveState = () => {
  const mobile = window.innerWidth < 1100
  isMobile.value = mobile
  if (mobile) {
    isCollapsed.value = false
  } else {
    mobileMenuVisible.value = false
  }
}

const loadUnreadCount = async () => {
  try {
    const result = await notificationApi.getUnreadCount()
    notificationCount.value = result?.count || result?.unread_count || 0
  } catch (_error) {
    notificationCount.value = 0
  }
}

const handleLogout = () => {
  authStore.clearAuth()
  router.replace('/login')
}

const ensureTab = (path) => {
  const current = menuItems.find((item) => item.path === path)
  if (!current) return
  const exists = openTabs.value.some((tab) => tab.path === path)
  if (!exists) {
    openTabs.value.push({ path: current.path, title: current.title })
  }
}

const closeTab = (path) => {
  if (path === '/dashboard') return
  const index = openTabs.value.findIndex((tab) => tab.path === path)
  if (index === -1) return

  const isCurrent = route.path === path
  openTabs.value.splice(index, 1)

  if (isCurrent) {
    const fallback = openTabs.value[index - 1] || openTabs.value[index] || openTabs.value[0]
    if (fallback) {
      router.push(fallback.path)
    }
  }
}

const handleMenuSelect = () => {
  if (isMobile.value) {
    mobileMenuVisible.value = false
  }
}

const handleSearchEnter = () => {
  const first = searchResults.value[0]
  if (first) {
    goToSearchResult(first.path)
  }
}

const goToSearchResult = (path) => {
  searchOpen.value = false
  searchKeyword.value = ''
  router.push(path)
  if (isMobile.value) {
    mobileMenuVisible.value = false
  }
}

const handleGlobalClick = (event) => {
  if (!event.target.closest('.global-search')) {
    searchOpen.value = false
  }
}

watch(
  () => route.path,
  (path) => {
    ensureTab(path)
    if (isMobile.value) {
      mobileMenuVisible.value = false
    }
  },
  { immediate: true }
)

onMounted(async () => {
  if (!authStore.user && authStore.token) {
    await authStore.fetchProfile()
  }
  syncResponsiveState()
  window.addEventListener('resize', syncResponsiveState)
  window.addEventListener('click', handleGlobalClick)
  loadUnreadCount()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncResponsiveState)
  window.removeEventListener('click', handleGlobalClick)
})
</script>

<style scoped lang="scss">
.admin-layout {
  position: relative;
  min-height: 100vh;
}

.mobile-mask {
  position: fixed;
  inset: 0;
  z-index: 39;
  background: rgba(4, 9, 20, 0.55);
  backdrop-filter: blur(3px);
}

.admin-layout__aside {
  position: relative;
  z-index: 40;
  overflow: hidden;
  transition: width 0.24s ease, transform 0.24s ease;
  border-right: 1px solid rgba(151, 164, 199, 0.14);
  background:
    linear-gradient(180deg, rgba(12, 21, 45, 0.98), rgba(9, 15, 31, 0.98)),
    linear-gradient(180deg, rgba(36, 201, 154, 0.06), transparent 28%);
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.03);
}

.admin-layout__content {
  min-width: 0;
}

.brand-panel {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 28px 22px 12px;
}

.brand-panel--collapsed {
  justify-content: center;
  padding-inline: 0;
}

.brand-copy {
  min-width: 0;
}

.brand-copy h1 {
    margin: 0;
    font-size: 20px;
  }

.brand-copy p {
    margin: 6px 0 0;
    color: #7f8aad;
    font-size: 12px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

.brand-mark {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: linear-gradient(135deg, #24c99a, #6ea8fe);
  color: #04111d;
  font-weight: 800;
  box-shadow: 0 18px 30px rgba(36, 201, 154, 0.25);
}

.aside-toggle-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 0 18px 12px;
}

.admin-layout--collapsed .aside-toggle-wrap {
  justify-content: center;
  padding: 0 0 12px;
}

.aside-toggle,
.header-icon-btn {
  border-color: rgba(151, 164, 199, 0.16);
  background: rgba(255, 255, 255, 0.04);
}

.menu-group-list {
  padding-bottom: 24px;
}

.menu-group {
  margin-bottom: 10px;
}

.menu-group__title {
  margin: 0;
  padding: 12px 20px 10px;
  color: #7483a8;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.admin-menu {
  border-right: none;
  padding: 0 12px;
}

.admin-menu :deep(.el-menu-item) {
  margin-bottom: 8px;
  border-radius: 14px;
}

.admin-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.05);
}

.admin-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(36, 201, 154, 0.22), rgba(110, 168, 254, 0.18));
}

.admin-layout--collapsed .admin-menu {
  padding-inline: 10px;
}

.admin-layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 28px;
  border-bottom: 1px solid rgba(151, 164, 199, 0.12);
  background: rgba(7, 12, 25, 0.42);
  backdrop-filter: blur(20px);
}

.header-primary {
  min-width: 0;
}

.header-topline {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.header-title-row h2 {
    margin: 0;
    font-size: 28px;
  }

.header-status {
  padding: 4px 10px;
  border: 1px solid rgba(99, 230, 190, 0.2);
  border-radius: 999px;
  background: rgba(36, 201, 154, 0.12);
  color: #7ff0c8;
  font-size: 12px;
  }

.admin-breadcrumb :deep(.el-breadcrumb__inner),
.admin-breadcrumb :deep(.el-breadcrumb__separator) {
  color: #8fa0c5;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.global-search {
  position: relative;
  width: 320px;
}

.search-panel {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  z-index: 20;
  overflow: hidden;
  border: 1px solid rgba(151, 164, 199, 0.14);
  border-radius: 18px;
  background: rgba(16, 25, 49, 0.96);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.34);
  backdrop-filter: blur(20px);
}

.search-results {
  display: grid;
  gap: 6px;
  padding: 10px;
}

.search-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  border: none;
  border-radius: 14px;
  background: transparent;
  color: #f3f7ff;
  text-align: left;
  cursor: pointer;
}

.search-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.search-item span,
.search-empty {
  color: #8fa0c5;
  font-size: 12px;
}

.search-empty {
  padding: 16px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 14px;
  border: 1px solid rgba(151, 164, 199, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
}

.user-copy p {
    margin: 2px 0 0;
    color: #7f8aad;
    font-size: 12px;
}

.avatar {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ffb84d, #ff6b81);
  color: #111827;
  font-weight: 700;
}

.admin-tabs-wrap {
  overflow-x: auto;
  border-bottom: 1px solid rgba(151, 164, 199, 0.12);
  background: rgba(10, 17, 34, 0.4);
}

.admin-tabs {
  display: flex;
  gap: 10px;
  min-width: max-content;
  padding: 12px 24px;
}

.admin-tab {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid rgba(151, 164, 199, 0.12);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  color: #cdd5ea;
  cursor: pointer;
}

.admin-tab.is-active {
  border-color: rgba(36, 201, 154, 0.28);
  background: linear-gradient(90deg, rgba(36, 201, 154, 0.18), rgba(110, 168, 254, 0.15));
  color: #ffffff;
}

.admin-tab i {
  font-style: normal;
  color: #95a5c8;
}

.admin-layout__main {
  padding: 0;
}

.brand-fade-enter-active,
.brand-fade-leave-active,
.search-panel-fade-enter-active,
.search-panel-fade-leave-active,
.mobile-mask-enter-active,
.mobile-mask-leave-active {
  transition: all 0.2s ease;
}

.brand-fade-enter-from,
.brand-fade-leave-to,
.search-panel-fade-enter-from,
.search-panel-fade-leave-to,
.mobile-mask-enter-from,
.mobile-mask-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.page-fade-slide-enter-active,
.page-fade-slide-leave-active {
  transition: all 0.24s ease;
}

.page-fade-slide-enter-from,
.page-fade-slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

@media (max-width: 1400px) {
  .global-search {
    width: 260px;
  }
}

@media (max-width: 1100px) {
  .admin-layout__aside {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 280px !important;
    transform: translateX(-100%);
  }

  .admin-layout__aside.is-mobile-open {
    transform: translateX(0);
  }

  .admin-layout__header {
    flex-direction: column;
    align-items: stretch;
    padding: 18px 18px 16px;
  }

  .header-actions {
    flex-wrap: wrap;
  }

  .global-search {
    width: 100%;
  }

  .user-copy {
    display: none;
  }

  .admin-tabs {
    padding: 12px 18px;
  }
}

@media (max-width: 768px) {
  .header-title-row h2 {
    font-size: 22px;
  }

  .admin-breadcrumb {
    display: none;
  }

  .header-actions {
    gap: 10px;
  }
}
</style>
