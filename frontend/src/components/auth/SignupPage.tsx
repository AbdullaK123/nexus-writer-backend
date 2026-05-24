import { SignupForm } from "./SignupForm";


export function SignupPage() {
    return (
        <div className="auth-page">
            <aside className="auth-page__hero">
                <div className="hero-brand__row">
                    <span className="hero-brand__logo">NX</span>
                    <p className="hero-brand__name">NEXUS WRITER</p>
                </div>
                <div className="hero-content">
                    <span className="section-tag">[BEGIN A NEW VAULT]</span>
                    <h1 className="hero-content__headline">
                        You Write.<br />
                        We Remember.<br />
                    </h1>
                    <div className="hero-brand">
                        <div className="hero-promise">
                            <span className="hero-brand__numeral">01</span>
                            <div>
                                <h3 className="hero-promise__headline">Every scene, indexed.</h3>
                                <p className="hero-content__subtitle">Background extraction turns chapters into searchable scenes. Characters, tension, pacing, threads. All Queryable.</p>
                            </div>
                        </div>
                        <div className="hero-promise">
                            <span className="hero-brand__numeral">02</span>
                            <div>
                                <h3 className="hero-promise__headline">An agent that's read it.</h3>
                                <p className="hero-content__subtitle">Ask anything about your own book. The agent runs hybrid search and cites the chapters it pulled from.</p>
                            </div>
                        </div>
                        <div className="hero-promise">
                            <span className="hero-brand__numeral">03</span>
                            <div>
                                <h3 className="hero-promise__headline">Inline edits you control.</h3>
                                <p className="hero-content__subtitle">Suggestions appear as Grammarly-style underlines. Accept, reject, or refine each one.</p>
                            </div>
                        </div>
                    </div>
                </div>
                <footer className="hero-footer">
                    <span className="hero-footer__credit">[BUILT BY ABDULLA]</span>
                    <span className="hero-footer__sep">·</span>
                    <a href="#" className="hero-footer__link">Privacy</a>
                    <span className="hero-footer__sep">·</span>
                    <a href="#" className="hero-footer__link">Terms</a>
                </footer>
            </aside>
            <main className="auth-page__form-pane">
                <SignupForm/>
            </main>
        </div>
    )
}