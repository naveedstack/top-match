import { ApplyForm } from "@/components/apply/apply-form";

export default async function ApplyPage({
  params,
}: {
  params: Promise<{ company: string; slug: string }>;
}) {
  const { company, slug } = await params;
  return <ApplyForm company={company} slug={slug} />;
}
