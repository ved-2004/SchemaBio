/**
 * Runtime API configuration.
 *
 * In development (npm run dev):  uses http://localhost:8000 via .env.development
 * In production (npm run build): uses the Render backend URL via .env.production
 *
 * All /api calls must be prefixed with API_BASE_URL instead of a bare "/api".
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
