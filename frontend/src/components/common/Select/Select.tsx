import { forwardRef } from "react";
import styles from "./Select.module.css";

export type Option<T = string> = {
  label: string;
  value: T;
};

// 1. Separate your HTML props from your custom typed handlers
type SelectProps<T> = Omit<React.ComponentPropsWithoutRef<"select">, "onChange" | "value"> & {
  label: string;
  options: Option<T>[];
  value?: T;
  onChange?: (value: T) => void; // Passes your real object/type back, not an event
};

// 2. Wrap forwardRef in a custom function so TypeScript can pass the generic <T> down
export const Select = forwardRef(function SelectInner<T>(
  { label, options, value, onChange, ...rest }: SelectProps<T>,
  ref: React.ForwardedRef<HTMLSelectElement>
) {
  
  // 3. Find the index of the currently selected real object to set the HTML select value
  const currentIdx = options.findIndex((opt) => opt.value === value);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (!onChange) return;
    const selectedIndex = Number(e.target.value);
    
    // 4. Retrieve the actual original object/type T from your options array
    const realValue = options[selectedIndex].value;
    onChange(realValue);
  };

  return (
    <div className={styles["select-container"]}>
      <label className={styles["label"]} htmlFor={label}>
        {label}
      </label>
      <select
        id={label}
        ref={ref}
        className={rest.className}
        value={currentIdx !== -1 ? currentIdx : ""} // Uses index as string
        onChange={handleChange}
        {...rest}
      >
        <option value="" disabled selected hidden>
            {rest.defaultValue}
        </option>
        {options.map((option, idx) => (
          // 5. Pass the loop index as the native DOM string value
          <option key={idx} value={idx}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}) as <T>(props: SelectProps<T> & { ref?: React.ForwardedRef<HTMLSelectElement> }) => React.ReactElement;
