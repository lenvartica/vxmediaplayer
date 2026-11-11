(() => {
  const root = document.documentElement;
  const repository = root.dataset.repository || "lenvartica/vxmediaplayer";
  const releaseUrl = `https://api.github.com/repos/${repository}/releases/latest`;
  const latestPage = `https://github.com/${repository}/releases/latest`;
  const note = document.querySelector("#release-note");

  document.querySelectorAll(".download-link").forEach((link) => {
    link.href = latestPage;
  });

  fetch(releaseUrl, { headers: { Accept: "application/vnd.github+json" } })
    .then((response) => {
      if (!response.ok) throw new Error(`GitHub returned ${response.status}`);
      return response.json();
    })
    .then((release) => {
      const windowsAsset = release.assets.find((asset) =>
        asset.name.toLowerCase() === "vxplayer-setup.exe"
      ) || release.assets.find((asset) =>
        asset.name.toLowerCase().includes("vxplayer") &&
        asset.name.toLowerCase().endsWith(".exe")
      );
      if (windowsAsset) {
        document.querySelectorAll('.download-link[data-platform="windows"]')
          .forEach((link) => { link.href = windowsAsset.browser_download_url; });
        if (note) note.textContent = `${release.tag_name} · Free and open source · No account required`;
      }
    })
    .catch(() => {
      if (note) note.textContent = "Free and open source · Download links open the latest release page";
    });
})();
