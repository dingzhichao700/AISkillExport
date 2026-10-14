# Bailian image-to-video

Verified workflow: official Beijing DashScope, wan2.6-i2v-flash, 3 seconds, 720P,
audio=false, prompt_extend=false, watermark=false, seed=140326. Keep parameters
explicit for comparisons; seeds do not guarantee identical videos. Inspect current
official API docs before introducing another model's parameters:
https://help.aliyun.com/zh/model-studio/legacy-image-to-video-api-reference/

Use a JSON request config (UTF-8; paths relative to this JSON):
```json
{
  "provider": "bailian",
  "region": "beijing",
  "key_env": "QWEN_ANI",
  "model": "wan2.6-i2v-flash",
  "reference": "reference.png",
  "prompt": "Same character, fixed camera and three-quarter front facing down-right. Walk naturally in place with small low steps, alternating legs, subtle opposing arm swings. Keep the same framing, costume and plain background. No turning, motion blur or camera movement.",
  "parameters": {"resolution":"720P","duration":3,"audio":false,"watermark":false,"prompt_extend":false,"seed":140326}
}
```
For idle replace the motion paragraph: feet planted throughout, one restrained breath,
arms relaxed, no stepping/turning/gestures, gently return to initial pose. For back
diagonal keep back/backpack visible and face hidden, heading up-right. Do not tell a
video model every joint coordinate; do name the motion and camera constraints.

These are diagonal-view examples from the validated astronaut case. Replace the view
sentence with the requested camera/projection and facing direction; isometric views
are optional. Keep an approved reference's view when no alternative is requested.

Commands (run directory must be under work/):
```
python scripts/video_api.py validate --config request.json
python scripts/video_api.py submit --config request.json --run-dir work/take-01
python scripts/video_api.py poll --run-dir work/take-01
```
Poll is one GET plus download when ready. Wait about 10 seconds between polls and keep
the user informed. Pending exits 0 with status; failures exit nonzero. No repeated POST.
The state is written BEFORE sending. If submission fails without a task ID, the run
blocks another submit. After explicit user retry, use a NEW run directory to retain
evidence. If a task ID is recovered from the provider console, record it in state.json
and resume poll; never guess it. Poll/download errors preserve that ID.

Regions supported by this adapter: beijing and singapore (legacy official hosts remain
supported as of the recorded workflow). The key must match the region. Do not probe a
key across regions. Other endpoints/providers need an explicit adapter/config review.
The environment variable's name is public config; its value is neither printed nor saved.
Images are encoded as quality-95 JPEG without changing dimensions; preserve original PNG.
State records hashes and task ID, not the Base64 request, key, or signed download URL.
Key authorization is attached only to the official API host, never the media download.
HTTP/transport failures are reported without raw response bodies or traceback secrets.

This repository does not ship credentials, entitlements, or an automatic paid retry loop.
