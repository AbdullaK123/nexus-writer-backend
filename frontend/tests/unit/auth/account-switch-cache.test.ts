import { beforeEach, describe, expect, test, vi } from "vitest"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import { useApi } from "../../../src/data/providers/ApiProvider"
import {
    authKeys,
    useLogin,
    useRegister,
} from "../../../src/data/queries/auth"

vi.mock("@tanstack/react-query", () => ({
    useQuery: vi.fn(),
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
}))

vi.mock("../../../src/data/providers/ApiProvider", () => ({
    useApi: vi.fn(),
}))

const clear = vi.fn()
const setQueryData = vi.fn()

function mutationOptions() {
    return vi.mocked(useMutation).mock.calls.at(-1)?.[0] as {
        onSuccess?: (user: unknown) => unknown
    }
}

beforeEach(() => {
    clear.mockReset()
    setQueryData.mockReset()
    vi.mocked(useMutation).mockReset()

    vi.mocked(useQueryClient).mockReturnValue({ clear, setQueryData } as never)
    vi.mocked(useApi).mockReturnValue({
        auth: {
            login: vi.fn(),
            register: vi.fn(),
        },
    } as never)
})

describe("account switch cache isolation", () => {
    test("successful login purges every cache entry from a previous account", () => {
        const newUser = { id: "user-b", username: "user-b" }

        useLogin()
        mutationOptions().onSuccess?.(newUser)

        expect(clear).toHaveBeenCalledOnce()
        expect(clear.mock.invocationCallOrder[0]).toBeLessThan(
            setQueryData.mock.invocationCallOrder[0],
        )
        expect(setQueryData).toHaveBeenCalledWith(authKeys.me(), newUser)
    })

    test("successful registration cannot inherit private cache from a prior session", () => {
        const newUser = { id: "new-user", username: "new-user" }

        useRegister()
        mutationOptions().onSuccess?.(newUser)

        expect(clear).toHaveBeenCalledOnce()
        expect(clear.mock.invocationCallOrder[0]).toBeLessThan(
            setQueryData.mock.invocationCallOrder[0],
        )
        expect(setQueryData).toHaveBeenCalledWith(authKeys.me(), newUser)
    })
})
