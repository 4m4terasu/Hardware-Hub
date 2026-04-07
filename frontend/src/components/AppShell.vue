<script setup lang="ts">
import { useRouter, RouterLink } from "vue-router";
import { clearAccessToken } from "../api/client";

const props = defineProps<{
  title: string;
  subtitle?: string;
  currentUserEmail?: string | null;
  isAdmin?: boolean;
}>();

const router = useRouter();

async function handleLogout() {
  clearAccessToken();
  await router.push("/login");
}
</script>

<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="app-sidebar-top">
        <div class="app-brand">
          <div class="app-brand-mark">▣</div>
          <div class="app-brand-text">
            <strong>Hardware Manager</strong>
          </div>
        </div>

        <nav class="app-nav">
          <RouterLink to="/dashboard" class="app-nav-link">
            Hardware List
          </RouterLink>

          <RouterLink to="/my-rentals" class="app-nav-link">
            My Rentals
          </RouterLink>

          <RouterLink v-if="props.isAdmin" to="/admin" class="app-nav-link">
            Admin Panel
          </RouterLink>
        </nav>
      </div>

      <div class="app-sidebar-bottom">
        <button type="button" class="app-logout-button" @click="handleLogout">
          Logout
        </button>
      </div>
    </aside>

    <main class="app-main">
      <header class="page-header">
        <div>
          <p class="eyebrow">Booksy Internal Tool</p>
          <h1>{{ props.title }}</h1>

          <p v-if="props.subtitle" class="muted">
            {{ props.subtitle }}
          </p>

          <p v-if="props.currentUserEmail" class="muted page-user">
            Signed in as {{ props.currentUserEmail }}
          </p>
        </div>

        <div class="page-actions">
          <slot name="actions" />
        </div>
      </header>

      <section class="page-content">
        <slot />
      </section>
    </main>
  </div>
</template>