import {z} from "zod"
import {  useQuery,  type UseQueryOptions, type UseQueryResult } from "@tanstack/react-query"
import type { ApiError } from "../../shared/types";
import type { AsyncState } from "./types";
import { Err,  None, Ok, Some, Option } from "oxide.ts";

export function buildValidationErrorMessage<T>(zodError: z.ZodError<T>): string {
    let errorMsg = ''
    const treeifiedError = z.treeifyError(zodError)
    for (const error of treeifiedError.errors) {
        errorMsg += `${error}\n`
    }
    return errorMsg
}

export function isEmpty(value: unknown): value is null | undefined | '' | Record<PropertyKey, never> | [] {
  // 1. Check for null or undefined
  if (value === null || value === undefined) {
    return true;
  }

  // 2. Check for strings and arrays
  if (typeof value === 'string' || Array.isArray(value)) {
    return value.length === 0;
  }

  // 3. Check for built-in collections (Map, Set)
  if (value instanceof Map || value instanceof Set) {
    return value.size === 0;
  }

  // 4. Check for plain objects
  if (typeof value === 'object') {
    // Exclude instances of Date, RegExp, etc.
    if (Object.prototype.toString.call(value) !== '[object Object]') {
      return false;
    }
    return Object.keys(value).length === 0;
  }

  return false;
}

export function toAsyncState<T>(query: UseQueryResult<T, ApiError>): AsyncState<T, ApiError> {
    if (query.isLoading) return {status: "loading", data: None}
    if (query.isError) return {status: "error", data: Some(Err(query.error))}
    if (query.data && isEmpty(query.data)) return {status: "empty", data: Some(Ok(query.data as []))}
    return {status: "success", data: Some(Ok(query.data as T))}
}

export function useTypedQuery<T>(
  options: UseQueryOptions<T, ApiError>
): AsyncState<T, ApiError> {
  const query = useQuery(options);

  switch (query.status) {
    case "pending":
      return { status: "idle", data: None };
      
    case "error":
      return { status: "error", data: Some(Err(query.error)) };
      
    case "success":
      return isEmpty(query.data)
        ? { status: "empty", data: Some(Ok([])) }
        : { status: "success", data: Some(Ok(query.data)) };
  }
}

export const toOption = <T>(val: T | undefined | null): Option<T> => 
  (val !== undefined && val !== null) ? Some(val) : None;