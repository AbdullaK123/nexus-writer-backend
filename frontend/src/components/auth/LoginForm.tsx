import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Field } from "@ark-ui/react/field"
import { useLogin } from "../../data/queries";
import { useNavigate, useSearch } from "@tanstack/react-router"
import { Button } from "../common";

const loginFormSchema = z.object({
    email: z.email("Invalid email"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    rememberMe: z.boolean().optional(),
})

type LoginFormSchema = z.infer<typeof loginFormSchema>


export function LoginForm() {

    const {
        register,
        handleSubmit,
        formState: {
            errors,
            isSubmitting
        },
        setError
    } = useForm<LoginFormSchema>({ resolver: zodResolver(loginFormSchema) })

    const login = useLogin()

    const navigate = useNavigate()

    const search = useSearch({ from: "/login" })

    const onSubmit = handleSubmit(async (values) => {
        login.mutate({
            email: values.email,
            password: values.password
        }, {
            onSuccess: () => navigate({ to: search.redirect ?? "/"}),
            onError: (err) => setError("root", { message: err.detail })
        })
    })

    return (
        <form onSubmit={onSubmit} className="card login-card">
            <header className="card__header">
                <span className="system-badge system-badge__nobg">[ACCESS]</span>
                <h2 className="card__title">WELCOME BACK.</h2>
                <p className="card__subtitle">Log in to your library.</p>
            </header>

            <Field.Root invalid={!!errors.email} className="field">
                <Field.Label className="field__label">Email</Field.Label>
                <Field.Input
                    type="email"
                    autoComplete="email"
                    placeholder="you@example.com"
                    className="field__input"
                    {...register("email")}
                />
                {errors.email && (
                    <Field.ErrorText className="field__error">
                        {errors.email.message}
                    </Field.ErrorText>
                )}
            </Field.Root>

            <Field.Root invalid={!!errors.password} className="field">
                <div className="field__header">
                    <Field.Label className="field__label">Password</Field.Label>
                    <a href="#" className="field__action">Forgot?</a>
                </div>
                <Field.Input
                    type="password"
                    autoComplete="current-password"
                    placeholder="••••••••••"
                    className="field__input"
                    {...register("password")}
                />
                {errors.password && (
                    <Field.ErrorText className="field__error">
                        {errors.password.message}
                    </Field.ErrorText>
                )}
            </Field.Root>

            <label className="checkbox-row">
                <input
                    type="checkbox"
                    className="checkbox-input"
                    {...register("rememberMe")}
                />
                <span className="checkbox-row__label">Keep me signed in for 30 days</span>
            </label>

            {errors.root && (
                <p className="form-error" role="alert">{errors.root.message}</p>
            )}

            <Button
                variant="primary"
                type="submit"
                disabled={isSubmitting}
            >
                {isSubmitting ? "Signing you in..." : "Launch Nexus  →"}
            </Button>

            <div className="divider">
                <span className="divider__line" />
                <span className="divider__label">OR</span>
                <span className="divider__line" />
            </div>

            <p className="card__footer">
                <span className="card__footer-text">Don't have a vault?</span>
                <a href="/signup" className="card__footer-link">Begin one →</a>
            </p>
        </form>
    )
}