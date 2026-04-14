"use client";

import { useRef, useState } from "react";
import { ingestDocument } from "@/lib/api-client";

interface Props {
  onSuccess?: () => void;
}

export function DocumentUpload({ onSuccess }: Props) {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;

    setUploading(true);
    setResult(null);

    try {
      const response = await ingestDocument(file, {});
      if (response.success) {
        setResult(
          `Thành công: ${response.chunks_created} chunks, ${response.articles_found} điều`
        );
        onSuccess?.();
      } else {
        setResult(`Thất bại: ${response.warnings.join(", ")}`);
      }
    } catch (err) {
      setResult("Lỗi upload. Kiểm tra server.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.docx,.html,.htm,.txt"
        className="text-sm text-gray-500 file:mr-2 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
      />
      <button
        onClick={handleUpload}
        disabled={uploading}
        className="px-3 py-1.5 bg-brand-600 text-white text-sm rounded hover:bg-brand-700 disabled:opacity-50"
      >
        {uploading ? "Đang xử lý..." : "Upload"}
      </button>
      {result && (
        <span className="text-xs text-gray-500">{result}</span>
      )}
    </div>
  );
}
