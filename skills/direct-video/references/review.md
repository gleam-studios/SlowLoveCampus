# Evidence-based review

Use PASS / REPAIR / UNVERIFIED / NOT APPLICABLE with reasons. An average score cannot cancel a factual or delivery failure.

| Layer | Required evidence | Typical failure |
|---|---|---|
| Purpose/story | Sequence + brief | Attractive shots with no progression |
| Composition/type | Hero + expected viewing size | Competing focal points, clipped/tiny text |
| Motion/edit | Playback or dense event sequence | Speed pops, accidental holds, broken direction |
| Image/continuity | Adjacent shots + difficult intervals | Identity/contact drift, inconsistent exposure |
| Sound | Listening + metering | Masked voice, harshness, clicks, poor rhythm |
| Delivery | Final metadata + decode | Wrong format/duration, missing/corrupt streams |
| Reproducibility | Out-of-order frame comparison | Random drift, hidden state, unloaded assets |

Review narrative/source fidelity before polish. Inspect opening, peak, ending, every cut and difficult action. For t at a cut inspect t−1/fps, t, t+1/fps plus a dense strip. For loops inspect the actual wrap. For multiple formats inspect each layout. Always check the final export after compression/muxing.

Record timestamp, observation, impact, smallest fix and recheck evidence. Fix the most consequential few defects first. Stop once requirements and relevant checks pass; disclose unverified dimensions.

review_video.py checks metadata/decoding and makes labeled frame grids with FFmpeg and Pillow. It needs no drawtext filter. It does not judge aesthetics. Audio checks cover stream presence only, not loudness, sync, intelligibility or rights. Meter separately and listen when supported.

Black, stillness and silence may be intentional; never delete them based only on a detector.

## Creative acceptance before a quality claim

Compare actual rendered keyframes and motion to the selected reference standard at the same viewing scale. Evaluate the mechanism rather than copying surface styling:
- Is there a subject-specific idea and visual language, or could the same piece advertise anything after changing the words?
- Do composition, image/material quality and type work as intentional design when paused?
- Does movement reveal information, express character or connect shots, rather than merely moving objects?
- Does the sequence have a convincing progression and rhythm, with sound appropriate to its intended delivery?
- Are any assets simplified only because the implementation was convenient?

Record the largest remaining gap and repair it. If the gap is conceptual or asset-related, rebuild that part; do not spend another pass tweaking ease curves or adding ornaments. A failing creative layer cannot be overruled by technical PASS results. Do not call a technical study “high quality” or showcase it as an upgrade without independent creative evidence.

User rejection is evidence that the current result failed the intended quality bar. Capture the specific feedback, make a fresh diagnosis, and change the relevant design decisions; do not defend the result with tests, research volume or process descriptions. Future projects should inherit the lesson, not the rejected look.

## Photographic look-development stop condition

Before a long product/photoreal render, compare a delivery-resolution detail and hero frame with a relevant professional reference. A material that merely has the right color, a generic gradient studio, unconvincing construction, or an emissive white band without convincing surrounding response is a reason to stop and revise image-making. Render time is not progress toward taste when these defects remain. Record the reasoned visual comparison; do not substitute an arbitrary similarity number or self-score.
