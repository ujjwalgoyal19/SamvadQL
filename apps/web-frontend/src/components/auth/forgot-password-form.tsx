import { cn } from '@/components/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import React, { useState } from 'react';
import { apiService } from '@/services/api';

export function ForgotPasswordForm({
  className,
  ...props
}: React.ComponentProps<'form'>) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const res = await apiService.forgotPassword(email);
    if (res.success) {
      setMessage(
        res.data?.message || 'If the email exists, a reset link will be sent.'
      );
      if (res.data?.reset_token) {
        // Expose token in dev for manual testing
        setMessage(
          `Reset token (dev only): ${res.data.reset_token}. Use on /reset-password page.`
        );
      }
    } else {
      setError(res.errors?.[0] || 'Failed to initiate reset');
    }
    setLoading(false);
  }
  return (
    <form
      className={cn('flex flex-col gap-6', className)}
      onSubmit={handleSubmit}
      {...props}
    >
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Forgot Password</h1>
        <p className="text-muted-foreground text-sm">
          Enter your email to reset your password
        </p>
      </div>
      <div className="grid gap-6">
        <div className="grid gap-3">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="m@example.com"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-red-500">{error}</p>}
        {message && (
          <p className="text-sm text-green-600 whitespace-pre-wrap">
            {message}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Sending...' : 'Reset Password'}
        </Button>
      </div>
      <div className="text-center text-sm">
        Remember your password?{' '}
        <a href="/signin" className="underline underline-offset-4">
          Sign in
        </a>
      </div>
    </form>
  );
}
