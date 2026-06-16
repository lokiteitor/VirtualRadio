// Route guard: protect every page except /login. Redirect authenticated users
// away from /login. The session is restored by plugins/session.client.ts first.
import { useSessionStore } from "~/entities/session";

export default defineNuxtRouteMiddleware((to) => {
  const session = useSessionStore();
  const isLoginPage = to.path === "/login";

  if (!session.isAuthenticated && !isLoginPage) {
    return navigateTo("/login");
  }
  if (session.isAuthenticated && isLoginPage) {
    return navigateTo("/");
  }
});
