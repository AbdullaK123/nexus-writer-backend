import { type ComponentPropsWithoutRef, type ReactNode } from "react"

type CardProps = ComponentPropsWithoutRef<"div"> & {
    title?: string 
    subtitle?: string
    header?: ReactNode
    footer?: ReactNode
    children: ReactNode
}

export function Card({ title, subtitle, header, footer, children, className, ...rest }: CardProps) {
    return (
        <div 
            className={`card ${className ? className : ""}`}
            {...rest}
        >
            {header && (
                <div className="card__header">
                    {header}
                </div>
            )}
            { title && (
                <div className="card__title">
                    {title}
                </div>
            )}
            { subtitle && (
                <div className="card__subtitle">
                    {subtitle}
                </div>
            )}
           { children }
           { footer && (
                <div className="card__footer">
                    {footer}
                </div>
           )}
        </div>
    )
}