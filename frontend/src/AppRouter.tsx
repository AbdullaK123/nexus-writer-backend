import { RouterProvider } from "@tanstack/react-router";
import { useAuthOrThrow, useSettings } from "./data/providers";
import { router } from "./router";
import { useEffect, useRef } from "react";
import { None, Some, streamSse } from "./infrastructure/sse";
import type { EventSourceMessage } from "eventsource-parser";
import { useToast } from "./components";
import { NotificationSchema } from "./infrastructure/api/types";
import { useQueryClient } from "@tanstack/react-query";
import { authKeys, chapterKeys, storyKeys } from "./data/queries";
import { isRetryable, isTerminal } from "./infrastructure/sse/notifications";

const MAX_RETRIES = 5;
const BASE_DELAY_MS = 1000;

export function AppRouter() {
  
  const auth = useAuthOrThrow();
  const qc = useQueryClient();
  const { info, error } = useToast();

  const controllerRef = useRef<AbortController | null>(null);
  const timerRef = useRef<number | null>(null);
  const retriesRef = useRef(0);
  const stoppedRef = useRef(false);
  const { settings } = useSettings()

  // Invalidate router immediately when auth changes
  useEffect(() => {
    router.invalidate();
  }, [auth.status]);

  // Unified SSE Lifecycle Stream Controller
  useEffect(() => {
    stoppedRef.current = false;
    retriesRef.current = 0;

    const clearAll = () => {
      controllerRef.current?.abort();
      controllerRef.current = null;
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };

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

      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;

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

            retriesRef.current = 0; // Reset healthy connection tracker

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
        controllerRef.current = null;

        if (result.isErr()) {
          const err = result.unwrapErr();

          if (isTerminal(err)) {
            if (err._tag === "SseHttpError" && (err.status === 401 || err.status === 403)) {
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

    // Clean up past stream hooks and initialize new stream if authorized
    clearAll();

    if (auth.status === "authenticated") {
        
        const id = window.setTimeout(() => {
            connect();
        }, 2000);

        return () => {
            window.clearTimeout(id);
        };
    }

    // Clean up on component unmount or auth status swap
    return () => {
      stoppedRef.current = true;
      clearAll();
    };
  }, [auth.status, info, qc]); // React query and layout helpers stay immutable, triggering updates correctly only when auth shifts

  return <RouterProvider router={router} context={{ auth }} />;
}
