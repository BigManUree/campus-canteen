<template>
  <div class="page-shell">
    <el-card class="panel-card placeholder-view" shadow="never">
      <template #header>
        <div class="placeholder-header">
          <div>
            <p class="placeholder-header__eyebrow">Module Preview</p>
            <h3>{{ title }}</h3>
            <p>{{ description }}</p>
          </div>
          <el-tag type="info" effect="dark">框架已就绪</el-tag>
        </div>
      </template>

      <div class="placeholder-body">
        <div class="placeholder-hero">
          <div class="placeholder-hero__icon">◌</div>
          <div>
            <h4>{{ title }} 正在接入真实业务能力</h4>
            <p>当前已完成路由、布局、权限壳与视觉规范，下一步可继续补充接口联调、表格筛选与弹窗交互。</p>
          </div>
        </div>

        <div class="placeholder-grid">
          <div class="placeholder-block">
            <span>01</span>
            <strong>页面结构</strong>
            <p>基础容器、标题区与内容布局已预留。</p>
          </div>
          <div class="placeholder-block">
            <span>02</span>
            <strong>交互预埋</strong>
            <p>适合继续接筛选栏、数据表格和详情抽屉。</p>
          </div>
          <div class="placeholder-block">
            <span>03</span>
            <strong>视觉统一</strong>
            <p>已与管理后台整体暗色风格保持一致。</p>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: '该模块骨架已创建。'
  }
})
</script>

<style scoped lang="scss">
.placeholder-view {
  min-height: calc(100vh - 154px);
}

.placeholder-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;

  h3 {
    margin: 6px 0 0;
    font-size: 24px;
  }

  p:last-child {
    margin: 10px 0 0;
    color: #8d98b5;
  }
}

.placeholder-header__eyebrow {
    margin: 0;
  color: #63e6be;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
}

.placeholder-body {
  display: grid;
  gap: 24px;
}

.placeholder-hero {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 24px;
  border: 1px solid rgba(151, 164, 199, 0.12);
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(36, 201, 154, 0.1), rgba(110, 168, 254, 0.08));

  h4 {
    margin: 0 0 10px;
    font-size: 20px;
  }

  p {
    margin: 0;
    color: #a1afce;
    line-height: 1.7;
  }
}

.placeholder-hero__icon {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 64px;
  height: 64px;
  border-radius: 22px;
  background: linear-gradient(135deg, #24c99a, #6ea8fe);
  color: #071221;
  font-size: 34px;
  font-weight: 800;
}

.placeholder-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.placeholder-block {
  padding: 22px 20px;
  border: 1px solid rgba(151, 164, 199, 0.12);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.03);

  span {
    display: inline-flex;
    margin-bottom: 14px;
    color: #63e6be;
    font-size: 12px;
    letter-spacing: 0.12em;
  }

  strong {
    display: block;
    margin-bottom: 10px;
    font-size: 18px;
  }

  p {
    margin: 0;
    color: #93a0c2;
    line-height: 1.7;
  }
}
</style>
