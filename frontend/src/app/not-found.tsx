import { ButtonLink } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="py-16 text-center">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="mt-2 text-slate-600">That page doesn&apos;t exist.</p>
      <ButtonLink href="/" className="mt-6">
        Back to dashboard
      </ButtonLink>
    </div>
  );
}
