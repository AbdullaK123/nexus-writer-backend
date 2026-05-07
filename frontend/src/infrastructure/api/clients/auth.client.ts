import { ApiClient } from "./base.client"
import {
    type RegistrationData,
    type AuthCredentials,
    type UserResponse,
    UserResponseSchema,
    type ApiMessage,
    ApiMessageSchema,
    type RequestOptions,
} from "../types"
import { unwrapResult } from "../../../shared/types"

export class AuthClient {

    private readonly api = new ApiClient()

    public async register(
        payload: RegistrationData,
        options: RequestOptions = {},
    ): Promise<UserResponse> {
        const response = await this.api.postJson(
            "/auth/register",
            payload,
            UserResponseSchema,
            options,
        )
        return unwrapResult(response)
    }

    public async login(
        payload: AuthCredentials,
        options: RequestOptions = {},
    ): Promise<UserResponse> {
        const response = await this.api.postJson(
            "/auth/login",
            payload,
            UserResponseSchema,
            options,
        )
        return unwrapResult(response)
    }

    public async logout(
        options: RequestOptions = {},
    ): Promise<ApiMessage> {
        const response = await this.api.postJson(
            "/auth/logout",
            {},
            ApiMessageSchema,
            options,
        )
        return unwrapResult(response)
    }

    public async getCurrentUser(
        options: RequestOptions = {},
    ): Promise<UserResponse> {
        const response = await this.api.getJson(
            "/auth/me",
            UserResponseSchema,
            options,
        )
        return unwrapResult(response)
    }
}
