import { Switch as ArcSwitch} from "@ark-ui/react/switch"
import styles from "./Switch.module.css"


export type SwitchProps = {
    checked: boolean
    onCheckedChanged: (e: boolean) => void
    label: string
}


export default function Switch({
    checked,
    onCheckedChanged,
    label
}: SwitchProps) {
    return (
        <ArcSwitch.Root 
            checked={checked}
            onCheckedChange={(e) => onCheckedChanged(e.checked)}
            className={styles['root']}
        >
            <ArcSwitch.Control className={styles['control']}>
                <ArcSwitch.Thumb className={styles['thumb']} />
            </ArcSwitch.Control>
            <ArcSwitch.Label className={styles['label']}>
                {label}
            </ArcSwitch.Label>
            <ArcSwitch.HiddenInput />
        </ArcSwitch.Root>
    )
}