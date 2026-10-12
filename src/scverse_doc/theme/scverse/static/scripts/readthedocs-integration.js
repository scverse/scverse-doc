/**
 * Fit the Read the Docs addons into the theme.
 */

// Flyout: flyout.css hardcodes things no part/variable can override:
// - `.container { position: fixed }`
// - the version icon’s grey
// - the logo, an <img> of a #fcfcfc SVG (made for dark backgrounds): dim it to the grey RTD uses for its icons
customElements.whenDefined("readthedocs-flyout").then(() => {
    const sheet = new CSSStyleSheet()
    sheet.replaceSync(`
        .container { position: static; max-width: none; max-height: none; }
        header > span svg.icon { color: var(--readthedocs-flyout-color); }
        header > img.logo { filter: brightness(0.5); }
    `)
    for (const { shadowRoot } of document.querySelectorAll(
        "readthedocs-flyout",
    )) {
        shadowRoot.adoptedStyleSheets = [
            ...shadowRoot.adoptedStyleSheets,
            sheet,
        ]
    }
})

// Search: see https://docs.readthedocs.com/platform/stable/addons.html#integrate-with-search-as-you-type
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
