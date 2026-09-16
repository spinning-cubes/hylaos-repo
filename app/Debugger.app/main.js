async function main(hyla) {
    let content = "";
    try {
        content = await hyla.fs.getAsText("/app/Debugger.app/screen/index.html");
    } catch (err) {
        content = '<div class="content-area"><p>Debugger: failed to load screen.</p></div>';
    }
    hyla.wm.createWindow({
        title: "Debugger",
        width: 820,
        height: 520,
        content: content
    });
}