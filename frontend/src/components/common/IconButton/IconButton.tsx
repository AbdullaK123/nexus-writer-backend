import type { ReactNode } from "react";
import { Option } from "oxide.ts"
import styles from "./IconButton.module.css"

type IconButtonProps = {
    label: string 
    children: ReactNode
    variant: Option<"ghost" | "outline" | "solid">
    size: Option<"sm" | "md">
}

const getStyles = (
    variant?: "ghost" | "outline" | "solid",
    size?: "sm" | "md"
): string => {
    let extraStyles = ""
    if (variant) {
        switch (variant) {
            case "ghost":
                extraStyles += styles['icon-btn__ghost']
                break
            case "outline":
                extraStyles += styles['icon-btn__outline']
                break
            case "solid":
                extraStyles += styles['icon-btn__solid']
                break
        }
    }
    if (size) {
        switch (size) {
            case "sm":
                extraStyles += ` ${styles['icon-btn__sm']}`
                break
            case "md":
                extraStyles += ` ${styles['icon-btn__md']}`
                break
        }
    }
    return extraStyles
}


export function IconButton({
    label,
    children,
    variant,
    size
}: IconButtonProps) {
    return (
        <button 
            className={`${styles["icon-btn"]} ${getStyles(variant.isSome() ? variant.unwrap() : "ghost", size.isSome() ? size.unwrap() : "md")}`} 
            aria-label={label}
        >
            {children}
        </button>
    )
}