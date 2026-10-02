import { ApplyForm } from "@/components/apply/apply-form";

export default async function ApplyPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <ApplyForm slug={slug} />;
}
