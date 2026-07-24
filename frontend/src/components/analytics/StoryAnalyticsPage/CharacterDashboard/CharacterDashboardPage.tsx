import { CharacterDashboard } from "./CharacterDashboard";
import { useCharacterDashboardPageProps } from "./useCharacterDashboardProps";


export function CharacterDashboardPage() {
    const props = useCharacterDashboardPageProps()
    return <CharacterDashboard {...props} />
}