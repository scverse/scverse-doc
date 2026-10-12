/**
 * See https://docs.readthedocs.com/platform/stable/addons.html#integrate-with-search-as-you-type
 */

document.addEventListener("readthedocs-addons-data-ready", (event) => {
    const { addons } = event.detail.data()
    if (!addons.search?.enabled) {
        return
    }

    /** @type {HTMLDialogElement | null} */
    const theme_dialog = document.querySelector("dialog#pst-search-dialog")
    if (!theme_dialog) {
        return // `disable_search` theme option
    }
    // pydata’s search button and Ctrl/⌘+K both open its dialog via `showModal()`: show RTD’s search instead.
    theme_dialog.showModal = () => {
        const shown = document.querySelector("readthedocs-search")?.show
        document.dispatchEvent(
            new CustomEvent(`readthedocs-search-${shown ? "hide" : "show"}`),
        )
    }
})
