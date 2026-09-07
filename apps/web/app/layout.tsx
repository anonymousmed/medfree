import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AppShell } from "@/components/AppShell";
import { ThemeProvider } from "@/components/ThemeProvider";
import { AuthProvider } from "@/components/AuthProvider";
import { PRODUCT_TAGLINE } from "@medfree/config";

export const metadata: Metadata = {
  title: {
    default: "MEDFREE — Digital Medical University",
    template: "%s · MEDFREE",
  },
  description: PRODUCT_TAGLINE,
  applicationName: "MEDFREE",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "MEDFREE",
    statusBarStyle: "black-translucent",
  },
  icons: {
    icon: [{ url: "/icon-192.svg", type: "image/svg+xml" }],
    apple: "/icon-192.svg",
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://medfree.example.com"),
  openGraph: {
    title: "MEDFREE",
    description: PRODUCT_TAGLINE,
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0c12",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body className="antialiased">
        <ThemeProvider>
          <AuthProvider>
            <AppShell>{children}</AppShell>
          </AuthProvider>
        </ThemeProvider>
        {/* Register the service worker for PWA/offline support (Step 18). */}
        <script
          dangerouslySetInnerHTML={{
            __html: `if ("serviceWorker" in navigator) {
              window.addEventListener("load", () => {
                navigator.serviceWorker.register("/sw.js").catch(() => {});
              });
            }`,
          }}
        />
      </body>
    </html>
  );
}
