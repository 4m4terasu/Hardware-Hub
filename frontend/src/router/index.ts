import { createRouter, createWebHistory } from "vue-router";
import { getAccessToken } from "../api/client";
import LoginView from "../views/LoginView.vue";
import DashboardView from "../views/DashboardView.vue";
import AdminView from "../views/AdminView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/login" },
    { path: "/login", name: "login", component: LoginView },
    { path: "/dashboard", name: "dashboard", component: DashboardView },
    { path: "/admin", name: "admin", component: AdminView },
  ],
});

router.beforeEach((to) => {
  const token = getAccessToken();
  const requiresAuth = to.name === "dashboard" || to.name === "admin";

  if (requiresAuth && !token) {
    return { name: "login" };
  }

  if (to.name === "login" && token) {
    return { name: "dashboard" };
  }

  return true;
});

export default router;