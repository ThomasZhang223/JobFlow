"use client";

import { Briefcase } from "lucide-react";
import Image from "next/image";

export default function SignInPage() {
  const handleOAuthSignIn = (provider: string) => {
    // OAuth sign-in logic will be implemented here
    console.log(`Sign in with ${provider}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex flex-col">
      <div className="p-6">
        <div className="flex items-center gap-2 text-blue-600">
          <Image
            src="/Adobe Express - file.png"
            alt="JobFlow Logo"
            width={32}
            height={32}
            className="rounded-lg"
          />
          <span className="text-2xl font-bold">JobFlow</span>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-white rounded-lg shadow-lg border-0 p-6">
          <div className="space-y-1 pb-4">
            <h1 className="text-3xl font-semibold text-center text-gray-900">Sign in</h1>
          </div>

          <div className="space-y-4">
            <div className="space-y-3">
              <button
                className="w-full h-12 text-base font-normal border-2 border-gray-300 hover:bg-slate-50 bg-transparent rounded-md flex items-center justify-center transition-colors text-gray-700"
                onClick={() => handleOAuthSignIn("google")}
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Continue with Google
              </button>

              <button
                className="w-full h-12 text-base font-normal border-2 border-gray-300 hover:bg-slate-50 bg-transparent rounded-md flex items-center justify-center transition-colors text-gray-700"
                onClick={() => handleOAuthSignIn("github")}
              >
                <svg className="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 24 24">
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z"
                  />
                </svg>
                Continue with GitHub
              </button>

              <button
                className="w-full h-12 text-base font-normal border-2 border-gray-300 hover:bg-slate-50 bg-transparent rounded-md flex items-center justify-center transition-colors text-gray-700"
                onClick={() => handleOAuthSignIn("twitter")}
              >
                <svg className="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
                Continue with X
              </button>

              <button
                className="w-full h-12 text-base font-normal border-2 border-gray-300 hover:bg-slate-50 bg-transparent rounded-md flex items-center justify-center transition-colors text-gray-700"
                onClick={() => handleOAuthSignIn("linkedin")}
              >
                <svg className="w-5 h-5 mr-3" fill="#0A66C2" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
                Continue with LinkedIn
              </button>
            </div>

            <div className="text-center text-sm text-gray-600 px-4 pt-2">
              By signing in, you agree to JobFlow's{" "}
              <a href="#" className="text-blue-600 hover:underline">
                User Agreement
              </a>
              ,{" "}
              <a href="#" className="text-blue-600 hover:underline">
                Privacy Policy
              </a>
              , and{" "}
              <a href="#" className="text-blue-600 hover:underline">
                Cookie Policy
              </a>
              .
            </div>
          </div>
        </div>
      </div>

      <div className="text-center pb-8 text-sm text-gray-600">
        New to JobFlow?{" "}
        <a href="/sign-up" className="text-blue-600 font-semibold hover:underline">
          Join now
        </a>
      </div>
    </div>
  );
}