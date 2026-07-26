import type { ComponentPropsWithoutRef } from "react"

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "disabled"

type ButtonProps = Omit<ComponentPropsWithoutRef<"button">, "variant"> & {
    variant: ButtonVariant
} 

export function Button({ variant, className, disabled = false, ...rest}: ButtonProps) {
    const resolvedVariant = disabled ? "disabled" : variant

    return (
        <button
            className={["btn", `btn--${resolvedVariant}`, className].filter(Boolean).join(" ")}
            disabled={disabled}
            {...rest}
        />
    )
}