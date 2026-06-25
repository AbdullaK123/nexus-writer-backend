import { type ComponentPropsWithoutRef, type ReactNode } from "react"
import { Option } from "oxide.ts"

type CardProps = ComponentPropsWithoutRef<"div"> & {
    cardTitle: Option<string> 
    subtitle: Option<string>
    header: Option<ReactNode>
    footer: Option<ReactNode>
    children: ReactNode
}

export function Card({ cardTitle, subtitle, header, footer, children, className, ...rest }: CardProps) {
    return (
        <div 
            className={`card ${className ? className : ""}`}
            {...rest}
        >
            {header.isSome() && (
                <div className="card__header">
                    {header.unwrap()}
                </div>
            )}
            { cardTitle.isSome() && (
                <div className="card__title">
                    {cardTitle.unwrap()}
                </div>
            )}
            { subtitle.isSome() && (
                <div className="card__subtitle">
                    {subtitle.unwrap()}
                </div>
            )}
           { children }
           { footer.isSome() && (
                <div className="card__footer">
                    {footer.unwrap()}
                </div>
           )}
        </div>
    )
}