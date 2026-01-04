"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

export default function ResetPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/update-password`,
      });

      if (error) throw error;

      setSuccess(true);
    } catch (error: any) {
      setError(error.message || "Failed to send reset email");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex flex-col">
      {/* Header */}
      <div className="p-6">
        <Link href="/" className="flex items-center gap-2 text-blue-600 hover:text-blue-700">
          <Image
            src="/Adobe Express - file.png"
            alt="JobFlow Logo"
            width={32}
            height={32}
            className="rounded-lg"
          />
          <span className="text-2xl font-bold">JobFlow</span>
        </Link>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-white rounded-lg shadow-lg border-0 p-8">
          {/* Title */}
          <div className="space-y-2 pb-6">
            <h1 className="text-3xl font-semibold text-center text-gray-900">
              Reset Password
            </h1>
            <p className="text-center text-gray-600 text-sm">
              Enter your email and we'll send you a link to reset your password
            </p>
          </div>

          {success ? (
            /* Success Message */
            <div className="space-y-4">
              <div className="p-4 rounded-md bg-green-50 border border-green-200">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-green-800">
                      Check your email!
                    </h3>
                    <div className="mt-2 text-sm text-green-700">
                      <p>We've sent a password reset link to <strong>{email}</strong></p>
                      <p className="mt-1">Click the link in the email to reset your password.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-center">
                <Link
                  href="/sign-in"
                  className="text-blue-600 hover:underline text-sm font-medium"
                >
                  Return to sign in
                </Link>
              </div>
            </div>
          ) : (
            /* Reset Form */
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium text-gray-700">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="you@example.com"
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-3 rounded-md text-sm bg-red-50 text-red-700 border border-red-200">
                  {error}
                </div>
              )}

              {/* Reset Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-md transition-colors"
              >
                {loading ? "Sending..." : "Send Reset Link"}
              </button>
            </form>
          )}

          {/* Back to Sign In */}
          {!success && (
            <div className="mt-6 text-center text-sm text-gray-600">
              Remember your password?{" "}
              <Link href="/sign-in" className="text-blue-600 font-semibold hover:underline">
                Sign in
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center pb-8 text-sm text-gray-600">
        <p>Copyright © 2026 JobFlow. All rights reserved.</p>
      </div>
    </div>
  );
}
