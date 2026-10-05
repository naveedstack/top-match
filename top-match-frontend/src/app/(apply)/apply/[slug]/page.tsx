import { LegacyApplyRedirect } from "@/components/apply/legacy-apply-redirect";

export default async function LegacyApplyPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <LegacyApplyRedirect slug={slug} />;
}
