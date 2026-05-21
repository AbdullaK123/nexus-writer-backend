import { LoginForm } from "./LoginForm"

export function LoginPage() {
    return (
        <div className="login-page">
            <aside className="login-page__hero">
                <div className="hero-brand">
                    <div className="hero-brand__row">
                        <span className="hero-brand__logo">NX</span>
                        <p className="hero-brand__name">NEXUS WRITER</p>
                    </div>
                    <span className="system-badge">
                        <span className="system-badge__dot" />
                        [SYSTEM ONLINE · v1.0.0]
                    </span>
                </div>

                <div className="hero-content">
                    <span className="section-tag">[FOR LONG-FORM NOVELISTS]</span>
                    <h1 className="hero-content__headline">
                        Write like<br />
                        a reader<br />
                        knows<br />
                        the book.
                    </h1>
                    <p className="hero-content__subtitle">
                        Every chapter remembered. Every scene findable. Every
                        thread you've left dangling, watched over by an agent that
                        has read it all.
                    </p>
                </div>

                <footer className="hero-footer">
                    <span className="hero-footer__credit">[BUILT BY ABDULLA]</span>
                    <span className="hero-footer__sep">·</span>
                    <a href="#" className="hero-footer__link">Privacy</a>
                    <span className="hero-footer__sep">·</span>
                    <a href="#" className="hero-footer__link">Terms</a>
                </footer>
            </aside>

            <main className="login-page__form-pane">
                <LoginForm />
            </main>
        </div>
    )
}