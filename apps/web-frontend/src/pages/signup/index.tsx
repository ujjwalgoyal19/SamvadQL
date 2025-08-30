import { SignupForm } from '@/components/auth/signup-form';

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted">
      <div className="w-full max-w-md p-8 bg-background rounded-lg shadow-md">
        <SignupForm />
      </div>
    </div>
  );
}
