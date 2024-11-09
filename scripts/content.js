(function () {
  // Function to initialize subtitle logging
  function initSubtitleLogger() {
    const video = document.querySelector("video");
    if (!video) {
      console.warn("No video element found on this page.");
      return;
    }

    const textTracks = video.textTracks;
    if (!textTracks || textTracks.length === 0) {
      console.warn("No text tracks available for this video.");
      return;
    }

    // Iterate through all text tracks to find subtitles/captions
    for (const track of video.textTracks) {
      if (track.kind === "subtitles" || track.kind === "captions") {
        // Set the track mode to 'hidden' to enable cue events without displaying them
        track.mode = "hidden";

        // Listen for cue changes
        track.addEventListener("cuechange", () => {
          const activeCues = track.activeCues;
          if (activeCues && activeCues.length > 0) {
            activeCues.forEach((cue) => {
              console.log(`Subtitle: ${cue.text}`);
            });
          }
        });
      }
    }
  }

  // Function to observe changes in the DOM to handle YouTube's dynamic content loading
  function observeVideoLoad() {
    const observer = new MutationObserver((mutations, obs) => {
      const video = document.querySelector("video");
      if (video) {
        initSubtitleLogger();
        obs.disconnect(); // Stop observing once the video is found and initialized
      }
    });

    // Start observing the body for added nodes
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  // Initialize the observer
  observeVideoLoad();
})();
