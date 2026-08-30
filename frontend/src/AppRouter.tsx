import { RouterProvider } from "@tanstack/react-router";
import { useAuthOrThrow, useSettings } from "./data/providers";
import { router } from "./router";
import { useEffect, useRef } from "react";
import { None, Some, streamSse } from "./infrastructure/sse";
import { createSseLifecycleCleanup } from "./infrastructure/sse/lifecycle";
import { AbortControllerSlot } from "./shared/abortControllerSlot";
import type { EventSourceMessage } from "eventsource-parser";
import { useToast } from "./components";
import { NotificationSchema } from "./infrastructure/api/types";
import { useQueryClient } from "@tanstack/react-query";
import { authKeys, chapterKeys, storyKeys } from "./data/queries";
import { isRetryable, isTerminal } from "./infrastructure/sse/notifications";
import { useTheme } from "./hooks";

const MAX_RETRIES = 5;
const BASE_DELAY_MS = 1000;

export function AppRouter() {
  const auth = useAuthOrThrow();
  const qc = useQueryClient();
  const { info, error } = useToast();

  const streamSlotRef = useRef(new AbortControllerSlot());
  const timerRef = useRef<number | null>(null);
  const retriesRef = useRef(0);
  const stoppedRef = useRef(false);
  const { settings } = useSettings()

  const theme = settings.isSome()
      ? settings.unwrap().appearance.theme
      : "system"

  useTheme(theme)

  useEffect(() => {
    router.invalidate();
  }, [auth.status]);

  useEffect(() => {
    stoppedRef.current = false;
    retriesRef.current = 0;

    const cleanup = createSseLifecycleCleanup(
      streamSlotRef.current,
      timerRef,
      stoppedRef,
      (id) => window.clearTimeout(id),
    )

    const scheduleReconnect = (reason: string) => {
      if (stoppedRef.current || auth.status !== "authenticated") return;
      if (retriesRef.current >= MAX_RETRIES) {
        info("Notifications stopped", "Could not reconnect.");
        return;
      }

      const delay = BASE_DELAY_MS * (retriesRef.current + 1);
      retriesRef.current += 1;
      info("Reconnecting", `${reason} (attempt ${retriesRef.current})`);

      timerRef.current = window.setTimeout(() => {
        timerRef.current = null;
        connect();
      }, delay);
    };

    const connect = () => {
      if (stoppedRef.current || auth.status !== "authenticated") return;

      const controller = streamSlotRef.current.replace()

      void streamSse(
        {
          url: "auth/me/notifications",
          method: Some("GET"),
          body: None,
          headers: None,
          signal: Some(controller.signal),
        },
        {
          onEvent: (event: EventSourceMessage) => {
            if (event.event !== "notification") return;

            let parsed: unknown;
            try {
              parsed = JSON.parse(event.data);
            } catch {
              return;
            }

            const notification = NotificationSchema.safeParse(parsed);
            if (notification.error) return;

            retriesRef.current = 0;

            switch (notification.data.kind) {
              case "scenes_extracted":
                info("Extraction complete!", notification.data.message);
                qc.invalidateQueries({ queryKey: authKeys.dashboard() });
                break;
              case "analysis_ready":
                if (settings.isSome() ? settings.unwrap().notifications.analysis_ready : false) {
                    info("Analysis ready!", notification.data.message);
                    qc.invalidateQueries({ queryKey: storyKeys.pulse(notification.data.story_id) }); 
                }
                break;
              case "comments_ready":
                if (settings.isSome() ? settings.unwrap().notifications.comments_ready : false ) {
                    info("Comments ready!", notification.data.message)
                    qc.invalidateQueries({ queryKey: chapterKeys.comments(notification.data.chapter_id)})
                }
                break;
              case "job_failed":
                if (settings.isSome() ? settings.unwrap().notifications.job_failures : false) {
                    error("Error!", notification.data.message)
                }
            }
          },
          onClose: Some(() => {
            scheduleReconnect("Stream closed");
          }),
        },
      ).then((result) => {
        if (controller.signal.aborted) return;
        streamSlotRef.current.clearIfCurrent(controller)

        if (result.isErr()) {
          const err = result.unwrapErr();

          if (isTerminal(err)) {
            if (err._tag === "SseHttpError" && (err.status === 401 || err.status === 403)) {
              void qc.resetQueries({
                queryKey: authKeys.me(),
                exact: true,
              });
              info("Session expired", "Please sign in again.");
            }
            return;
          }

          if (isRetryable(err)) {
            scheduleReconnect("Connection interrupted");
            return;
          }

          info("Notifications stopped", "Unhandled stream error.");
        }
      });
    };

    cleanup()
    stoppedRef.current = false

    if (auth.status === "authenticated") {
      timerRef.current = window.setTimeout(() => {
        timerRef.current = null;
        connect();
      }, 2000);
    }

    return cleanup;
  }, [auth.status, info, qc, error, settings]);

  return <RouterProvider router={router} context={{ auth }} />;
}
