<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "../api/client";

const router = useRouter();

const email = ref("");
const password = ref("");
const errorMessage = ref("");
const isSubmitting = ref(false);

async function handleSubmit() {
  errorMessage.value = "";
  isSubmitting.value = true;

  try {
    await login({
      email: email.value,
      password: password.value,
    });

    await router.push("/dashboard");
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Login failed.";
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <main class="screen">
    <section class="card">
      <p class="eyebrow">Booksy Internal Tool</p>
      <h1>Hardware Hub</h1>
      <p class="muted">Sign in with an admin-created account.</p>

      <form class="stack" @submit.prevent="handleSubmit">
        <label class="form-field">
          <span>Email</span>
          <input v-model="email" type="email" placeholder="admin@booksy.com" />
        </label>

        <label class="form-field">
          <span>Password</span>
          <input
            v-model="password"
            type="password"
            placeholder="Enter your password"
          />
        </label>

        <p v-if="errorMessage" class="form-error">
          {{ errorMessage }}
        </p>

        <button type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? "Signing in..." : "Sign in" }}
        </button>
      </form>
    </section>
  </main>
</template>