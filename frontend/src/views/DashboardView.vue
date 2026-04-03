<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { getHardware, type HardwareListItem } from "../api/client";

const hardwareItems = ref<HardwareListItem[]>([]);
const isLoading = ref(true);
const errorMessage = ref("");

const selectedStatus = ref("");
const selectedBrand = ref("");
const selectedSortBy = ref<"id" | "name" | "brand" | "purchase_date_raw" | "status_raw">("id");
const selectedSortDir = ref<"asc" | "desc">("asc");

const availableStatuses = ["Available", "In Use", "Repair"];

const availableBrands = computed(() => {
  const uniqueBrands = new Set(
    hardwareItems.value
      .map((item) => item.brand)
      .filter((brand): brand is string => Boolean(brand)),
  );

  return Array.from(uniqueBrands).sort((a, b) => a.localeCompare(b));
});

async function loadHardware() {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    hardwareItems.value = await getHardware({
      status: selectedStatus.value || undefined,
      brand: selectedBrand.value || undefined,
      sortBy: selectedSortBy.value,
      sortDir: selectedSortDir.value,
    });
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : "Failed to load hardware inventory.";
  } finally {
    isLoading.value = false;
  }
}

watch(
  [selectedStatus, selectedBrand, selectedSortBy, selectedSortDir],
  () => {
    void loadHardware();
  },
);

onMounted(() => {
  void loadHardware();
});
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Dashboard</p>
        <h1>Hardware Hub</h1>
      </div>

      <nav class="nav">
        <RouterLink to="/admin">Admin</RouterLink>
        <RouterLink to="/login">Logout</RouterLink>
      </nav>
    </header>

    <section class="panel">
      <div class="panel-header">
        <div>
          <h2>Inventory</h2>
          <p class="muted">Read-only dashboard connected to the backend API.</p>
        </div>

        <button type="button" class="secondary-button" @click="loadHardware">
          Refresh
        </button>
      </div>

      <div class="controls-row">
        <label class="control-field">
          <span>Status</span>
          <select v-model="selectedStatus">
            <option value="">All statuses</option>
            <option v-for="status in availableStatuses" :key="status" :value="status">
              {{ status }}
            </option>
          </select>
        </label>

        <label class="control-field">
          <span>Brand</span>
          <select v-model="selectedBrand">
            <option value="">All brands</option>
            <option v-for="brand in availableBrands" :key="brand" :value="brand">
              {{ brand }}
            </option>
          </select>
        </label>

        <label class="control-field">
          <span>Sort by</span>
          <select v-model="selectedSortBy">
            <option value="id">ID</option>
            <option value="name">Name</option>
            <option value="brand">Brand</option>
            <option value="purchase_date_raw">Purchase Date</option>
            <option value="status_raw">Status</option>
          </select>
        </label>

        <label class="control-field">
          <span>Direction</span>
          <select v-model="selectedSortDir">
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>
        </label>
      </div>

      <p v-if="isLoading" class="state-text">Loading inventory...</p>
      <p v-else-if="errorMessage" class="state-text error-text">
        {{ errorMessage }}
      </p>

      <div v-else class="table-wrapper">
        <table class="inventory-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Brand</th>
              <th>Purchase Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in hardwareItems" :key="item.id">
              <td>{{ item.name }}</td>
              <td>{{ item.brand || "—" }}</td>
              <td>{{ item.purchase_date_raw || "—" }}</td>
              <td>{{ item.status_raw || "—" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>