<template>
  <article class="ring-metric">
    <div class="ring" :style="{ '--score': normalizedScore }">
      <span>{{ normalizedScore }}</span>
    </div>
    <p>{{ label }}</p>
  </article>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  label: { type: String, required: true },
  value: { type: Number, required: true },
});

const normalizedScore = computed(() => Math.max(0, Math.min(100, Math.round(props.value))));
</script>
