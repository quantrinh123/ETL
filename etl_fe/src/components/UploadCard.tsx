import React, { useState } from "react";
import { uploadCsv } from "../api";

interface Props {
  source: "online" | "offline";
  title: string;
  description: string;
}

const UploadCard: React.FC<Props> = ({ source, title, description }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMessage(null);
    setError(null);
    const f = e.target.files?.[0] ?? null;
    setFile(f);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Vui lòng chọn file CSV trước.");
      return;
    }
    setIsLoading(true);
    setMessage(null);
    setError(null);
    try {
      const res = await uploadCsv(source, file);
      setMessage(`Đã publish ${res.published} dòng lên hàng đợi.`);
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? "Không thể upload file.";
      setError(detail);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>{title}</h3>
      <p className="card-description">{description}</p>
      <div className="card-body">
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="file-input"
        />
        <button
          type="button"
          className="btn primary"
          onClick={handleUpload}
          disabled={isLoading}
        >
          {isLoading ? "Đang upload..." : "Upload & Publish"}
        </button>
      </div>
      {message && <p className="status success">{message}</p>}
      {error && <p className="status error">{error}</p>}
    </div>
  );
};

export default UploadCard;


