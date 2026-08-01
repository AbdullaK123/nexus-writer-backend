import { useEffect } from "react";


export function useShortcut(
    key: string,
    usesCtrlKey: boolean,
    useAltKey: boolean,
    handler: () => void
) {

    useEffect(() => {

        const handleShortcut = (e: KeyboardEvent) => {

            const shouldRunHandler = (e.key === key) && (!usesCtrlKey || e.ctrlKey) && (!useAltKey || e.altKey)
            
            if (shouldRunHandler) {
                handler()
            }
        }

        window.addEventListener('keydown', handleShortcut)

        return () => {
            window.removeEventListener('keydown', handleShortcut)
        }

    }, [handler, key, usesCtrlKey, useAltKey])

}