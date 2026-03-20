<script setup lang="ts">
import Header from './Header.vue'
</script>

<template>
  <div class="min-h-screen flex flex-col bg-neutral-50">
    <Header />
    <main class="flex-1 p-6">
      <div class="max-w-5xl mx-auto">
        <slot />
      </div>
    </main>
  </div>
</template>