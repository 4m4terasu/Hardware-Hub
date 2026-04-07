<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import AppShell from "../components/AppShell.vue";
import {
  clearAccessToken,
  createAdminHardware,
  createAdminUser,
  deleteAdminHardware,
  getCurrentUser,
  getHardware,
  getInventoryAuditReport,
  toggleAdminRepairStatus,
  type AuthUser,
  type HardwareListItem,
  type InventoryAuditReport,
} from "../api/client";

const router = useRouter();

const currentUser = ref<AuthUser | null>(null);
const hardwareItems = ref<HardwareListItem[]>([]);
const auditReport = ref<InventoryAuditReport | null>(null);

const isCheckingAccess = ref(true);
const isLoadingHardware = ref(false);
const isCreatingUser = ref(false);
const isCreatingHardware = ref(false);
const isLoadingAudit = ref(false);
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

async function scrollToTopForFeedback() {
  await nextTick();

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
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

function getStatusClass(status: string | null): string {
  if (status === "Available") {
    return "status-available";
  }

  if (status === "In Use") {
    return "status-in-use";
  }

  if (status === "Repair") {
    return "status-repair";
  }

  return "status-unknown";
}

async function handleUnauthorized() {
  clearAccessToken();
  await router.replace("/login");
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

    if (isAuthErrorMessage(message)) {
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
    await scrollToTopForFeedback();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to create user.";
    await scrollToTopForFeedback();
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
    await scrollToTopForFeedback();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to create hardware.";
    await scrollToTopForFeedback();
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
    await scrollToTopForFeedback();
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : "Failed to toggle repair status.";
    await scrollToTopForFeedback();
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
    await scrollToTopForFeedback();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to delete hardware.";
    await scrollToTopForFeedback();
  } finally {
    activeHardwareActionId.value = null;
  }
}

async function handleRefresh() {
  clearMessages();
  await loadHardware();
}

async function handleRunAudit() {
  clearMessages();
  isLoadingAudit.value = true;

  try {
    auditReport.value = await getInventoryAuditReport();

    if (auditReport.value.ai_summary.fallback_used) {
      successMessage.value =
        "Deterministic audit loaded. Gemini fallback was used for the summary.";
    } else {
      successMessage.value = "Inventory audit report generated successfully.";
    }

    await scrollToTopForFeedback();
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Failed to load inventory audit report.";

    if (isAuthErrorMessage(message)) {
      await handleUnauthorized();
      return;
    }

    errorMessage.value = message;
    await scrollToTopForFeedback();
  } finally {
    isLoadingAudit.value = false;
  }
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
  <main v-if="isCheckingAccess" class="screen">
    <section class="card">
      <p class="state-text">Checking admin access...</p>
    </section>
  </main>

  <AppShell
    v-else-if="currentUser"
    title="Hardware Management"
    subtitle="Manage users, inventory state, and audit output."
    :current-user-email="currentUser.email"
    :is-admin="currentUser.is_admin"
  >
    <template #actions>
      <button
        type="button"
        class="secondary-button"
        :disabled="isLoadingHardware"
        @click="handleRefresh"
      >
        {{ isLoadingHardware ? "Refreshing..." : "Refresh" }}
      </button>
    </template>

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
            <p class="muted">Create a new inventory item using the existing fields.</p>
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
          <h2>Inventory Audit Report</h2>
          <p class="muted">
            Run the deterministic audit and let Gemini summarize the findings.
          </p>
        </div>

        <button
          type="button"
          class="secondary-button"
          :disabled="isLoadingAudit"
          @click="handleRunAudit"
        >
          {{ isLoadingAudit ? "Running audit..." : "Run Audit Report" }}
        </button>
      </div>

      <div v-if="auditReport" class="audit-layout">
        <article class="audit-card">
          <h3>Deterministic Summary</h3>
          <div class="audit-summary-grid">
            <div class="audit-metric">
              <span class="audit-metric-label">Items</span>
              <strong>{{ auditReport.summary.total_items }}</strong>
            </div>
            <div class="audit-metric">
              <span class="audit-metric-label">Findings</span>
              <strong>{{ auditReport.summary.total_findings }}</strong>
            </div>
            <div class="audit-metric">
              <span class="audit-metric-label">High</span>
              <strong>{{ auditReport.summary.high_severity_count }}</strong>
            </div>
            <div class="audit-metric">
              <span class="audit-metric-label">Medium</span>
              <strong>{{ auditReport.summary.medium_severity_count }}</strong>
            </div>
            <div class="audit-metric">
              <span class="audit-metric-label">Low</span>
              <strong>{{ auditReport.summary.low_severity_count }}</strong>
            </div>
          </div>
        </article>

        <article class="audit-card">
          <div class="audit-card-header">
            <div>
              <h3>Gemini Summary</h3>
              <p class="muted">
                Provider: {{ auditReport.ai_summary.provider || "gemini" }}
                <span v-if="auditReport.ai_summary.model">
                  · Model: {{ auditReport.ai_summary.model }}
                </span>
              </p>
            </div>

            <span
              class="audit-risk-badge"
              :class="`risk-${auditReport.ai_summary.risk_level}`"
            >
              {{ auditReport.ai_summary.risk_level }} risk
            </span>
          </div>

          <p
            v-if="auditReport.ai_summary.fallback_used"
            class="audit-fallback-note"
          >
            Gemini fallback was used. Deterministic findings are still valid.
          </p>

          <p class="audit-summary-text">
            {{ auditReport.ai_summary.summary_text }}
          </p>

          <div>
            <h4>Priority Actions</h4>
            <ul class="audit-actions-list">
              <li
                v-for="action in auditReport.ai_summary.priority_actions"
                :key="action"
              >
                {{ action }}
              </li>
            </ul>
          </div>

          <p v-if="auditReport.ai_summary.error_message" class="audit-error-note">
            Fallback reason: {{ auditReport.ai_summary.error_message }}
          </p>
        </article>

        <article class="audit-card audit-findings-card">
          <h3>Structured Findings</h3>

          <ul class="audit-findings-list">
            <li
              v-for="finding in auditReport.findings"
              :key="`${finding.issue_code}-${finding.hardware_id}-${finding.message}`"
              class="audit-finding-item"
            >
              <div class="audit-finding-topline">
                <span
                  class="audit-severity-badge"
                  :class="`severity-${finding.severity}`"
                >
                  {{ finding.severity }}
                </span>

                <strong>{{ finding.issue_code }}</strong>
              </div>

              <p class="audit-finding-title">
                {{ finding.hardware_name || "Inventory-level finding" }}
                <span v-if="finding.hardware_id !== null">
                  (ID {{ finding.hardware_id }})
                </span>
              </p>

              <p class="audit-finding-message">
                {{ finding.message }}
              </p>
            </li>
          </ul>
        </article>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <h2>Hardware Inventory</h2>
          <p class="muted">
            Review inventory state and manage repair / delete actions.
          </p>
        </div>
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
              <td>
                <span class="status-pill" :class="getStatusClass(item.status_raw)">
                  {{ item.status_raw || "—" }}
                </span>
              </td>
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
  </AppShell>
</template>