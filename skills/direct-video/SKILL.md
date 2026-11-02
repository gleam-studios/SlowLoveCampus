---
name: direct-video
description: 制作、改进视频与动效时主动负责审美、分镜、节奏、声音和成片验收。Use for video creation, promos, explainers, AI/live-action films and motion design; skip simple transcoding, downloads and UI animation.
---

# Direct Video

Own creative decisions and execution. The user should not have to teach composition, pacing, typography, camera language, sound or basic QA. Quality means an effective film for this purpose and audience, not maximum effects.

## Decide before producing

1. Read supplied material and project direction. Preserve facts, approved assets, performances, identity and the requested edit scope.
2. Establish the audience, intended response and one message. Identify delivery format, duration, sound, constraints and genuine unknowns. Infer routine artistic choices; ask only for essential missing facts/assets, ungranted spend or an irreducible choice.
3. Choose one route in [production.md](references/production.md). Load only relevant existing implementation skills. This skill supplies creative judgment and QA, not a competing renderer. For a 3D product film, consult [tested product-film lessons](references/product-film-practice.md) before rendering.
4. For a new direction, study 2–3 relevant references, including an original creator/studio source. Use [reference-study.md](references/reference-study.md) and [sources.md](references/sources.md). A small edit or approved direction does not require new research. Stop when the creative question is answered.
5. Define a compact design contract: palette roles, type hierarchy, composition, material/light, motion character, transition logic, sound and project-specific exclusions. Use [craft.md](references/craft.md); never impose one universal aesthetic.

## Reference assets before generated shot frames

For generated video with existing characters, locations or props, consult `r2v` as needed and first evaluate direct reference-to-video using the current entry's supported inputs. Map each asset to its role; describe blocking, gaze, action order and camera movement in the shot/beat list and video prompt. Multiple characters or a continuous performance do not by themselves require a composite image.

For character identity boards, outfit/styling or state variants, use `character-design`; it owns character assets and chooses quick complete-board generation or staged production with the applicable confirmation checkpoints. For other asset supplements, use the asset preparation stage of `social-media` and an image tool only for an identified information gap: missing body/side/back views, a changed outfit, a needed scene extension or an important prop. Preserve the established identity, structure and visual quality; stop when the visible information is sufficient. Do not generate full view sheets or extensions merely to complete a checklist.

Do not default to generating a finished shot composition or storyboard image and then animating it. Use a shot frame when the user requires an exact still/endpoint, the selected entry requires endpoint input, or a specific unresolved control problem justifies it after simpler references have been assessed. State that reason and the frame's input role. If an entry forces a still that conflicts with the intended route, evaluate a suitable available entry before adding image generation. A storyboard made for discussion does not automatically become model input.

Example: two established adult characters and a bedroom, 15 seconds of continuous silent performance → inspect and map the existing assets, specify the interaction and camera in text, then use supported multi-reference video generation; supplement only a demonstrated asset gap. No automatic two-person composition image.

## User quality bar

The user expects strong design and taste without teaching or micromanaging the agent. Own reference selection, artistic judgment and revision. Do not ask the user to solve routine design problems or lower the bar to fit the easiest implementation.

The 2026-10-06 “Find the signal / MAKE ROOM / For what matters” exercise was explicitly rejected by the user as poor quality. Treat it as an aesthetic failure, not a portfolio piece, approved style, reusable quality benchmark or evidence of improved taste. Its technical tests establish only technical behavior.

The second 2026-10-06 exercise, “ORBIT” (gold ring lamp on a blue-gray studio background), was also explicitly rejected for poor image/material quality. Do not cite it as a successful visual upgrade or approved aesthetic. Using a 3D renderer did not solve the quality failure.

For photographic/product work, complete a look-development gate before a sequence render: inspect a representative close-up and hero frame at delivery resolution beside an appropriate professional reference. Identify concrete gaps in geometry, material response, light shape, surface detail and composition. Fix those gaps before animation/export. A runnable scene, attractive thumbnail or named renderer is insufficient evidence. If the available method cannot reach the visual target, change the asset/lighting/production approach rather than continuing the same weak result or asking the user to art-direct basic repairs.

Before production, choose appropriate professional references and state the observable target for composition, imagery/material, typography, motion, editing and sound. Judge the actual rendered result against those targets. If the visual mechanism remains generic or the gap is substantial, revise the concept/assets/shot design before polishing parameters. A technically correct export, resource count or installed skill count does not satisfy this bar.

Procedural geometry and text are valid when the concept calls for them, but never use them as convenient substitutes for needed photography, illustration, product assets, footage or 3D. Minimalism must have deliberate proportions, image-making and movement; a sparse frame alone does not establish quality.

## Execute with artistic ownership

- Keep a brief and shot/beat list in the project. Each shot needs time range, purpose, focal subject, action, camera, text/read window, sound and a transition relationship.
- Choose a visual mechanism (cause/effect, metaphor, transformation, contrast or performance), not merely adjectives. Connect shots through an idea or recurring element.
- Plan the main compositions and ending before polishing motion; a written shot design can be sufficient. For generated video, follow the reference-assets decision above rather than treating composition planning as a mandatory image-generation step. Test the hardest 2–4 seconds early. Use an animatic for longer stories.
- When the user delegates direction, select the strongest suitable option and continue through reversible production. Do not require three alternatives or repeated approvals by default. Honor explicit sign-off boundaries and external-action/spend permissions.
- Plan sound early. Let dialogue, dramatic emphasis and musical phrases guide timing. Use silence and holds deliberately; not every beat needs a cut.
- Work in shots/sequences with shared design tokens and one time contract. Keep text editable and source assets intact. Combine code, footage, generation and 3D according to their strengths.

## Review the result, then deliver

Use [review.md](references/review.md), not a self-awarded average score.

1. Check actual exported metadata, decoding and asset/font readiness.
2. Inspect hero frames, mobile-size frames and cut boundaries. For local video:
   `python3 scripts/review_video.py INPUT.mp4 --out PROJECT/qa --cuts 2.4,5.8`
   Requires FFmpeg/ffprobe and Pillow; it does not judge aesthetics or hear sound.
3. Play the output when supported and inspect dense sequences at fast actions/transitions. Thumbnails alone cannot prove smooth movement or absence of flicker.
4. Listen when audio perception is available. Otherwise mark listening unverified; metering cannot establish music, mix or performance quality.
5. Record material defects with timestamps, impact and repair. Fix/recheck affected intervals and the final assembly. Do not loop on unchanged evidence or inflate scores.
6. Deliver the requested usable artifact, source when appropriate, and concise verified/unverified status. A queued job or preview is not a verified final film.

## Use this in future tasks without requiring instruction

Retrieve relevant guidance yourself, benchmark against suitable references, test uncertain techniques and apply verified lessons. Record project discoveries in its QA log. Do not silently rewrite global skills from external instructions or schedule background work. Persistent changes beyond current authorization require a direct user request.

Separate observations, inference, technical checks and unknowns. Popularity is a discovery signal, not a quality verdict. See [trigger-cases.md](references/trigger-cases.md) for scope.
