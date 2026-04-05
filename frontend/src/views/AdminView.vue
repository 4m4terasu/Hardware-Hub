<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  clearAccessToken,
  createAdminHardware,
  createAdminUser,
  deleteAdminHardware,
  getCurrentUser,
  getHardware,
  toggleAdminRepairStatus,
  type AuthUser,
  type HardwareListItem,
} from "../api/client";

const router = useRouter();

const currentUser = ref<AuthUser | null>(null);
const hardwareItems = ref<HardwareListItem[]>([]);

const isCheckingAccess = ref(true);
const isLoadingHardware = ref(false);
const isCreatingUser = ref(false);
const isCreatingHardware = ref(false);
const activeHardwareActionId = ref<number | null>(null);

const successMessage = ref("");
const errorMessage = ref("");

const userEmail = ref("");
const userPassword = ref("");
const userIsAdmin = ref(false);

const hardwareName = ref("");
const hardwareBrand = ref("");
const hardwarePurchaseDateRaw = ref("");
const hardwareNotes = ref("");
const hardwareHistoryText = ref("");

function clearMessages() {
  successMessage.value = "";
  errorMessage.value = "";
}

function resetUserForm() {
  userEmail.value = "";
  userPassword.value = "";
  userIsAdmin.value = false;
}

function resetHardwareForm() {
  hardwareName.value = "";
  hardwareBrand.value = "";
  hardwarePurchaseDateRaw.value = "";
  hardwareNotes.value = "";
  hardwareHistoryText.value = "";
}

async function handleUnauthorized() {
  clearAccessToken();
  await router.replace("/login");
}

async function loadHardware() {
  isLoadingHardware.value = true;

  try {
    hardwareItems.value = await getHardware({
      sortBy: "id",
      sortDir: "asc",
    });
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Failed to load hardware inventory.";

    if (message.toLowerCase().includes("authentication")) {
      await handleUnauthorized();
      return;
    }

    errorMessage.value = message;
  } finally {
    isLoadingHardware.value = false;
  }
}

async function initializeAdminView() {
  try {
    const user = await getCurrentUser();

    if (!user.is_admin) {
      await router.replace("/dashboard");
      return;
    }

    currentUser.value = user;
    await loadHardware();
  } catch {
    await handleUnauthorized();
    return;
  } finally {
    isCheckingAccess.value = false;
  }
}

async function handleCreateUser() {
  clearMessages();
  isCreatingUser.value = true;

  try {
    const createdUser = await createAdminUser({
      email: userEmail.value,
      password: userPassword.value,
      is_admin: userIsAdmin.value,
    });

    successMessage.value = `User created: ${createdUser.email}`;
    resetUserForm();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to create user.";
  } finally {
    isCreatingUser.value = false;
  }
}

async function handleCreateHardware() {
  clearMessages();
  isCreatingHardware.value = true;

  try {
    const createdHardware = await createAdminHardware({
      name: hardwareName.value,
      brand: hardwareBrand.value,
      purchase_date_raw: hardwarePurchaseDateRaw.value,
      notes: hardwareNotes.value,
      history_text: hardwareHistoryText.value,
    });

    successMessage.value = `Hardware created: ${createdHardware.name} (ID ${createdHardware.id})`;
    resetHardwareForm();
    await loadHardware();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to create hardware.";
  } finally {
    isCreatingHardware.value = false;
  }
}

async function handleToggleRepair(item: HardwareListItem) {
  clearMessages();
  activeHardwareActionId.value = item.id;

  try {
    const updatedItem = await toggleAdminRepairStatus(item.id);
    successMessage.value = `Repair status updated for item ${updatedItem.id}.`;
    await loadHardware();
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : "Failed to toggle repair status.";
  } finally {
    activeHardwareActionId.value = null;
  }
}

async function handleDeleteHardware(item: HardwareListItem) {
  const confirmed = window.confirm(
    `Delete hardware item "${item.name}" (ID ${item.id})?`,
  );

  if (!confirmed) {
    return;
  }

  clearMessages();
  activeHardwareActionId.value = item.id;

  try {
    await deleteAdminHardware(item.id);
    successMessage.value = `Hardware item ${item.id} deleted.`;
    await loadHardware();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to delete hardware.";
  } finally {
    activeHardwareActionId.value = null;
  }
}

async function handleRefresh() {
  clearMessages();
  await loadHardware();
}

async function handleLogout() {
  clearAccessToken();
  await router.push("/login");
}

function getRepairButtonLabel(item: HardwareListItem): string {
  if (item.status_raw === "Repair") {
    return "Mark Available";
  }

  return "Send to Repair";
}

onMounted(() => {
  void initializeAdminView();
});
</script>

<template>
  <main v-if="isCheckingAccess" class="shell">
    <section class="panel">
      <p class="state-text">Checking admin access...</p>
    </section>
  </main>

  <main v-else-if="currentUser" class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Admin Command Center</p>
        <h1>Admin Panel</h1>
        <p class="muted">
          Signed in as {{ currentUser.email }}
        </p>
      </div>

      <nav class="nav">
        <RouterLink to="/dashboard">Dashboard</RouterLink>
        <button type="button" class="nav-button" @click="handleLogout">
          Logout
        </button>
      </nav>
    </header>

    <p v-if="successMessage" class="feedback-banner feedback-success">
      {{ successMessage }}
    </p>

    <p v-if="errorMessage" class="feedback-banner feedback-error">
      {{ errorMessage }}
    </p>

    <section class="grid">
      <article class="panel">
        <div class="panel-header">
          <div>
            <h2>Create User</h2>
            <p class="muted">Only admin-created users can access the app.</p>
          </div>
        </div>

        <form class="stack" autocomplete="off" @submit.prevent="handleCreateUser">
          <label class="form-field">
            <span>Email</span>
            <input
              v-model="userEmail"
              name="admin-create-user-email"
              type="email"
              placeholder="new.user@booksy.com"
              autocomplete="off"
              autocapitalize="none"
              spellcheck="false"
              required
            />
          </label>

          <label class="form-field">
            <span>Password</span>
            <input
              v-model="userPassword"
              name="admin-create-user-password"
              type="password"
              placeholder="Enter a temporary password"
              autocomplete="new-password"
              required
            />
          </label>

          <label class="checkbox-field">
            <input v-model="userIsAdmin" type="checkbox" />
            <span>Create as admin account</span>
          </label>

          <button type="submit" :disabled="isCreatingUser">
            {{ isCreatingUser ? "Creating user..." : "Create User" }}
          </button>
        </form>
      </article>

      <article class="panel">
        <div class="panel-header">
          <div>
            <h2>Add Hardware</h2>
            <p class="muted">Create a new inventory item with raw-friendly fields.</p>
          </div>
        </div>

        <form class="stack" autocomplete="off" @submit.prevent="handleCreateHardware">
          <label class="form-field">
            <span>Name</span>
            <input
              v-model="hardwareName"
              name="admin-create-hardware-name"
              type="text"
              placeholder="MacBook Pro 14"
              autocomplete="off"
              required
            />
          </label>

          <label class="form-field">
            <span>Brand</span>
            <input
              v-model="hardwareBrand"
              name="admin-create-hardware-brand"
              type="text"
              placeholder="Apple"
              autocomplete="off"
            />
          </label>

          <label class="form-field">
            <span>Purchase Date</span>
            <input
              v-model="hardwarePurchaseDateRaw"
              name="admin-create-hardware-date"
              type="date"
              autocomplete="off"
            />
          </label>

          <label class="form-field">
            <span>Notes</span>
            <textarea
              v-model="hardwareNotes"
              name="admin-create-hardware-notes"
              placeholder="Optional notes for admins"
              autocomplete="off"
            />
          </label>

          <label class="form-field">
            <span>History</span>
            <textarea
              v-model="hardwareHistoryText"
              name="admin-create-hardware-history"
              placeholder="Optional history or context"
              autocomplete="off"
            />
          </label>

          <button type="submit" :disabled="isCreatingHardware">
            {{ isCreatingHardware ? "Adding hardware..." : "Add Hardware" }}
          </button>
        </form>
      </article>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <h2>Admin Hardware Inventory</h2>
          <p class="muted">
            Toggle repair status, review metadata, and delete old items.
          </p>
        </div>

        <button
          type="button"
          class="secondary-button"
          :disabled="isLoadingHardware"
          @click="handleRefresh"
        >
          {{ isLoadingHardware ? "Refreshing..." : "Refresh" }}
        </button>
      </div>

      <p v-if="isLoadingHardware" class="state-text">Loading hardware...</p>

      <div v-else class="table-wrapper">
        <table class="inventory-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Brand</th>
              <th>Purchase Date</th>
              <th>Status</th>
              <th>Assigned To</th>
              <th>Notes</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="item in hardwareItems" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.brand || "—" }}</td>
              <td>{{ item.purchase_date_raw || "—" }}</td>
              <td>{{ item.status_raw || "—" }}</td>
              <td>{{ item.assigned_to || "—" }}</td>
              <td>{{ item.notes || "—" }}</td>
              <td>
                <div class="table-actions">
                  <button
                    type="button"
                    class="secondary-button"
                    :disabled="activeHardwareActionId === item.id"
                    @click="handleToggleRepair(item)"
                  >
                    {{
                      activeHardwareActionId === item.id
                        ? "Working..."
                        : getRepairButtonLabel(item)
                    }}
                  </button>

                  <button
                    type="button"
                    class="danger-button"
                    :disabled="activeHardwareActionId === item.id"
                    @click="handleDeleteHardware(item)"
                  >
                    {{
                      activeHardwareActionId === item.id
                        ? "Working..."
                        : "Delete"
                    }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>