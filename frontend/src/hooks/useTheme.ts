import { useEffect } from "react";

export type ThemePreference = "system" | "light" | "dark"
export type ResolvedTheme = "light" | "dark"

export function useTheme(preference: ThemePreference) {
    useEffect(() => {
        const media = window.matchMedia(
            "(prefers-color-scheme: dark)"
        )

        const applyTheme = () => {
            const theme: ResolvedTheme =
                preference === "system"
                    ? media.matches
                        ? "dark"
                        : "light"
                    : preference

            document.documentElement.dataset.theme = theme
        }

        applyTheme()

        if (preference !== "system") {
            return
        }

        media.addEventListener("change", applyTheme)

        return () => {
            media.removeEventListener("change", applyTheme)
        }
    }, [preference])
}