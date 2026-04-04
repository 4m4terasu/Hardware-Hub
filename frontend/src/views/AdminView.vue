<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  clearAccessToken,
  getCurrentUser,
  type AuthUser,
} from "../api/client";

const router = useRouter();

const currentUser = ref<AuthUser | null>(null);
const isCheckingAccess = ref(true);

async function initializeAdminView() {
  try {
    const user = await getCurrentUser();

    if (!user.is_admin) {
      await router.replace("/dashboard");
      return;
    }

    currentUser.value = user;
  } catch {
    clearAccessToken();
    await router.replace("/login");
    return;
  } finally {
    isCheckingAccess.value = false;
  }
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
      </nav>
    </header>

    <section class="grid">
      <article class="panel">
        <h2>Create User</h2>
        <p class="muted">Placeholder for admin-created accounts.</p>
      </article>

      <article class="panel">
        <h2>Add Hardware</h2>
        <p class="muted">Placeholder for inventory creation.</p>
      </article>
    </section>
  </main>
</template>