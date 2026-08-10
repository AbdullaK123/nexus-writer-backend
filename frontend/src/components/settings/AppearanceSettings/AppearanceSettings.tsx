import { useEffect } from "react";
import { useSettings } from "../../../data/providers";
import { Button, Select } from "../../common";
import Switch from "../../common/Switch/Switch";
import { type AppearanceSettings } from "../../../infrastructure/api/types"
import { Controller, useForm } from "react-hook-form";
import styles from "./AppearanceSettings.module.css"


export function AppearanceSettings() {

    const { settings, updateSettings } = useSettings()
    const { 
        control, 
        handleSubmit, 
        reset, 
        formState: { isDirty, isSubmitting } 
    } = useForm<AppearanceSettings>({
        defaultValues: {
            theme: "system",
            reduced_motion: false
        }
    })
    useEffect(() => {
        if (settings.isSome()) {
            reset(settings.unwrap().appearance)
        }
    }, [settings, reset])

    const onSubmit = (values: AppearanceSettings) => {
        updateSettings({ kind: "appearance", appearance: values })
    }

    return (
        <div className={styles['content']}>
            <div className={styles['header']}>
                <span className="system-badge system-badge__nobg">
                    [APPEARANCE]
                </span>
                {isDirty && (
                    <span className={styles['dirty-indicator']}>
                        *
                    </span>
                )}
            </div>
            <form className={styles['form-content']} onSubmit={handleSubmit(onSubmit)}>
               <Controller 
                    control={control}
                    name="theme"
                    render={({ field }) => (
                        <Select 
                            label="theme"
                            options={[
                                {"label": "system", value: "system"},
                                {"label": "light", value: "light"},
                                {"label": "dark", value: "dark"}
                            ]}
                            onChange={field.onChange}
                            value={field.value}
                        />
                    )}
               />
               <Controller
                    control={control}
                    name="reduced_motion"
                    render={({ field }) => (
                        <Switch
                            checked={field.value}
                            onCheckedChanged={field.onChange}
                            label="Enable reduced motion"
                        />
                    )}
                />
                <Button 
                    disabled={isSubmitting}
                    variant="primary" 
                    type="submit"
                >
                    Submit
                </Button>
            </form>
        </div>
    )
}