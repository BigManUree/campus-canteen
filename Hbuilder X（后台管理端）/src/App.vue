<template>
  <div class="app-shell">
    <div class="route-loading-bar"></div>
  <router-view />
  </div>
</template>

<script setup>
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.route-loading-bar {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 3000;
  width: 100%;
  height: 3px;
  transform: scaleX(0);
  transform-origin: left;
  background: linear-gradient(90deg, #24c99a, #6ea8fe, #ffb84d);
  opacity: 0;
  pointer-events: none;
}

:global(body.route-loading) .route-loading-bar {
  opacity: 1;
  transform: scaleX(0.72);
  transition: transform 0.28s ease, opacity 0.2s ease;
}
</style>
