import type { Metadata } from "next";
import "./globals.css";
import { AppProviders } from "@/providers/AppProviders";

export const metadata: Metadata = {
  title: "Drone IMS Dashboard",
  description: "Warehouse drone inventory mission dashboard"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-950 text-zinc-50">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}

