<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getHardware, type HardwareListItem } from "../api/client";

const hardwareItems = ref<HardwareListItem[]>([]);
const isLoading = ref(true);
const errorMessage = ref("");

async function loadHardware() {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    hardwareItems.value = await getHardware();
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : "Failed to load hardware inventory.";
  } finally {
    isLoading.value = false;
  }
}

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