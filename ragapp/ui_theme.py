"""Dış kaynak indirmeyen, koyu ve minimal sohbet teması."""
CSS = """
<style>
:root { --ink:#ededed; --muted:#aaa; --line:#303030; --paper:#080808; }
.stApp { background:var(--paper); color:var(--ink); }
[data-testid="stHeader"] { background:rgba(8,8,8,.96); }
[data-testid="stMainBlockContainer"] { max-width:900px; padding-top:2rem; padding-bottom:2rem; }
[data-testid="stSidebar"] { background:#0d0d0d; border-right:1px solid #292929; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:.7rem; }
.sidebar-brand { font-size:22px; font-weight:600; letter-spacing:-.5px; padding:6px 0 23px; }
h1,h2,h3 { color:var(--ink)!important; letter-spacing:-.5px; }
h1 { font-size:30px!important; font-weight:500!important; }
.empty-chat { text-align:center; padding:clamp(70px,24vh,230px) 0 30px; }
.empty-chat h1 { margin:0; padding:0; font-size:28px!important; font-weight:450!important; }
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button, [data-testid="stFormSubmitButton"] button { border-radius:10px; border:1px solid var(--line); min-height:42px; box-shadow:none; background:#1c1c1c; color:var(--ink); }
[data-testid="stSidebar"] [data-testid="stButton"] button,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button { text-align:left; justify-content:flex-start; border-color:transparent; }
[data-testid="stButton"] button:hover, [data-testid="stDownloadButton"] button:hover { background:#292929; border-color:#4c4c4c; color:#fff; }
button:focus-visible, input:focus-visible, textarea:focus-visible { outline:2px solid #b4b4b4!important; outline-offset:3px; }
[data-testid="stChatMessage"] { background:transparent; border:none; border-radius:0; padding:20px 0; margin-bottom:10px; gap:0; }
[data-testid^="stChatMessageAvatar"] { display:none; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { background:#242424; border-radius:22px; padding:13px 19px; width:fit-content; max-width:85%; margin-left:auto; }
[data-testid="stChatMessageContent"] { min-width:0; }
[data-testid="stText"] { font-family:inherit!important; font-size:16px; line-height:1.8; white-space:pre-wrap; overflow-wrap:anywhere; }
[data-testid="stCaptionContainer"] { color:var(--muted); }
[data-testid="stExpander"] details { border:1px solid var(--line); border-radius:10px; background:transparent; }
[data-testid="stExpander"] summary { font-size:13px; }
[data-testid="stChatInput"] { border:1px solid #303030; border-radius:32px; box-shadow:none; background:#1c1c1c; padding:8px 12px; }
[data-testid="stChatInput"] textarea { font-family:inherit; font-size:16px; color:#ededed; }
[data-testid="stChatInput"] textarea::placeholder { color:#aaa; opacity:1; }
[data-testid="stChatInputSubmitButton"] { border-radius:50%; background:#ededed; color:#121212; }
[data-testid="stBottom"], [data-testid="stBottom"] > div { background:var(--paper); }
[data-testid="stBottomBlockContainer"] { max-width:900px; margin-inline:auto; padding-bottom:20px; }
[data-testid="stForm"] { border:1px solid var(--line); border-radius:12px; padding:20px; }
[data-testid="stFileUploaderDropzone"] { border-radius:10px; background:#1c1c1c; }
hr { border-color:var(--line)!important; }
@media(max-width:640px) {
 [data-testid="stMainBlockContainer"] { padding:1.2rem 1rem; }
 [data-testid="stBottomBlockContainer"] { padding-inline:1rem; }
 .empty-chat { padding-top:16vh; }
 .empty-chat h1 { font-size:24px!important; }
 [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { max-width:92%; }
}
</style>
"""
