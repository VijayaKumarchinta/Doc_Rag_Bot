<template>
  <main style="padding:2rem;font-family:sans-serif">
    <h1>Document RAG Chatbot</h1>
    <p>Backend status: <strong>{{ status }}</strong></p>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const status = ref('checking...')
onMounted(async () => {
  try {
    const { data } = await axios.get('/api/health')
    status.value = `${data.app} / db:${data.database}`
  } catch {
    status.value = 'unreachable'
  }
})
</script>