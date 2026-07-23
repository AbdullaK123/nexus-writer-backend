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
    if (query.isPending) return {status: "idle", data: None}
    if (query.isError) return {status: "error", data: Some(Err(query.error))}
    if (query.data && isEmpty(query.data)) return {status: "empty", data: Some(Ok(query.data as []))}
    return {status: "success", data: Some(Ok(query.data as T))}
}

export function useTypedQuery<T>(
  options: UseQueryOptions<T, ApiError>
): AsyncState<T, ApiError> {
  const query = useQuery<T, ApiError>(options);

  switch (query.status) {
    case "pending":
      return query.isLoading ? 
              { status: "loading", data: None} 
            : { status: "idle", data: None };
      
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


export type ResolvedAsyncState<T, E> = 
  | { status: "idle"}
  | { status: "loading" }
  | { status: "error", errors: E[] }
  | { status: "empty"}
  | { status: "success", data: T }

export function resolveAsyncStates<T extends Record<string, unknown>, E>(
  states: {
    [K in keyof T]: AsyncState<T[K], E>
  }
): ResolvedAsyncState<T, E> {

  const errors: E[] = []
  const data = {} as Partial<T>
  let hasEmpty = false
  let hasIdle = false

  for (const key in states) {
    const state = states[key]

    switch (state.status) {
      case "idle":
        hasIdle=true
        break;
      case "loading":
        return { status: "loading" }
      case "empty":
        hasEmpty = true
        break;
      case "error":
        errors.push(state.data.unwrap().unwrapErr())
        break;
      case "success":
        data[key] = state.data.unwrap().unwrap()
        break;
    }
  }

  if (errors.length > 0) {
    return { status: "error", errors: errors}
  }

  if (hasEmpty) {
    return { status: "empty" }
  }

  if (hasIdle) {
    return { status: "idle"}
  }

  return {
    status: "success",
    data: data as T
  }

}