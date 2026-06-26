import { AvatarBadge, SectionTag } from "../../../common";
import styles from "./WelcomeHeader.module.css"
import { Option } from "oxide.ts"

export type WelcomeHeaderProps =
  | {
      status: 'ready'
      username: string
      profileImageUrl: Option<string>
      query: string
      onQueryChange: (v: string) => void
      onEnterDown: (query: string) => void
    }

export function WelcomeHeader(props: WelcomeHeaderProps) {
  switch (props.status) {
    case 'ready':
      return (
        <div className={styles['header-container']}>
          <div className={styles['welcome-section-container']}>
            <SectionTag sectionName={`${props.username} - online`} />
            <h2>Welcome Back.</h2>
          </div>
          <div className={styles['search-section-container']}>
            <input
              type="text"
              value={props.query}
              className="field__input"
              onChange={(e) => props.onQueryChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && props.query.trim() !== '') props.onEnterDown(props.query)
              }}
              placeholder="Search scenes, chapters..."
            />
            <AvatarBadge username={props.username} profileImgUrl={props.profileImageUrl} />
          </div>
        </div>
      )
  }
}