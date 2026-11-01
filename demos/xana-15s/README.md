# Xana: 15-second visual demo

[`xana-demo-15s.mp4`](xana-demo-15s.mp4) is a 1280×720 narrated walkthrough of Xana's order and return flow. It is an **illustrative demo** made from the current Xana UI style and documented behavior; it is not a recording of a live customer transaction. The $24 quote is an example.

Xana's portrait is shared with the app at `apps/web/public/images/xana-avatar.svg`. To change the clip visuals or copy, edit `demo.html`. To change the narration, edit `narrate.ps1`. On Windows, regenerate the clip with:

```powershell
./narrate.ps1
node ./render.mjs
```

The render uses this repo's Playwright installation and requires `ffmpeg` on `PATH`. Run `node ./render.mjs --preview` to export six still frames for review.
