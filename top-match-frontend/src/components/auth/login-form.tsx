"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/context/auth-context";
import { getApiErrorMessage } from "@/lib/api-error";
import { isValidEmail } from "@/lib/email";

export function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [formError, setFormError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedEmail = email.trim();
    let valid = true;
    setFormError("");

    if (!trimmedEmail) {
      setEmailError("Work email is required");
      valid = false;
    } else if (!isValidEmail(trimmedEmail)) {
      setEmailError("Enter a valid email");
      valid = false;
    } else {
      setEmailError("");
    }

    if (!password) {
      setPasswordError("Password is required");
      valid = false;
    } else {
      setPasswordError("");
    }

    if (!valid) {
      return;
    }

    setPending(true);
    try {
      await login({ email: trimmedEmail, password });
      router.replace("/jobs");
    } catch (error) {
      setFormError(getApiErrorMessage(error, "Invalid email or password"));
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <div className="mb-space-md">
        <h1 className="text-headline-md font-semibold tracking-tight text-on-surface">Welcome back</h1>
        <p className="mt-1 text-body-md text-on-surface-variant">
          Sign in to access your company screening pipelines.
        </p>
      </div>
      {formError ? (
        <div className="mb-space-md">
          <AuthErrorBanner message={formError} />
        </div>
      ) : null}
      <form className="space-y-space-md" noValidate onSubmit={onSubmit}>
        <Input
          autoComplete="email"
          error={emailError}
          id="work-email"
          label="Work email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="recruiter@acme.com"
          required
          type="email"
          value={email}
        />
        <Input
          autoComplete="current-password"
          error={passwordError}
          id="password"
          label="Password"
          onChange={(event) => setPassword(event.target.value)}
          required
          trailing={
            <button
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="text-on-surface-variant transition-colors hover:text-on-surface"
              onClick={() => setShowPassword((visible) => !visible)}
              type="button"
            >
              <Icon name={showPassword ? "visibility_off" : "visibility"} className="text-xl" />
            </button>
          }
          type={showPassword ? "text" : "password"}
          value={password}
        />
        <div className="pt-1">
          <Button className="h-11 w-full font-semibold" pending={pending} type="submit">
            Log in
            <Icon name="arrow_forward" className="text-lg" />
          </Button>
        </div>
      </form>
      <div className="mt-space-md border-t border-outline-variant pt-space-md text-center">
        <p className="text-body-sm text-on-surface-variant">
          Need an account?{" "}
          <Link className="text-label-md font-semibold text-secondary hover:underline" href="/register">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
