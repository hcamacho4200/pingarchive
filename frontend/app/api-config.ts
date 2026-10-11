const DEVELOPMENT_API_BASE_URL = "http://127.0.0.1:8002/api/v1";
const PRODUCTION_API_BASE_URL = "/api/v1";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "development"
    ? DEVELOPMENT_API_BASE_URL
    : PRODUCTION_API_BASE_URL);
