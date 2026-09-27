// https://docs.readthedocs.com/platform/latest/addons.html#event-data-reference

// Version Selector
document.addEventListener("readthedocs-addons-data-ready", (event) => {
    const config = event.detail.data()

    const versionSelector = `
      <div class="version-selector">
        <select onchange="window.location.href=this.value">
          <option value="${config.versions.current.urls.documentation}">
            ${config.versions.current.slug}
          </option>
          ${config.versions.active
              .filter((v) => v.slug !== config.versions.current.slug)
              .map(
                  (version) => `
              <option value="${version.urls.documentation}">
                ${version.slug}
              </option>
            `,
              )
              .join("")}
        </select>
      </div>
    `

    document
        .querySelector("#pst-primary-sidebar")
        .insertAdjacentHTML("beforeend", versionSelector)
})
