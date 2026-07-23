import type { CastStatisticsRow } from "../../../../../infrastructure/api/types/analytics";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from "recharts"

export type CharacterBarChartProps = 
{
    data: CastStatisticsRow[]
}

export function CharacterBarChart(props: CharacterBarChartProps) {
    return (
        <div>
            <ResponsiveContainer
                width="100%"
                height="100%"
            >
                <BarChart
                    layout="vertical"
                    data={props.data}
                >
                    <CartesianGrid 
                        strokeDasharray="3 3" 
                        horizontal={false}
                    />
                    <XAxis 
                        type="number"
                        tickLine={false}
                    />
                    <YAxis 
                        dataKey="character"
                        type="category"
                        tickLine={false}
                    />
                    <Tooltip />
                    <Legend />
                    <Bar 
                        dataKey="scene_count"
                        name="Number of scenes"
                    />
                    <Bar 
                        dataKey="word_count"
                        name="Word count"
                    />
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}