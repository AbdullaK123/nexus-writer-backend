import type { SseError } from ".";

export const isRetryable = (err: SseError): boolean => {
  if (err._tag === "SseNetworkError" || err._tag === "SseStreamError" || err._tag === "SseNoBodyError") return true;
  if (err._tag === "SseHttpError") return err.status >= 500 || err.status === 429;
  return false;
};

export const isTerminal = (err: SseError): boolean => {
  if (err._tag === "SseAbortedError") return true;
  if (err._tag === "SseHttpError") return err.status === 401 || err.status === 403 || err.status === 404;
  return false;
};