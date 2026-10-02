"use client";

import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useState, type FormEvent } from "react";

import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/context/auth-context";
import { getApiErrorMessage } from "@/lib/api-error";
import { isValidEmail } from "@/lib/email";

const PASSWORD_MIN = 8;
const PASSWORD_MAX = 128;

export function RegisterForm() {
  const { register } = useAuth();
  const router = useRouter();
  const consentId = useId();
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [consented, setConsented] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [companyError, setCompanyError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [consentError, setConsentError] = useState("");
  const [formError, setFormError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedCompany = companyName.trim();
    const trimmedEmail = email.trim();
    let valid = true;
    setFormError("");

    if (!trimmedCompany) {
      setCompanyError("Company name is required");
      valid = false;
    } else {
      setCompanyError("");
    }

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
    } else if (password.length < PASSWORD_MIN || password.length > PASSWORD_MAX) {
      setPasswordError(`Password must be ${PASSWORD_MIN}–${PASSWORD_MAX} characters`);
      valid = false;
    } else {
      setPasswordError("");
    }

    if (!consented) {
      setConsentError("You must agree to continue");
      valid = false;
    } else {
      setConsentError("");
    }

    if (!valid) {
      return;
    }

    setPending(true);
    try {
      await register({
        company_name: trimmedCompany,
        email: trimmedEmail,
        password,
      });
      router.replace("/jobs");
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        setEmailError(getApiErrorMessage(error, "Email already registered"));
      } else {
        setFormError(getApiErrorMessage(error));
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <div className="mb-space-lg">
        <h1 className="text-headline-md font-semibold tracking-tight text-on-surface">
          Create your Top Match account
        </h1>
        <p className="mt-1 text-body-md text-on-surface-variant">
          Screen high-volume applications without the ATS bloat.
        </p>
      </div>
      {formError ? (
        <div className="mb-space-md">
          <AuthErrorBanner message={formError} />
        </div>
      ) : null}
      <form className="space-y-space-md" noValidate onSubmit={onSubmit}>
        <Input
          autoComplete="organization"
          error={companyError}
          helper="One company workspace per enterprise deployment."
          id="company-name"
          label="Company name"
          onChange={(event) => setCompanyName(event.target.value)}
          placeholder="Acme Technologies"
          required
          type="text"
          value={companyName}
        />
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
          autoComplete="new-password"
          error={passwordError}
          helper="8–128 characters"
          id="password"
          label="Password"
          maxLength={PASSWORD_MAX}
          onChange={(event) => setPassword(event.target.value)}
          required
          trailing={
            <button
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="text-outline transition-colors hover:text-on-surface"
              onClick={() => setShowPassword((visible) => !visible)}
              type="button"
            >
              <Icon name={showPassword ? "visibility_off" : "visibility"} className="text-[18px]" />
            </button>
          }
          type={showPassword ? "text" : "password"}
          value={password}
        />
        <div className="pt-1">
          <label className="flex cursor-pointer items-start gap-space-sm select-none" htmlFor={consentId}>
            <input
              checked={consented}
              className="mt-1 size-4 rounded border-outline-variant accent-primary-container"
              id={consentId}
              onChange={(event) => setConsented(event.target.checked)}
              type="checkbox"
            />
            <span className="text-body-sm leading-tight text-on-surface">
              I agree to the{" "}
              <span className="font-medium text-secondary">Enterprise Service Agreement</span> and{" "}
              <span className="font-medium text-secondary">Acceptable AI Use Policy</span>.
            </span>
          </label>
          {consentError ? <p className="mt-1 text-body-sm text-error">{consentError}</p> : null}
        </div>
        <div className="pt-2">
          <Button className="w-full font-semibold" pending={pending} type="submit">
            Create Account
            <Icon name="arrow_forward" className="text-[18px]" />
          </Button>
        </div>
      </form>
      <div className="mt-space-lg border-t border-outline-variant pt-space-md text-center">
        <p className="text-body-md text-on-surface-variant">
          Already have an account?{" "}
          <Link className="font-semibold text-secondary hover:underline" href="/login">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
