import { ProfileEditor } from "@/components/ProfileEditor";

export const metadata = { title: "Profile — MEDFREE" };

export default function ProfilePage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <ProfileEditor />
    </div>
  );
}
