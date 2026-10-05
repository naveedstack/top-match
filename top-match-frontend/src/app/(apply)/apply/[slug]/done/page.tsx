import { LegacyApplyRedirect } from "@/components/apply/legacy-apply-redirect";

export default async function LegacyApplyDonePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return <LegacyApplyRedirect slug={slug} suffix="/done" />;
}
