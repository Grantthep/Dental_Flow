"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Role } from "./types";

// shortcut: there is no login yet, so the role comes from a switcher in the top bar (saved in localStorage).
// Member 3: replace this with the role from /auth/me after login — every page already reads it via useRole().

const RoleContext = createContext<{ role: Role; setRole: (r: Role) => void }>({ role: "admin", setRole: () => {} });

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<Role>("admin");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("df-role");
      if (saved === "admin" || saved === "receptionist" || saved === "dentist") setRoleState(saved);
    } catch {}
  }, []);

  const setRole = (r: Role) => {
    setRoleState(r);
    try {
      localStorage.setItem("df-role", r);
    } catch {}
  };

  return <RoleContext.Provider value={{ role, setRole }}>{children}</RoleContext.Provider>;
}

export const useRole = () => useContext(RoleContext).role;
export const useSetRole = () => useContext(RoleContext).setRole;

/** What each role may do in the UI. The backend enforces the same rules once auth is in. */
export const can = {
  book: (r: Role) => r !== "dentist",
  editPatients: (r: Role) => r !== "dentist",
  reports: (r: Role) => r === "admin",
};
