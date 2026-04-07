<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import AppShell from "../components/AppShell.vue";
import {
  clearAccessToken,
  getCurrentUser,
  getHardware,
  rentHardware,
  returnHardware,
  type AuthUser,
  type HardwareListItem,
} from "../api/client";

const router = useRouter();

const currentUser = ref<AuthUser | null>(null);
const hardwareItems = ref<HardwareListItem[]>([]);
const isLoading = ref(true);
const errorMessage = ref("");
const successMessage = ref("");
const activeHardwareActionId = ref<number | null>(null);

const selectedStatus = ref("");
const selectedBrand = ref("");
const selectedSortBy = ref<
  "id" | "name" | "brand" | "purchase_date_raw" | "status_raw"
>("id");
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

function clearMessages() {
  successMessage.value = "";
  errorMessage.value = "";
}

async function scrollToTopForFeedback() {
  await nextTick();

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

function getStatusClass(status: string | null): string {
  if (status === "Available") return "status-available";
  if (status === "In Use") return "status-in-use";
  if (status === "Repair") return "status-repair";
  return "status-unknown";
}

function isAuthErrorMessage(message: string): boolean {
  const normalizedMessage = message.toLowerCase();

  return (
    normalizedMessage.includes("not authenticated") ||
    normalizedMessage.includes("authentication") ||
    normalizedMessage.includes("invalid or expired authentication token") ||
    normalizedMessage.includes("authenticated user was not found")
  );
}

async function handleUnauthorized() {
  clearAccessToken();
  await router.push("/login");
}

async function loadHardware() {
  isLoading.value = true;

  try {
    hardwareItems.value = await getHardware({
      status: selectedStatus.value || undefined,
      brand: selectedBrand.value || undefined,
      sortBy: selectedSortBy.value,
      sortDir: selectedSortDir.value,
    });
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Failed to load hardware inventory.";

    if (isAuthErrorMessage(message)) {
      await handleUnauthorized();
      return;
    }

    errorMessage.value = message;
  } finally {
    isLoading.value = false;
  }
}

async function initializeDashboard() {
  try {
    currentUser.value = await getCurrentUser();
    await loadHardware();
  } catch {
    await handleUnauthorized();
  }
}

function canRentItem(item: HardwareListItem): boolean {
  return item.status_raw === "Available";
}

function canReturnItem(item: HardwareListItem): boolean {
  return (
    item.status_raw === "In Use" &&
    item.assigned_to === currentUser.value?.email
  );
}

async function handleRent(item: HardwareListItem) {
  clearMessages();
  activeHardwareActionId.value = item.id;

  try {
    const updatedItem = await rentHardware(item.id);
    successMessage.value = `You rented ${updatedItem.name}.`;
    await loadHardware();
    await scrollToTopForFeedback();
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to rent hardware item.";

    if (isAuthErrorMessage(message)) {
      await handleUnauthorized();
      return;
    }

    errorMessage.value = message;
    await scrollToTopForFeedback();
  } finally {
    activeHardwareActionId.value = null;
  }
}

async function handleReturn(item: HardwareListItem) {
  clearMessages();
  activeHardwareActionId.value = item.id;

  try {
    const updatedItem = await returnHardware(item.id);
    successMessage.value = `You returned ${updatedItem.name}.`;
    await loadHardware();
    await scrollToTopForFeedback();
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to return hardware item.";

    if (isAuthErrorMessage(message)) {
      await handleUnauthorized();
      return;
    }

    errorMessage.value = message;
    await scrollToTopForFeedback();
  } finally {
    activeHardwareActionId.value = null;
  }
}

async function handleRefresh() {
  clearMessages();
  await loadHardware();
}

watch(
  [selectedStatus, selectedBrand, selectedSortBy, selectedSortDir],
  () => {
    if (currentUser.value) {
      void loadHardware();
    }
  },
);

onMounted(() => {
  void initializeDashboard();
});
</script>

<template>
  <main v-if="isLoading && !currentUser" class="screen">
    <section class="card">
      <p class="state-text">Loading inventory...</p>
    </section>
  </main>

  <AppShell
    v-else-if="currentUser"
    title="Hardware List"
    subtitle="Browse available gear, filter the inventory, and rent devices."
    :current-user-email="currentUser.email"
    :is-admin="currentUser.is_admin"
  >
    <template #actions>
      <button type="button" class="secondary-button" @click="handleRefresh">
        Refresh
      </button>
    </template>

    <p v-if="successMessage" class="feedback-banner feedback-success">
      {{ successMessage }}
    </p>

    <p v-if="errorMessage" class="feedback-banner feedback-error">
      {{ errorMessage }}
    </p>

    <section class="panel">
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

      <div v-else class="table-wrapper">
        <table class="inventory-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Brand</th>
              <th>Purchase Date</th>
              <th>Status</th>
              <th>Assigned To</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="item in hardwareItems" :key="item.id">
              <td>{{ item.name }}</td>
              <td>{{ item.brand || "—" }}</td>
              <td>{{ item.purchase_date_raw || "—" }}</td>
              <td>
                <span class="status-pill" :class="getStatusClass(item.status_raw)">
                  {{ item.status_raw || "—" }}
                </span>
              </td>
              <td>{{ item.assigned_to || "—" }}</td>
              <td>
                <div class="table-actions">
                  <button
                    v-if="canRentItem(item)"
                    type="button"
                    :disabled="activeHardwareActionId === item.id"
                    @click="handleRent(item)"
                  >
                    {{ activeHardwareActionId === item.id ? "Working..." : "Rent" }}
                  </button>

                  <button
                    v-else-if="canReturnItem(item)"
                    type="button"
                    class="secondary-button"
                    :disabled="activeHardwareActionId === item.id"
                    @click="handleReturn(item)"
                  >
                    {{ activeHardwareActionId === item.id ? "Working..." : "Return" }}
                  </button>

                  <span v-else class="table-empty-action">—</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </AppShell>
</template>