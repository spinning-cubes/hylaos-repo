async function main(hyla) {
    let screenHtml = await hyla.fs.getAsText(hyla.app.path + "/screen/index.html");
    hyla.wm.createWindow({
        content: screenHtml
    })
}