"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, token } from "./api";
import type { Role, User } from "./types";

// The logged-in user comes from /auth/me (token in localStorage). Every page reads the role via useRole().
// The role only hides pages and buttons; the backend is what actually enforces access (docs/roles.md).

type Auth = { user: User | null; signIn: (t: string, u: User) => void; logout: () => void };

const AuthContext = createContext<Auth>({ user: null, signIn: () => {}, logout: () => {} });

export function RoleProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [checked, setChecked] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const onLogin = pathname === "/login";

  useEffect(() => {
    if (!token.get()) {
      setChecked(true);
      return;
    }
    api.auth
      .me()
      .then(setUser)
      .catch(() => token.clear()) // 401 already redirects; anything else: log in again
      .finally(() => setChecked(true));
  }, []);

  useEffect(() => {
    if (checked && !user && !onLogin) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [checked, user, onLogin, pathname, router]);

  const signIn = useCallback((t: string, u: User) => {
    token.set(t);
    setUser(u);
  }, []);

  const logout = useCallback(() => {
    token.clear();
    setUser(null);
    router.replace("/login");
  }, [router]);

  // Don't flash protected pages before we know who is logged in.
  if (!onLogin && !user) return null;
  return <AuthContext.Provider value={{ user, signIn, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
/** Role of the logged-in user. Pages under the shell only render once someone is logged in. */
export const useRole = (): Role => useContext(AuthContext).user?.role ?? "dentist";

/** What each role may do in the UI. The backend enforces the same rules. */
export const can = {
  book: (r: Role) => r !== "dentist",
  editPatients: (r: Role) => r !== "dentist",
  // Dentists may only mark their own appointments completed / no-show and edit notes.
  confirm: (r: Role) => r !== "dentist",
  editReason: (r: Role) => r !== "dentist",
  reports: (r: Role) => r === "admin",
};
