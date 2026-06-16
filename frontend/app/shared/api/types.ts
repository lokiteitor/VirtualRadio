// Backend response contract: { data, meta } on success, { error } on failure.

export interface Meta {
  [key: string]: unknown;
}

export interface Envelope<T> {
  data: T;
  meta: Meta;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(code: string, message: string, status: number, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

/** Normalize any thrown fetch error into an ApiError using the {error} envelope. */
export function toApiError(err: unknown): ApiError {
  const anyErr = err as { data?: ApiErrorBody; statusCode?: number; status?: number; message?: string };
  const body = anyErr?.data;
  const status = anyErr?.statusCode ?? anyErr?.status ?? 0;
  if (body && body.error) {
    return new ApiError(body.error.code, body.error.message, status, body.error.details ?? {});
  }
  return new ApiError("NETWORK_ERROR", anyErr?.message ?? "Error de conexión", status);
}
