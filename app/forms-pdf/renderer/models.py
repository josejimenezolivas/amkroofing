from pydantic import BaseModel


class RenderRequest(BaseModel):
    """A serialized snapshot of the on-screen document, printed verbatim.

    The forms API validates the same fields before forwarding them here.
    """

    html: str
    css: str = ""
    filename: str = "document"
    #: `@page` margins. Fixed-position layouts print at "0" and paint their own
    #: margins; flowing layouts need real page margins so every page gets them.
    #: Chromium's PDF API only accepts px, in, cm and mm here -- not pt.
    margin_top: str = "0"
    margin_bottom: str = "0"
    margin_side: str = "0"


class RenderJob(RenderRequest):
    #: Where the page's relative URLs (the logo, fonts) resolve: the site the
    #: user was on, so the print fetches the same assets the screen showed.
    base_url: str | None = None
