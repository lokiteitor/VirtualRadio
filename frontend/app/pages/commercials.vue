<script setup lang="ts">
import { onMounted, ref } from "vue";
import { AppPageHeader, AppEmptyState } from "~/shared/ui";
import { NAV_ITEMS } from "~/shared/config";
import { BrandCard, useBrandStore, type Brand } from "~/entities/brand";
import { CommercialCard, useCommercialStore, type Commercial } from "~/entities/commercial";
import { BrandForm } from "~/features/manage-brand";
import { CommercialForm } from "~/features/manage-commercial";

const nav = NAV_ITEMS.find((n) => n.id === "commercials");

const brandStore = useBrandStore();
const commercialStore = useCommercialStore();

const editingBrand = ref<Brand | null>(null);
const editingCommercial = ref<Commercial | null>(null);

function brandName(brandId: string): string {
  return brandStore.byId.get(brandId)?.name ?? "Marca desconocida";
}

async function refresh() {
  await Promise.all([brandStore.fetchAll(), commercialStore.fetchAll()]);
}

onMounted(refresh);

function scrollTop() {
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

function onEditBrand(b: Brand) {
  editingBrand.value = b;
  scrollTop();
}
async function onRemoveBrand(b: Brand) {
  if (confirm(`¿Eliminar la marca "${b.name}"? Se borrarán sus anuncios asociados.`)) {
    await brandStore.remove(b.id);
    await commercialStore.fetchAll();
  }
}

function onEditCommercial(c: Commercial) {
  editingCommercial.value = c;
  scrollTop();
}
async function onRemoveCommercial(c: Commercial) {
  if (confirm(`¿Eliminar el anuncio "${c.title}"?`)) {
    await commercialStore.remove(c.id);
  }
}
</script>

<template>
  <div>
    <AppPageHeader title="Comerciales" :subtitle="nav?.subtitle" />

    <div class="split-pane">
      <div class="left-list card-container">
        <div class="section-title-row">
          <h3>Comerciales Recurrentes</h3>
          <span class="badge">{{ commercialStore.items.length }} anuncios</span>
        </div>

        <div v-if="brandStore.items.length" class="brands-list-horizontal">
          <BrandCard
            v-for="b in brandStore.items"
            :key="b.id"
            :brand="b"
            class="brand-pill-clickable"
            @click="onEditBrand(b)"
          />
        </div>
        <AppEmptyState
          v-else-if="!brandStore.loading"
          icon="🏭"
          title="No hay marcas"
          message="Registra tu primera marca con el formulario de la derecha."
        />

        <div v-if="commercialStore.items.length" class="commercials-list">
          <CommercialCard
            v-for="c in commercialStore.items"
            :key="c.id"
            :commercial="c"
            :brand-name="brandName(c.brand_id)"
            @edit="onEditCommercial"
            @remove="onRemoveCommercial"
          />
        </div>
        <AppEmptyState
          v-else-if="!commercialStore.loading"
          icon="📢"
          title="No hay anuncios"
          message="Crea un guión publicitario para alguna de tus marcas."
        />
      </div>

      <div class="right-form-stack">
        <BrandForm :brand="editingBrand" @saved="editingBrand = null" @cancel="editingBrand = null" />
        <CommercialForm
          :commercial="editingCommercial"
          @saved="editingCommercial = null"
          @cancel="editingCommercial = null"
        />
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.brands-list-horizontal {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 12px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}
.brand-pill-clickable {
  cursor: pointer;
  transition: border-color 0.2s ease;
}
.brand-pill-clickable:hover {
  border-color: var(--primary);
}
.commercials-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.right-form-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
