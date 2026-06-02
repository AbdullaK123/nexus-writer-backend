import styles from "./SideRail.module.css"


export type SideRailProps = {
    onClickHome: () => void
    onClickEdit: () => void 
    onClickChat: () => void 
    onClickStat: () => void
    onClickSet: () => void
}


export function SideRail({
    onClickHome,
    onClickEdit,
    onClickChat,
    onClickStat,
    onClickSet
}: SideRailProps) {
    return (
        <nav className={styles['siderail-container']}>
            <span className={styles['siderail-item']}>NX</span>
            <button 
                className={styles['siderail-item']}
                onClick={onClickHome}
            >
                HOME
            </button>
            <button 
                className={styles['siderail-item']}
                onClick={onClickEdit}
            >
                EDIT
            </button>
            <button 
                className={styles['siderail-item']}
                onClick={onClickChat}
            >
                CHAT
            </button>
            <button 
                className={styles['siderail-item']}
                onClick={onClickStat}
            >
                STAT
            </button>
            <button 
                className={styles['siderail-item']}
                onClick={onClickSet}
            >
                SET
            </button>
        </nav>
    )
}