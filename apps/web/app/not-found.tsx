import { ButtonLink } from "@/components/ui/button";
import { Logo } from "@/components/logo";

export default function NotFound() {
  return (
    <main id="main" className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center px-4 text-center">
      <Logo />
      <h1 className="mt-6 text-2xl font-bold">We couldn&apos;t find that page.</h1>
      <p className="mt-2 text-muted">It may have moved, or the link may be wrong.</p>
      <ButtonLink href="/" className="mt-6">
        Go to the home page
      </ButtonLink>
    </main>
  );
}
