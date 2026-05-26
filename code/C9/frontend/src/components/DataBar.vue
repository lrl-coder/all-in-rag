<template>
  <div class="data-bar">
    <div class="data-row">
      <span>{{ label }}</span>
      <strong>{{ value }}</strong>
    </div>
    <div class="track">
      <div class="fill" :style="{ width: width }"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  label: { type: String, required: true },
  value: { type: Number, required: true },
  max: { type: Number, required: true },
});

const width = computed(() => `${Math.max(3, Math.min(100, (props.value / Math.max(1, props.max)) * 100))}%`);
</script>
