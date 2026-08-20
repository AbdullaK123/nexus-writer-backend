import { useRouteContext } from "@tanstack/react-router";
import { useDashboard, useStories } from "../../../data/queries";
import type { QueryObserverResult, RefetchOptions } from "@tanstack/react-query";
import type { DashboardResponse, StoryGridResponse } from "../../../infrastructure/api/types";
import { None, type ApiError } from "../../../shared/types";
import type { WelcomeHeaderProps } from "./WelcomeHeader";
import type { KpisRowProps } from "./KpisRow";
import type { JumpBackInRowProps } from "./JumpBackInRow";
import type { LibraryGridProps } from "./LibraryGrid/LibraryGrid";
import { useWelcomeHeaderProps } from "./hooks/useWelcomeHeaderProps";
import { useKpisRowProps } from "./hooks/useKpisRowProps";
import { useJumpBackInRowProps } from "./hooks/useJumpBackInRowProps";
import { useLibraryGridProps } from "./hooks/useLibraryGridProps";

export type RefetchProps = {
  dashboard: (options?: RefetchOptions) => Promise<QueryObserverResult<DashboardResponse, ApiError>>
  stories: (options?: RefetchOptions) => Promise<QueryObserverResult<StoryGridResponse, ApiError>>
}

export type DashboardPageProps = {
  welcomeHeader: WelcomeHeaderProps,
  kpisRow: KpisRowProps,
  jumpBackInRow: JumpBackInRowProps,
  libraryGrid: LibraryGridProps
}

export function useDashboardPage(): DashboardPageProps {
  const ctx = useRouteContext({ from: "/app" });
  const storiesState = useStories();
  const dashboardState = useDashboard();

  const welcomeHeader = useWelcomeHeaderProps({
    username: (ctx.auth.status === "authenticated") ? ctx.auth.user.username : "",
    profileImageUrl: None,
  });

  const kpisRow = useKpisRowProps({
    dashboardState
  });

  const jumpBackInRow = useJumpBackInRowProps({
    dashboardState
  });

  const libraryGrid = useLibraryGridProps({
    storiesState
  });

  return {
    welcomeHeader,
    kpisRow,
    jumpBackInRow,
    libraryGrid
  };
}
