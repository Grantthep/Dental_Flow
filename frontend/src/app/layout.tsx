import type { Metadata } from "next";
import { Shell } from "@/components/Shell";
import { RoleProvider } from "@/lib/role";
import "./globals.css";

export const metadata: Metadata = {
  title: "DentalFlow",
  description: "Dental clinic appointments, patients and reports",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <RoleProvider>
          <Shell>{children}</Shell>
        </RoleProvider>
      </body>
    </html>
  );
}
