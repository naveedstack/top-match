import { ApplySuccess } from "@/components/apply/apply-success";

export default async function ApplyDonePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <ApplySuccess slug={slug} />;
}
