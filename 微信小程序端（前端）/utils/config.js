// utils/config.js
// 统一环境配置：默认使用本机后端，适合无外网/离线演示

const ENV = 'dev' // dev | lan | prod

const CONFIG = {
  dev: {
    host: 'http://127.0.0.1:8000',
    baseURL: 'http://127.0.0.1:8000/api',
    requestTimeout: 15000
  },
  lan: {
    // 真机调试时，把这里改成电脑当前局域网 IP
    host: 'http://10.96.134.240:8000',
    baseURL: 'http://10.96.134.240:8000/api',
    requestTimeout: 15000
  },
  prod: {
    host: 'https://your-domain.com',
    baseURL: 'https://your-domain.com/api',
    requestTimeout: 15000
  }
}

module.exports = {
  ENV,
  ...CONFIG[ENV]
}


