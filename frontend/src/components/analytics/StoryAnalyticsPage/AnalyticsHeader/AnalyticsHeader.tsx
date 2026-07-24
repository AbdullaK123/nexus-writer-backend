import { None } from "oxide.ts";
import { LoadingSkeleton, Nothing } from "../../../common";
import { FilterChipNoCounts } from "../../../story/DashboardPage/LibraryGrid/FilterChip/FilterChip";


export type AnalyticsHeaderProps = 
| { status: "loading"}
| { status: "idle" }
| { status: "empty"}
| { status: "error", onRetry: () => void }
| {
    status: "ready"
    selectedLense: "character" | "plot" | "structure" | "world"
    storyTitle: string
    onClickCharacter: () => void
    onClickPlot: () => void
    onClickStructure: () => void
    onClickWorld: () => void
  }

export function AnalyticsHeader(props: AnalyticsHeaderProps) {
    switch (props.status) {
        case "loading": {
            return (
                <div>
                    <div>
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                    </div>
                    <div>
                        <div>
                            <LoadingSkeleton className={None} />
                            <LoadingSkeleton className={None} />
                        </div>
                        <div>
                            <LoadingSkeleton className={None} />
                            <LoadingSkeleton className={None} />
                            <LoadingSkeleton className={None} />
                            <LoadingSkeleton className={None} />
                        </div>
                    </div>
                </div>
            )
        }
        case "error":
        case "empty":
        case "idle": {
            return <Nothing />
        }
        case "ready": {
            <div>
                <div>
                    <span>
                        {`[BOOK PULSE - ${props.storyTitle}]`}
                    </span>
                </div>
                <div>
                    <div>
                        <h2>Analytics</h2>
                        <p>Four lenses on your book. Each one is opnionated.</p>
                    </div>
                    <div>
                        <FilterChipNoCounts 
                            label="Character"
                            status={(props.selectedLense === "character") ? "selected" : "idle"}
                            onClick={props.onClickCharacter}
                        />
                        <FilterChipNoCounts 
                            label="Plot"
                            status={(props.selectedLense === "plot") ? "selected" : "idle"}
                            onClick={props.onClickPlot}
                        />
                        <FilterChipNoCounts 
                            label="Structure"
                            status={(props.selectedLense === "structure") ? "selected" : "idle"}
                            onClick={props.onClickStructure}
                        />
                        <FilterChipNoCounts 
                            label="World"
                            status={(props.selectedLense === "world") ? "selected" : "idle"}
                            onClick={props.onClickWorld}
                        />
                    </div>
                </div>
            </div>
        }
    }
}