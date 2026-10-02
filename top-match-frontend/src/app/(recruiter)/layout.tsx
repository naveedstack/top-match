import type { ReactNode } from "react";

import { RecruiterShell } from "@/components/recruiter-shell";
import { RequireAuth } from "@/components/require-auth";

export default function RecruiterLayout({ children }: { children: ReactNode }) {
  return (
    <RequireAuth>
      <RecruiterShell>{children}</RecruiterShell>
    </RequireAuth>
  );
}
