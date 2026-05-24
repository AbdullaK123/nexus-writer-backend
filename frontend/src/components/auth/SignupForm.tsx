import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Field } from "@ark-ui/react/field"
import { useLogin, useRegister } from "../../data/queries"
import { useNavigate, useSearch } from "@tanstack/react-router"
import { Button } from "../common"
import { getPasswordStrength, PasswordStrengthMeter } from "./PasswordStrengthMeter";

const signupFormSchema = z.object({
    username: z.string().min(5, "Display name must be at least 5 characters."),
    email: z.email(),
    password: z.string().superRefine((val, ctx) => {
        const result = getPasswordStrength(val)
        if (result.score < 2) {
            ctx.addIssue({
                code: "custom",
                message: result.warning || "Password is too weak."
            })
        }
    }),
    agreeTermsAndService: z.literal(true)
})
type SignupFormSchema = z.infer<typeof signupFormSchema>

export function SignupForm() {

    const {
        watch,
        register,
        handleSubmit,
        formState: {
            errors,
            isSubmitting
        },
        setError
    } = useForm<SignupFormSchema>({ resolver: zodResolver(signupFormSchema)})

    const signup = useRegister()
    const login = useLogin()

    const navigate = useNavigate()

    const search = useSearch({ from: "/signup" })

    const onSubmit = handleSubmit(async (values) => {
       signup.mutate({
            username: values.username,
            email: values.email,
            password: values.password
       }, {
            onSuccess: () => {
                login.mutate({
                    email: values.email,
                    password: values.password
                }, {
                    onSuccess: () => navigate({ to: (search.redirect as string) ?? "/" }),
                    onError: (err) => setError("root", { message: err.detail })
                })
            },
            onError: (err) => {
                if (err.status === 409) 
                    setError("email", { message: err.detail }) 
                else 
                    setError("root", { message: err.detail})
            }
       })
    })
    
    const password = watch("password")

    return (
        <form onSubmit={onSubmit} className="card">
            <header className="card__header">
                <span className="system-badge system-badge__nobg">[NEW VAULT]</span>
                <h2 className="card__title">BEGIN.</h2>
                <p className="card__subtitle">Your library, your rules. Free for as long as you write.</p>
            </header>

            <Field.Root invalid={!!errors.username} className="field">
                <Field.Label className="field__label">
                    Display Name
                </Field.Label>
                <Field.Input 
                    type="text"
                    placeholder="John Doe..."
                    className="field__input"
                    {...register("username")}
                />
                {errors.username && (
                    <Field.ErrorText className="field__error">
                        {errors.username.message}
                    </Field.ErrorText>
                )}
            </Field.Root>

            <Field.Root invalid={!!errors.email} className="field">
                <Field.Label className="field__label">
                    Email
                </Field.Label>
                <Field.Input
                    type="email"
                    autoComplete="email"
                    placeholder="you@example.com"
                    className="field__input"
                    {...register("email")}
                />
                {errors.email && (
                    <Field.ErrorText className="field__error">
                        {errors.email?.message}
                    </Field.ErrorText>
                )}
            </Field.Root>

            <Field.Root invalid={!!errors.password} className="field">
                <Field.Label className="field__label">
                    Password
                </Field.Label>
                <Field.Input 
                    type="password"
                    autoComplete="new-password"
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

            {password && (
                <PasswordStrengthMeter 
                    {...getPasswordStrength(password)}
                />
            ) }

            <label className="checkbox-row">
                <input 
                    type="checkbox"
                    className="checkbox-input"
                    {...register("agreeTermsAndService")}
                />
                <span className="checkbox-row__label">I agree to the Terms and Privacy Policy</span>
            </label>

            <Button
                variant="primary"
                type="submit"
                disabled={isSubmitting}
            >   
                {isSubmitting ? "Signing you up..." : "CREATE VAULT →"}
            </Button>
            <p className="card__footer">
                <span className="card__footer-text">Already have one?</span>
                <a href="/login" className="card__footer-link">Log in →</a>
            </p>
            {errors.root && (
                <span className="suggestion">
                    {errors.root.message}
                </span>
            )}
        </form>
    )
}