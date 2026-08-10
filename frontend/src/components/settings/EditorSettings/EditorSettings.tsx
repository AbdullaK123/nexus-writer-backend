import { Controller, useForm } from "react-hook-form";
import { useSettings } from "../../../data/providers";
import { type EditorSettings } from "../../../infrastructure/api/types"
import { useEffect } from "react";
import styles from "./EditorSettings.module.css"
import { Button, Select } from "../../common";
import { Field } from "@ark-ui/react";
import Switch from "../../common/Switch/Switch";

const EDITOR_FONTS = [
    "Literata",
    "Source Serif 4",
    "IBM Plex Serif",
    "Lora",
    "Merriweather",
    "Alegreya",
    "Noto Serif",
    "Exo 2",
    "IBM Plex Sans",
    "JetBrains Mono",
] as const

export function EditorSettings() {
    const { settings, updateSettings } = useSettings()
    const {
        control,
        register,
        handleSubmit,
        reset,
        formState: { isDirty, isSubmitting, errors }
    } = useForm<EditorSettings>({
        defaultValues: {
            font_family: "Literata",
            font_size: 18,
            line_height: 1.7,
            content_width: 760,
            spellcheck: true
        }
    })
    useEffect(() => {
        if (settings.isSome()) {
            reset(settings.unwrap().editor)
        }
    }, [settings, reset])

    const onSubmit = (values: EditorSettings) => {
        updateSettings({ kind: "editor", editor: values})
    }

    return (
        <div className={styles['content']}>
            <div className={styles['header']}>
                <span className="system-badge system-badge__nobg">
                    [EDITOR]
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
                    name="font_family"
                    render={({ field }) => (
                        <Select 
                            label="Font"
                            options={EDITOR_FONTS.map((font) => ({
                                label: font,
                                value: font
                            }))}
                            onChange={field.onChange}
                            value={field.value}
                        />
                    )}
               />
               <Field.Root invalid={!!errors.font_size} className="field">
                    <Field.Label className="field__label">
                        Font size
                    </Field.Label>
                    <Field.Input 
                        type="number"
                        className="field__input"
                        {...register("font_size")}
                    />
                    {errors.font_size && (
                        <Field.ErrorText className="field__error">
                            {errors.font_size.message}
                        </Field.ErrorText>
                    )}
               </Field.Root>
               <Field.Root invalid={!!errors.line_height} className="field">
                    <Field.Label className="field__label">
                        Line height
                    </Field.Label>
                    <Field.Input 
                        type="number"
                        className="field__input"
                        {...register("line_height")}
                    />
                    {errors.line_height && (
                        <Field.ErrorText className="field__error">
                            {errors.line_height.message}
                        </Field.ErrorText>
                    )}
               </Field.Root>
               <Field.Root invalid={!!errors.content_width} className="field">
                    <Field.Label className="field__label">
                        Content width
                    </Field.Label>
                    <Field.Input 
                        type="number"
                        className="field__input"
                        {...register("content_width")}
                    />
                    {errors.content_width && (
                        <Field.ErrorText className="field__error">
                            {errors.content_width.message}
                        </Field.ErrorText>
                    )}
               </Field.Root>
               <Controller
                    control={control}
                    name="spellcheck"
                    render={({ field }) => (
                        <Switch
                            checked={field.value}
                            onCheckedChanged={field.onChange}
                            label="Enable spellcheck"
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