"use client";

import { useCallback, useRef, useState } from "react";
import type { ComplianceResult, FormStep } from "@/lib/types";
import { createContract, validateContract } from "@/lib/api-client";

interface UseContractFormOptions {
  templateKey: string;
  steps: FormStep[];
}

export function useContractForm({ templateKey, steps }: UseContractFormOptions) {
  const [currentStep, setCurrentStep] = useState(0);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [compliance, setCompliance] = useState<ComplianceResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const totalSteps = steps.length;
  const isLastStep = currentStep === totalSteps - 1;
  const isFirstStep = currentStep === 0;

  const setField = useCallback((key: string, value: unknown) => {
    setValues((prev) => ({ ...prev, [key]: value }));
  }, []);

  const runValidation = useCallback(async () => {
    setIsValidating(true);
    try {
      const region = (values.region as string) || "vung_1";
      const result = await validateContract(templateKey, values, region);
      setCompliance(result);
    } catch {
      // Validation failure is non-blocking
    } finally {
      setIsValidating(false);
    }
  }, [templateKey, values]);

  const debouncedValidate = useCallback(() => {
    if (validateTimer.current) clearTimeout(validateTimer.current);
    validateTimer.current = setTimeout(runValidation, 600);
  }, [runValidation]);

  const nextStep = useCallback(() => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep((s) => s + 1);
      debouncedValidate();
    }
  }, [currentStep, totalSteps, debouncedValidate]);

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((s) => s - 1);
    }
  }, [currentStep]);

  const goToStep = useCallback((step: number) => {
    if (step >= 0 && step < totalSteps) {
      setCurrentStep(step);
    }
  }, [totalSteps]);

  const submit = useCallback(async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const region = (values.region as string) || "vung_1";
      const result = await createContract(templateKey, values, region);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Loi khi tao hop dong");
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }, [templateKey, values]);

  return {
    currentStep,
    totalSteps,
    isFirstStep,
    isLastStep,
    values,
    compliance,
    isValidating,
    isSubmitting,
    error,
    setField,
    nextStep,
    prevStep,
    goToStep,
    submit,
    runValidation,
  };
}
