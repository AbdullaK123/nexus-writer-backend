import { useEffect, useEffectEvent } from "react";
import type { KpisRowProps } from "../KpisRow";
import type { AsyncState, DashboardResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import { useToast } from "../../../common";

export function useKpisRowProps(args: { dashboardState: AsyncState<DashboardResponse, ApiError>; onRetry: () => void }): KpisRowProps {
  const { dashboardState, onRetry } = args;
  const { error } = useToast();
  const onDashboardError = useEffectEvent(() => {
    error("Failed to load your dashboard.", "Something went wrong. If the problem persists, please contact support.");
  });
  useEffect(() => {
    if (dashboardState.status === 'error') onDashboardError();
  }, [dashboardState.status]);

  switch (dashboardState.status) {
    case 'idle':
    case 'loading':
      return { status: 'loading' };
    case 'error':
      return { status: 'error', onRetry };
    case 'empty':
      return { status: 'empty' };
    case 'success': {
      const d = dashboardState.data.unwrap().unwrap();
      return {
        status: 'ready',
        totalWords: d.totalWords,
        storyCount: d.totalStories,
        totalChapters: d.chaptersTotal,
        chaptersPublished: d.chaptersPublished,
        currentStreak: d.streakDays,
        totalScenesTracked: d.scenesTracked,
      };
    }
  }
}
