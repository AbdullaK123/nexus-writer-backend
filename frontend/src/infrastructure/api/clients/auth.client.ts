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
    DashboardResponseSchema,
    type DashboardResponse,
    type UserNavigationResponse,
    UserNavigationResponseSchema,
    type StoryNavigationResponse,
    StoryNavigationResponseSchema,
    type SettingsPayload
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
            "auth/register",
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
            "auth/login",
            payload,
            UserResponseSchema,
            options,
        )
    }

    public logout(
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ApiMessage, ApiError>> {
        return this.api.postJson(
            "auth/logout",
            {},
            ApiMessageSchema,
            options,
        )
    }

    public getCurrentUser(
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<UserResponse, ApiError>> {
        return this.api.getJson(
            "auth/me",
            UserResponseSchema,
            options,
        )
    }

    public getDashboard(
        options: RequestOptions = noRequestOptions
    ): Promise<Result<DashboardResponse, ApiError>> {
        return this.api.getJson(
            "auth/me/dashboard",
            DashboardResponseSchema,
            options
        )
    }

    public getEditorLinks(
        options: RequestOptions = noRequestOptions
    ): Promise<Result<UserNavigationResponse, ApiError>> {
        return this.api.getJson(
            "auth/me/links/editor",
            UserNavigationResponseSchema,
            options
        )
    }

    public getChatLinks(
        options: RequestOptions = noRequestOptions
    ): Promise<Result<StoryNavigationResponse, ApiError>> {
        return this.api.getJson(
            "auth/me/links/chat",
            StoryNavigationResponseSchema,
            options
        )
    }

    public updateSettings(
        payload: SettingsPayload,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<UserResponse, ApiError>> {
        return this.api.patchJson(
            'auth/me/settings',
            payload,
            UserResponseSchema,
            options
        )
    }
}
