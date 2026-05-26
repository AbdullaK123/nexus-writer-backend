import { toaster } from "./toaster"


export function useToast(duration: number = 3000) {
    return {
        info: ( title: string, message: string ) => toaster.info({ title: title, description: message, duration: duration }),
        warning: ( title: string, message: string )=> toaster.warning({ title: title, description: message, duration: duration }),
        error: ( title: string, message: string )=> toaster.error({ title: title, description: message, duration: duration }),
        success: ( title: string, message: string )=> toaster.success({ title: title, description: message, duration: duration })
    }
}