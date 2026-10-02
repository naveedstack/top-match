import { Icon } from "@/components/icon";

export function AuthErrorBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-space-sm rounded-lg border border-error/30 bg-error-container/60 p-space-sm"
    >
      <Icon name="error" className="mt-0.5 shrink-0 text-lg text-error" />
      <p className="text-body-sm text-on-error-container">{message}</p>
    </div>
  );
}
