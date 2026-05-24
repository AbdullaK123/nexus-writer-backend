import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Field } from "@ark-ui/react/field"
import { useLogin, useRegister } from "../../data/queries"
import { match, Result } from "oxide.ts"
import { useNavigate, useSearch } from "@tanstack/react-router"
import { Button } from "../common"

const signupFormSchema = z.object({
    username: z.string().min(5, "Display name must be at least 5 characters."),
    email: z.email(),
    password: z.string().regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]).{8,}$/,
         "Password must be at least 8 characters with uppercase, lowercase, number, and special character"
    ),
    agreeTermsAndService: z.boolean().optional()
})
type SignupFormSchema = z.infer<typeof signupFormSchema>

export function SignupForm() {

    const {
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
        const result = await Result.safe(signup.mutateAsync({
            username: values.username,
            email: values.email,
            password: values.password
        }))
        match(result, {
            Ok: () => {
                const handleLogin = async () => {
                    const loginResult = await Result.safe(login.mutateAsync({email: values.email, password: values.password}))
                    match(loginResult, {
                        Ok: () => { navigate({ to: (search.redirect as string) ?? "/"})},
                        Err: (err) => { setError("root", { message: err.message })}
                    })
                }
                handleLogin()
            },
            Err: (err) => { setError("root", { message: err.message })}
        })
    })

    return (
        <form onSubmit={onSubmit} className="card">
            <header className="card__header">
                <span className="system-badge system-badge__nobg">[NEW VAULT]</span>
                <h2 className="card__title">BEGIN.</h2>
                <p className="card__subtitle">Your library. your rules. Free for as long as you write.</p>
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
                        {errors.password?.message}
                    </Field.ErrorText>
                )}
            </Field.Root>

            <Field.Root invalid={!!errors.password} className="field">
                <Field.Label className="field__label">
                    Password
                </Field.Label>
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

            {/*Password strength checker*/}

            <label className="checkbox-row">
                <input 
                    type="checkbox"
                    className="checkbox-input"
                    {...register("agreeTermsAndService")}
                />
                <span className="checkbox-row__label">I agree to the terms and service</span>
            </label>

            <Button
                variant="primary"
                type="submit"
                disabled={isSubmitting}
            >   
                {isSubmitting ? "Signing you ip..." : "Create Vault →"}
            </Button>
            <p className="card__footer">
                <span className="card__footer-text">Already have one?</span>
                <a href="/login" className="card__footer-link">Login</a>
            </p>
        </form>
    )
}