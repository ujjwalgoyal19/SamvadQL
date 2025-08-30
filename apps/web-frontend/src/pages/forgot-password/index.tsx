import { ForgotPasswordForm } from '@/components/auth/forgot-password-form';

export default function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted">
      <div className="w-full max-w-md p-8 bg-background rounded-lg shadow-md">
        <ForgotPasswordForm />
      </div>
    </div>
  );
}
