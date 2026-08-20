
import type { KpisRowProps } from "../KpisRow";
import type { AsyncState, DashboardResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";


export function useKpisRowProps(args: { dashboardState: AsyncState<DashboardResponse, ApiError> }): KpisRowProps {
  const { dashboardState } = args;
  switch (dashboardState.status) {
    case 'idle':
    case 'loading':
      return { status: 'loading' };
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
