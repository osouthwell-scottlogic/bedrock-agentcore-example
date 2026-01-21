export interface HttpErrorDetails {
  [key: string]: unknown;
}

export class HttpError extends Error {
  status: number;
  errorCode?: string;
  requestId?: string;
  details?: HttpErrorDetails;
  headers?: Record<string, string>;

  constructor(params: {
    message: string;
    status: number;
    errorCode?: string;
    requestId?: string;
    details?: HttpErrorDetails;
    headers?: Record<string, string>;
  }) {
    super(params.message);
    this.name = 'HttpError';
    this.status = params.status;
    this.errorCode = params.errorCode;
    this.requestId = params.requestId;
    this.details = params.details;
    this.headers = params.headers;
  }
}

const headerVariants = ['x-amzn-requestid', 'x-request-id', 'x-amzn-request-id'];

const getRequestId = (headers: Headers): string | undefined => {
  for (const key of headerVariants) {
    const value = headers.get(key);
    if (value) return value;
  }
  return undefined;
};

const safeParseJson = async (response: Response): Promise<any | undefined> => {
  try {
    return await response.json();
  } catch {
    return undefined;
  }
};

export interface FetchJsonOptions {
  expectJson?: boolean;
  signal?: AbortSignal;
}

export interface FetchJsonResult<T> {
  data: T;
  requestId?: string;
  headers: Record<string, string>;
}

export const fetchJson = async <T = any>(
  input: RequestInfo | URL,
  init?: RequestInit,
  options?: FetchJsonOptions
): Promise<FetchJsonResult<T>> => {
  const response = await fetch(input, { ...init, signal: options?.signal });
  const headersObj = Object.fromEntries(response.headers.entries());
  const requestId = getRequestId(response.headers);

  const parsedBody = options?.expectJson === false ? undefined : await safeParseJson(response);

  if (!response.ok) {
    const errorCode = parsedBody?.errorCode || parsedBody?.code;
    const message = parsedBody?.message || parsedBody?.error || response.statusText || 'Request failed';
    const details = parsedBody?.details || parsedBody;
    throw new HttpError({
      message,
      status: response.status,
      errorCode,
      requestId,
      details,
      headers: headersObj,
    });
  }

  return {
    data: (parsedBody as T) ?? (undefined as T),
    requestId,
    headers: headersObj,
  };
};
