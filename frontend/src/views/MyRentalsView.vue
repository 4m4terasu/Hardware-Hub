<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import AppShell from "../components/AppShell.vue";
import {
  clearAccessToken,
  getCurrentUser,
  getHardware,
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

async function loadRentals() {
  isLoading.value = true;

  try {
    hardwareItems.value = await getHardware({
      sortBy: "id",
      sortDir: "asc",
    });
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Failed to load rental inventory.";

    if (isAuthErrorMessage(message)) {
      await handleUnauthorized();
      return;
    }

    errorMessage.value = message;
  } finally {
    isLoading.value = false;
  }
}

const myRentals = computed(() => {
  if (!currentUser.value) {
    return [];
  }

  return hardwareItems.value.filter(
    (item) =>
      item.assigned_to === currentUser.value?.email &&
      item.status_raw === "In Use",
  );
});

async function initializeMyRentals() {
  try {
    currentUser.value = await getCurrentUser();
    await loadRentals();
  } catch {
    await handleUnauthorized();
  }
}

async function handleReturn(item: HardwareListItem) {
  clearMessages();
  activeHardwareActionId.value = item.id;

  try {
    const updatedItem = await returnHardware(item.id);
    successMessage.value = `You returned ${updatedItem.name}.`;
    await loadRentals();
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
  await loadRentals();
}

onMounted(() => {
  void initializeMyRentals();
});
</script>

<template>
  <main v-if="isLoading && !currentUser" class="screen">
    <section class="card">
      <p class="state-text">Loading your rentals...</p>
    </section>
  </main>

  <AppShell
    v-else-if="currentUser"
    title="My Rentals"
    subtitle="View the devices currently assigned to you."
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
      <div class="table-wrapper">
        <table class="inventory-table">
          <thead>
            <tr>
              <th>Device Name</th>
              <th>Brand</th>
              <th>Purchase Date</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody v-if="myRentals.length > 0">
            <tr v-for="item in myRentals" :key="item.id">
              <td>{{ item.name }}</td>
              <td>{{ item.brand || "—" }}</td>
              <td>{{ item.purchase_date_raw || "—" }}</td>
              <td>
                <span class="status-pill" :class="getStatusClass(item.status_raw)">
                  {{ item.status_raw || "—" }}
                </span>
              </td>
              <td>
                <button
                  type="button"
                  class="secondary-button"
                  :disabled="activeHardwareActionId === item.id"
                  @click="handleReturn(item)"
                >
                  {{ activeHardwareActionId === item.id ? "Working..." : "Return" }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="!isLoading && myRentals.length === 0" class="empty-state">
          You don't have any active rentals.
        </div>
      </div>
    </section>
  </AppShell>
</template>