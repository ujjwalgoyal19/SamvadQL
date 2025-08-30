import { LoginForm } from '@/components/auth/login-form';

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted">
      <div className="w-full max-w-md p-8 bg-background rounded-lg shadow-md">
        <LoginForm />
      </div>
    </div>
  );
}
