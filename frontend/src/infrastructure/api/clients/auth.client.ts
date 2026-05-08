import { ApiClient } from "./base.client"
import {
    type RegistrationData,
    type AuthCredentials,
    type UserResponse,
    UserResponseSchema,
    type ApiMessage,
    ApiMessageSchema,
    type RequestOptions,
    noRequestOptions,
} from "../types"
import type { Result, ApiError } from "../../../shared/types"

export class AuthClient {

    private readonly api: ApiClient
    constructor(api: ApiClient) {
        this.api = api
    }

    public register(
        payload: RegistrationData,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<UserResponse, ApiError>> {
        return this.api.postJson(
            "/auth/register",
            payload,
            UserResponseSchema,
            options,
        )
    }

    public login(
        payload: AuthCredentials,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<UserResponse, ApiError>> {
        return this.api.postJson(
            "/auth/login",
            payload,
            UserResponseSchema,
            options,
        )
    }

    public logout(
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ApiMessage, ApiError>> {
        return this.api.postJson(
            "/auth/logout",
            {},
            ApiMessageSchema,
            options,
        )
    }

    public getCurrentUser(
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<UserResponse, ApiError>> {
        return this.api.getJson(
            "/auth/me",
            UserResponseSchema,
            options,
        )
    }
}
