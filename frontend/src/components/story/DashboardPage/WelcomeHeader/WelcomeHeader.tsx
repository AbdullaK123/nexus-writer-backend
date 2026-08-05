import { SectionTag } from "../../../common";
import styles from "./WelcomeHeader.module.css"
import { Option } from "oxide.ts"
import { WelcomeHeaderLoadingSkeleton } from "./WelcomeHeaderLoadingSkeleton"

export type WelcomeHeaderProps =
  | { status: "loading"}
  | {
      status: 'ready'
      username: string
      profileImageUrl: Option<string>
    }

export function WelcomeHeader(props: WelcomeHeaderProps) {
  switch (props.status) {
    case "loading":
      return <WelcomeHeaderLoadingSkeleton />
    case 'ready':
      return (
        <div className={styles['header-container']}>
          <div className={styles['welcome-section-container']}>
            <SectionTag sectionName={`${props.username} - online`} />
            <h2>Welcome Back.</h2>
          </div>
        </div>
      )
  }
}