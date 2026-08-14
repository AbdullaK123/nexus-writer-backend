import { Controller, useForm } from "react-hook-form";
import { useSettings } from "../../../data/providers";
import { type NotificationSettings } from "../../../infrastructure/api/types"
import { useEffect } from "react";
import styles from "./NotificationSettings.module.css"
import { Button } from "../../common";
import Switch from "../../common/Switch/Switch";

export function NotificationSettings() {
    const { settings, updateSettings } = useSettings()
    const {
        control,
        handleSubmit,
        reset,
        formState: { isDirty, isSubmitting }
    } = useForm<NotificationSettings>({
        defaultValues: {
            analysis_ready: true,
            comments_ready: true,
            job_failures: true
        }
    })
    useEffect(() => {
        if (settings.isSome()) {
            reset(settings.unwrap().notifications)
        }
    }, [settings, reset])

    const onSubmit = (values: NotificationSettings) => {
        updateSettings({ kind: "notifications", notifications: values})
    }

    return (
        <div className={styles['content']}>
            <div className={styles['header']}>
                <span className="system-badge system-badge__nobg">
                    [NOTIFICATIONS]
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
                    name="analysis_ready"
                    render={({ field }) => (
                        <Switch
                            checked={field.value}
                            onCheckedChanged={field.onChange}
                            label="Receive notifications whenever Nexus finishes an analysis or extraction?"
                        />
                    )}
                />
                <Controller
                    control={control}
                    name="comments_ready"
                    render={({ field }) => (
                        <Switch
                            checked={field.value}
                            onCheckedChanged={field.onChange}
                            label="Receive a notification whenever Nexus generates a batch of comments?"
                        />
                    )}
                />
                <Controller
                    control={control}
                    name="job_failures"
                    render={({ field }) => (
                        <Switch
                            checked={field.value}
                            onCheckedChanged={field.onChange}
                            label="Receive a notification whenever Nexus runs into a technical issue?"
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