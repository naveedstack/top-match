import { ApplySuccess } from "@/components/apply/apply-success";

export default async function ApplyDonePage({
  params,
}: {
  params: Promise<{ company: string; slug: string }>;
}) {
  const { company, slug } = await params;
  return <ApplySuccess company={company} slug={slug} />;
}
