import type { WelcomeHeaderProps } from "../WelcomeHeader";
import { Option } from "oxide.ts";

export function useWelcomeHeaderProps(args: { username: string; profileImageUrl: Option<string> }): WelcomeHeaderProps {
  return {
    status: 'ready',
    username: args.username,
    profileImageUrl: args.profileImageUrl
  };
}
