import { Select as ArcSelect, createListCollection } from "@ark-ui/react/select"

type Option = {
    label: string 
    value: string
}

type SelectProps = {
    options: Option[]
    value?: string 
    defaultValue?: string
    placeholder?: string 
    onChange?: (value: string) => void
}


export function Select({
    options,
    value,
    defaultValue,
    placeholder,
    onChange
}: SelectProps) {

    const collection = createListCollection<Option>({
        items: options
    })

    const handleValueChange = (details: ArcSelect.ValueChangeDetails<Option>) => {
        if (onChange) {
            onChange(details.value[0])
        }
    }


    return (
        <ArcSelect.Root
            collection={collection}
            value={value ? [value] : undefined}
            defaultValue={ defaultValue ? [defaultValue] : undefined }
            onValueChange={handleValueChange}
        >
            <ArcSelect.Trigger>
                <ArcSelect.ValueText placeholder={placeholder} />
            </ArcSelect.Trigger>

            <ArcSelect.Positioner>
                <ArcSelect.Content>
                    {collection.items.map((option) => (
                        <ArcSelect.Item key={option.value} item={option}>
                            <ArcSelect.ItemText>{option.label}</ArcSelect.ItemText>
                            <ArcSelect.ItemIndicator>✓</ArcSelect.ItemIndicator>
                        </ArcSelect.Item>
                    ))}
                </ArcSelect.Content>
            </ArcSelect.Positioner>

        </ArcSelect.Root>
    )
}