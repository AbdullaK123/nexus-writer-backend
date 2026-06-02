import { forwardRef } from "react";
import styles from "./Select.module.css"

type Option = {
    label: string 
    value: string
}

type SelectProps = {
  label: string
  options: Option[]
} & React.ComponentPropsWithoutRef<"select">


export const Select = forwardRef<HTMLSelectElement, SelectProps>(
    function Select({
        label,
        options,
        ...rest
    }, ref) {
        return (
            <div className={styles['select-container']}>
                <label className={styles['label']} htmlFor={label}>{label}</label>
                <select
                    id={label} 
                    ref={ref}
                    {...rest}
                >
                    {options.map((option) => (
                        <option 
                            key={option.value} 
                            value={option.value}
                        >
                            {option.label}
                        </option>
                    ))}
                </select>
            </div>
        )
    }
)