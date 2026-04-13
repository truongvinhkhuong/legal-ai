"use client";

import { useRouter } from "next/navigation";
import type { FormStep } from "@/lib/types";
import { useContractForm } from "@/hooks/use-contract-form";
import { ComplianceBadge } from "./compliance-badge";

function StepIndicator({
  steps,
  current,
  onGoTo,
}: {
  steps: FormStep[];
  current: number;
  onGoTo: (n: number) => void;
}) {
  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-2">
      {steps.map((step, i) => {
        const isActive = i === current;
        const isDone = i < current;
        return (
          <button
            key={step.step_number}
            onClick={() => onGoTo(i)}
            className={`flex-shrink-0 flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors ${
              isActive
                ? "bg-brand-500 text-white"
                : isDone
                  ? "bg-brand-100 text-brand-700"
                  : "bg-gray-100 text-gray-500"
            }`}
          >
            <span className="font-semibold">{i + 1}</span>
            <span className="hidden sm:inline">{step.title_vi}</span>
          </button>
        );
      })}
    </div>
  );
}

function FieldInput({
  field,
  value,
  onChange,
}: {
  field: FormStep["fields"][number];
  value: unknown;
  onChange: (val: unknown) => void;
}) {
  const strVal = value != null ? String(value) : "";

  const baseClass =
    "w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500";

  if (field.field_type === "textarea") {
    return (
      <textarea
        className={baseClass}
        rows={3}
        placeholder={field.placeholder_vi}
        value={strVal}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }

  if (field.field_type === "select" && field.options) {
    return (
      <select
        className={baseClass}
        value={strVal}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">-- Chon --</option>
        {field.options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    );
  }

  return (
    <input
      type={field.field_type === "number" ? "number" : field.field_type === "date" ? "date" : "text"}
      className={baseClass}
      placeholder={field.placeholder_vi}
      value={strVal}
      onChange={(e) => {
        if (field.field_type === "number") {
          const n = e.target.value === "" ? "" : Number(e.target.value);
          onChange(n);
        } else {
          onChange(e.target.value);
        }
      }}
    />
  );
}

function SummaryStep({
  steps,
  values,
  onGoTo,
}: {
  steps: FormStep[];
  values: Record<string, unknown>;
  onGoTo: (n: number) => void;
}) {
  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-sm text-gray-900">
        Xac nhan thong tin
      </h3>
      {steps
        .filter((s) => s.fields.length > 0)
        .map((step, i) => (
          <div
            key={step.step_number}
            className="border border-gray-200 rounded-lg p-3"
          >
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-semibold text-gray-700">
                {step.title_vi}
              </span>
              <button
                onClick={() => onGoTo(i)}
                className="text-xs text-brand-600 hover:underline"
              >
                Sua
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1">
              {step.fields.map((f) => {
                const v = values[f.field_key];
                const display = v != null && v !== "" ? String(v) : "—";
                return (
                  <div key={f.field_key} className="text-xs">
                    <span className="text-gray-500">{f.label_vi}: </span>
                    <span className="text-gray-900">{display}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
    </div>
  );
}

export function FormWizard({
  templateKey,
  templateName,
  steps,
}: {
  templateKey: string;
  templateName: string;
  steps: FormStep[];
}) {
  const router = useRouter();
  const {
    currentStep,
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
  } = useContractForm({ templateKey, steps });

  const step = steps[currentStep];

  const handleSubmit = async () => {
    const result = await submit();
    if (result) {
      router.push(`/contracts/${result.contract_id}`);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-base font-bold text-gray-900 mb-3">
        {templateName}
      </h2>

      <StepIndicator steps={steps} current={currentStep} onGoTo={goToStep} />

      <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4">
        {step.fields.length > 0 ? (
          <div className="space-y-4">
            <h3 className="font-semibold text-sm text-gray-700">
              {step.title_vi}
            </h3>
            {step.fields.map((field) => (
              <div key={field.field_key}>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  {field.label_vi}
                  {field.required && (
                    <span className="text-red-500 ml-0.5">*</span>
                  )}
                </label>
                <FieldInput
                  field={field}
                  value={values[field.field_key]}
                  onChange={(val) => setField(field.field_key, val)}
                />
                {field.help_text_vi && (
                  <p className="text-[10px] text-gray-400 mt-0.5">
                    {field.help_text_vi}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <SummaryStep steps={steps} values={values} onGoTo={goToStep} />
        )}

        {/* Compliance results */}
        {compliance && compliance.issues.length > 0 && (
          <div className="mt-4 pt-3 border-t border-gray-100">
            <ComplianceBadge compliance={compliance} />
          </div>
        )}

        {error && (
          <p className="mt-3 text-xs text-red-600">{error}</p>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-4">
        <button
          onClick={prevStep}
          disabled={isFirstStep}
          className="px-4 py-2 text-sm rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Quay lai
        </button>

        {isLastStep ? (
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="px-5 py-2 text-sm rounded-md bg-brand-500 text-white hover:bg-brand-600 disabled:opacity-60"
          >
            {isSubmitting ? "Dang tao..." : "Tao hop dong"}
          </button>
        ) : (
          <button
            onClick={nextStep}
            className="px-4 py-2 text-sm rounded-md bg-brand-500 text-white hover:bg-brand-600"
          >
            Tiep theo
          </button>
        )}
      </div>
    </div>
  );
}
