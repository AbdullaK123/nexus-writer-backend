import { useRef, useState } from "react";
import type { LibraryGridProps } from "../LibraryGrid/LibraryGrid";
import type { AsyncState, StoryGridResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import { useCreateStory} from "../../../../data/queries";
import { useToast } from "../../../common";
import { useNavigate } from "@tanstack/react-router"
import { SingleFlightGate } from "../../../../shared/singleFlight";

export function useLibraryGridProps(args: { storiesState: AsyncState<StoryGridResponse, ApiError> }): LibraryGridProps {
  const { storiesState } = args;
  const { error, success } = useToast();
  const { mutate: createStory } = useCreateStory();
  const createStoryGateRef = useRef(new SingleFlightGate())
  const navigate = useNavigate()

  const [modalOpen, setModalOpen] = useState(false);
  const [storyTitle, setStoryTitle] = useState("");
  const [libraryFilter, setLibraryFilter] = useState<'all' | 'ongoing' | 'hiatus' | 'complete'>("all");

  const onNewStory = (title: string) => {
    if (!createStoryGateRef.current.tryStart()) return

    createStory({ title }, {
      onSuccess: () => {
        success("Success!", "Your story has been successfully created! Happy writing!");
        setStoryTitle("");
        setModalOpen(false);
      },
      onError: () => {
        error("Failed to create your story.", "Something went wrong. If the problem persists, please contact support.");
        setModalOpen(false);
      },
      onSettled: () => {
        createStoryGateRef.current.finish()
      }
    })
  }

  switch (storiesState.status) {
    case 'idle':
    case 'loading':
      return { status: 'loading' };
    case 'empty':
      return {
        status: 'empty',
        modalOpen,
        onModalOpenChange: (e: boolean) => setModalOpen(e),
        storyTitle,
        onStoryTitleChange: (v: string) => setStoryTitle(v),
        onNewStory,
      };
    case 'success': {
      const data = storiesState.data.unwrap().unwrap();
      const stories = data.stories.map(s => ({ ...s, onClick: () => navigate({ to: `/stories/${s.storyId}` }) }));
      if (stories.length === 0) {
        return {
          status: 'empty',
          modalOpen,
          onModalOpenChange: (e: boolean) => setModalOpen(e),
          storyTitle,
          onStoryTitleChange: (v: string) => setStoryTitle(v),
          onNewStory,
        };
      }
      const counts = stories.reduce(
        (acc, s) => {
          acc.all += 1;
          switch (s.status) {
            case 'Ongoing': acc.ongoing += 1; break;
            case 'On Hiatus': acc.hiatus += 1; break;
            case 'Complete': acc.complete += 1; break;
          }
          return acc;
        },
        { all: 0, ongoing: 0, hiatus: 0, complete: 0 }
      );
      const filterFn = (s: typeof stories[number]) =>
        libraryFilter === 'all' ? true :
        libraryFilter === 'ongoing' ? s.status === 'Ongoing' :
        libraryFilter === 'hiatus' ? s.status === 'On Hiatus' :
        s.status === 'Complete';
      const filtered = stories.filter(filterFn);
      return {
        status: 'ready',
        stories: filtered,
        selected: libraryFilter,
        counts,
        onSelect: setLibraryFilter,
        modalOpen,
        onModalOpenChange: (e: boolean) => setModalOpen(e),
        storyTitle,
        onStoryTitleChange: (v: string) => setStoryTitle(v),
        onNewStory,
      };
    }
  }
}
