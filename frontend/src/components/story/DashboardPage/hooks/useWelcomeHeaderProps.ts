import { useState } from "react";
import type { WelcomeHeaderProps } from "../WelcomeHeader";
import { Option } from "oxide.ts";

export function useWelcomeHeaderProps(args: { username: string; profileImageUrl: Option<string> }): WelcomeHeaderProps {
  const [query, setQuery] = useState("");
  return {
    status: 'ready',
    username: args.username,
    profileImageUrl: args.profileImageUrl,
    query,
    onQueryChange: setQuery,
    onEnterDown: (q: string) => { console.log(q); }
  };
}
