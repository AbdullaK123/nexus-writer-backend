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
               <Controller
                    control={control}
                    name="font_size"
                    render={({ field }) => (
                        <Field.Root
                            invalid={!!errors.font_size}
                            className="field"
                        >
                            <Field.Label className="field__label">
                                Font size
                            </Field.Label>

                            <Field.Input
                                ref={field.ref}
                                name={field.name}
                                type="number"
                                min={10}
                                max={36}
                                className="field__input"
                                value={field.value}
                                onBlur={field.onBlur}
                                onChange={(e) =>
                                    field.onChange(e.currentTarget.valueAsNumber)
                                }
                            />
                        </Field.Root>
                    )}
                />
               <Controller
                    control={control}
                    name="line_height"
                    render={({ field }) => (
                        <Field.Root
                            invalid={!!errors.line_height}
                            className="field"
                        >
                            <Field.Label className="field__label">
                                Line height
                            </Field.Label>

                            <Field.Input
                                ref={field.ref}
                                name={field.name}
                                type="number"
                                min={1}
                                max={2}
                                step={0.1}
                                className="field__input"
                                value={field.value}
                                onBlur={field.onBlur}
                                onChange={(e) =>
                                    field.onChange(e.currentTarget.valueAsNumber)
                                }
                            />
                        </Field.Root>
                    )}
                />
               <Controller
                    control={control}
                    name="content_width"
                    render={({ field }) => (
                        <Field.Root
                            invalid={!!errors.content_width}
                            className="field"
                        >
                            <Field.Label className="field__label">
                                Content width
                            </Field.Label>

                            <Field.Input
                                ref={field.ref}
                                name={field.name}
                                type="number"
                                min={760}
                                max={1024}
                                className="field__input"
                                value={field.value}
                                onBlur={field.onBlur}
                                onChange={(e) =>
                                    field.onChange(e.currentTarget.valueAsNumber)
                                }
                            />
                        </Field.Root>
                    )}
                />
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