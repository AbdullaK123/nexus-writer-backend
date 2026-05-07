import {z} from "zod"

export function buildValidationErrorMessage<T>(zodError: z.ZodError<T>): string {
    let errorMsg = ''
    const treeifiedError = z.treeifyError(zodError)
    for (const error of treeifiedError.errors) {
        errorMsg += `${error}\n`
    }
    return errorMsg
}