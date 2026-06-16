<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { AppPageHeader, AppEmptyState } from "~/shared/ui";
import { NAV_ITEMS } from "~/shared/config";
import { NewsCard, useNewsStore, type NewsItem } from "~/entities/news-item";
import { NewsForm } from "~/features/manage-news";

const store = useNewsStore();
const editing = ref<NewsItem | null>(null);
const nav = computed(() => NAV_ITEMS.find((n) => n.id === "news"));

onMounted(() => store.fetchAll());

function onEdit(item: NewsItem) {
  editing.value = item;
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}
async function onRemove(item: NewsItem) {
  if (confirm(`¿Eliminar la noticia "${item.headline}"?`)) {
    await store.remove(item.id);
    if (editing.value?.id === item.id) editing.value = null;
  }
}
</script>

<template>
  <div>
    <AppPageHeader title="Noticias" :subtitle="nav?.subtitle" />

    <div class="split-pane">
      <div class="card-container">
        <div class="section-title-row">
          <h3>Biblioteca de Noticias</h3>
          <span class="badge">{{ store.items.length }} items</span>
        </div>
        <div v-if="store.items.length" class="news-list">
          <NewsCard
            v-for="item in store.items"
            :key="item.id"
            :item="item"
            @edit="onEdit"
            @remove="onRemove"
          />
        </div>
        <AppEmptyState
          v-else-if="!store.loading"
          icon="📰"
          title="No hay noticias"
          message="Crea tu primera noticia ficticia con el formulario de la derecha."
        />
      </div>

      <NewsForm :item="editing" @saved="editing = null" @cancel="editing = null" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.news-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
  padding-right: 8px;
}
</style>
