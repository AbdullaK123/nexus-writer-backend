import type { ComponentPropsWithoutRef } from "react"

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger"

type ButtonProps = Omit<ComponentPropsWithoutRef<"button">, "variant"> & {
    variant: ButtonVariant
} 

export function Button({ variant, className, ...rest}: ButtonProps) {
    return (
        <button
            className={`btn btn--${variant} ${className}`}
            {...rest}
        />
    )
}