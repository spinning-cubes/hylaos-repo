async function main(hyla) {
    const screenHtml = await hyla.fs.getAsText(hyla.app.path + "/screen/index.html");
    hyla.wm.createWindow({
        content: screenHtml
    })
}