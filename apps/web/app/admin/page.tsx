import { SectionHeading } from "@medfree/ui";
import { AdminPortal } from "@/components/AdminPortal";

export const metadata = { title: "Admin" };

export default function AdminPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <SectionHeading
        eyebrow="Admin"
        title="Platform Administration"
        subtitle="User management, resource review workflow, and Atlas asset management — all admin-only at the backend."
      />
      <AdminPortal />
    </div>
  );
}
