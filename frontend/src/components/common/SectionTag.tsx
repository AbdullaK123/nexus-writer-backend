

type SectionTagProps = {
    sectionName: string;
}


export function SectionTag({ sectionName }: SectionTagProps) {
    return (
        <span className="section-tag">
            [{sectionName}]
        </span>
    )
}