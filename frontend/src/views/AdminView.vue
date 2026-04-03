<template>
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Admin Command Center</p>
        <h1>Admin Panel</h1>
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