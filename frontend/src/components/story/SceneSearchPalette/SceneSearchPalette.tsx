import { SceneSearchPaletteFooter, SceneSearchPaletteHeader, SceneSearchResultList, type SceneSearchPaletteFooterProps, type SceneSearchPaletteHeaderProps, type SceneSearchResultListProps } from "./components";
import { TriggerlessModal, type FocusGetter } from "../../common";
import styles from "./SceneSearchPalette.module.css"
import { None, Option, Some } from "oxide.ts";
import { useEffect, useId, useState } from "react";
import { paletteBus } from "./eventbus";


export type SceneSearchPaletteProps =
{
    query: string
    onQueryChange: (query: string) => void
    content: SceneSearchPaletteContentProps
}

type SceneSearchPaletteModalProps =
 {
    open: boolean
    onOpenChange: (open: boolean) => void
    content: SceneSearchPaletteContentProps
    initialFocusEl: Option<FocusGetter>
    finalFocusEl: Option<FocusGetter>
    modalInputId: string
 }

type SceneSearchPaletteContentProps = 
{
    header: Omit<SceneSearchPaletteHeaderProps, "modalInputId">
    list: SceneSearchResultListProps
    footer: SceneSearchPaletteFooterProps
}

type SceneSearchPaletteContentInternalProps =
    SceneSearchPaletteContentProps & {
        modalInputId: string
    }

function SceneSearchPaletteContent (props: SceneSearchPaletteContentInternalProps) {
     return (
        <div className={styles['palette-container']}>
            <SceneSearchPaletteHeader 
                {...props.header}
                modalInputId={props.modalInputId}
            />
            <SceneSearchResultList {...props.list} />
            <SceneSearchPaletteFooter 
                {...props.footer}
            />
        </div>
    )
}


function SceneSearchPaletteModal(props: SceneSearchPaletteModalProps) {
    return (
        <TriggerlessModal
            closeTrigger={None}
            title={None}
            description={None}
            open={props.open}
            onOpenChange={props.onOpenChange}
            content={
                <SceneSearchPaletteContent  
                    {...props.content}
                    modalInputId={props.modalInputId}
                />
            }
            initialFocusEl={props.initialFocusEl}
            finalFocusEl={props.finalFocusEl}
        />
    )
}



function getElementById(id: string): () => HTMLElement | null {
    return () => {
        if (typeof document === "undefined") {
            return null
        }

        return document.getElementById(id)
    }
}



export function SceneSearchPalette(props: SceneSearchPaletteProps) {

    const launcherInputId = useId()
    const modalInputId = useId()
    const [open, setOpen] = useState(false)
    const initialFocusEl = Some(getElementById(modalInputId))
    const finalFocusEl = Some(getElementById(launcherInputId))

     useEffect(() => {
        const handleBusClose = () => {
            setOpen(false);
        };

        paletteBus.addEventListener('close', handleBusClose);
        return () => {
            paletteBus.removeEventListener('close', handleBusClose);
        };
    }, []);

    return (
        <>
            <input 
                id={launcherInputId}
                type="text"
                className={`field__input ${styles['full-height']}`}
                placeholder="Search any moment..."
                value={props.query}
                onChange={(e) => {
                    const nextQuery = e.currentTarget.value
                    props.onQueryChange(nextQuery)
                    if (nextQuery.length > 0) {
                        setOpen(true)
                    }
                }}
            />
            <SceneSearchPaletteModal 
                content={props.content}
                open={open}
                onOpenChange={setOpen}
                initialFocusEl={initialFocusEl}
                finalFocusEl={finalFocusEl}
                modalInputId={modalInputId}
            />
       </>
    )
    
}