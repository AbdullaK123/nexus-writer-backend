import { useEffect, useEffectEvent } from "react";
import type { JumpBackInRowProps } from "../JumpBackInRow";
import type { AsyncState, DashboardResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import { useToast } from "../../../common";
import { useNavigate } from "@tanstack/react-router";

export function useJumpBackInRowProps(args: { dashboardState: AsyncState<DashboardResponse, ApiError>; onRetry: () => void }): JumpBackInRowProps {
  const { dashboardState, onRetry } = args;
  const { error } = useToast();
  const onDashboardError = useEffectEvent(() => {
    error("Failed to load recent chapters.", "Something went wrong. If the problem persists, please contact support.");
  });

  const navigate = useNavigate()

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
      if (d.jumpBackIn.length === 0) return { status: 'empty' };
      return {
        status: 'ready',
        chapterCards: d.jumpBackIn.map(card => ({ ...card, onClick: () => navigate({ to: "/stories/$storyId/$chapterId", params: { storyId: card.storyId, chapterId: card.chapterId } }) }))
      };
    }
  }
}
