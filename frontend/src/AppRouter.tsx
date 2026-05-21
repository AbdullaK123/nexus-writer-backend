import { RouterProvider } from "@tanstack/react-router";
import { useAuthOrThrow } from "./data/providers";
import { router } from "./router"
import { useEffect } from "react";


export function AppRouter() {
    const auth = useAuthOrThrow()
    useEffect(() => {
        router.invalidate()
    }, [auth.status])
    return <RouterProvider router={router} context = {{ auth }} />
}