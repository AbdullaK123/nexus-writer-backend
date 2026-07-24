import { useMemo, useState } from "react";
import type { CharacterStatisticsRow } from "../../../../../infrastructure/api/types/analytics";
import { Select } from "../../../../common";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";


export type CharacterAppearanceDensityChartProps = 
{
    data: CharacterStatisticsRow[]
}

export function CharacterAppearanceDensityChart(props: CharacterAppearanceDensityChartProps) {

    const povs = useMemo(() => {
        const povs = props.data.map((row) => row.pov)
        return [...new Set(povs)]
    }, [props.data])

    const [activeCharacter, setActiveCharacter] = useState(povs[0])

    const filteredData = useMemo(() => {
        return props.data.filter((row) => row.pov === activeCharacter)
    }, [activeCharacter, props.data])

    const [activeMetric, setActiveMetric] = useState<"scene_count"| "word_count">("scene_count")

    const getMetricText = (metric: "scene_count" | "word_count") => {
        switch (metric) {
            case "scene_count": return "scene count"
            case "word_count": return "word count"
        }
    }

    return (
        <div>
            <div>
                <div>
                    <span>
                        {`[${activeCharacter} - ${getMetricText(activeMetric)} by chapter]`}
                    </span>
                    <p>Density across all chapters</p>
                </div>
                <div>
                    <Select 
                        label="Metric"
                        onChange={(e) => setActiveMetric(e.target.value as "scene_count" | "word_count")}
                        options={[
                            {label: "Number of scenes", value: "scene_count"},
                            {label: "Word count", value: "word_count"}
                        ]}
                    />
                    <Select
                        label="Character"
                        onChange={(e) => setActiveCharacter(e.target.value)}
                        options={
                            povs.map((pov) => ({
                                label: pov,
                                value: pov
                            }))
                        }
                    />
                </div>
            </div>
            <ResponsiveContainer
                width="100%"
                height="100%"
            >
                <LineChart
                    data={filteredData}
                >
                    <XAxis 
                        type="number"
                    />
                    <YAxis
                        dataKey={activeMetric}
                    />
                    <Tooltip />
                    <Line 
                        dataKey={activeMetric}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    )

}