import { Button } from "../../../../common";
import styles from "./CharacterSuggestionCard.module.css"

export type CharacterSuggestionCardProps = 
{
    status: "healthy" | "worth-watching" | "needs-your-attention" | "not-available",
    headline: string
    analysis: string
    onAskNexus: () => void
}

const getStyles = (status: "healthy" | "worth-watching" | "needs-your-attention" | "not-available") => {
    switch (status) {
        case "healthy": 
            return styles['status__healthy']
        case "worth-watching": 
            return styles['status__worth-watching']
        case "needs-your-attention": 
            return styles['status__needs-your-attention']
        case "not-available": 
            return styles['status__not-available']
    }
}

const getText = (status: "healthy" | "worth-watching" | "needs-your-attention" | "not-available") => {
    switch (status) {
        case "healthy": 
            return "Healthy"
        case "worth-watching": 
            return "Worth watching"
        case "needs-your-attention": 
            return "Needs your attention"
        case "not-available": 
            return "Not available"
    }
}


export function CharacterSuggestionCard(props: CharacterSuggestionCardProps) {
    return (
        <div>
            <div>
                <span className={getStyles(props.status)}>
                    {getText(props.status)}
                </span>
                <h3>{props.headline}</h3>
                <p>{props.analysis}</p>
            </div>
            <Button
                variant="ghost"
                onClick={props.onAskNexus}
            >
                → Ask Nexus
            </Button>
        </div>
    )
}